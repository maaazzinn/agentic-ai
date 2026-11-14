"""
AI Problem Analyzer — Local Service AI
Qwen 3.5 2B via Ollama. Full agentic support:
- intent: discover | book | urgent
- Dynamic suggested_replies from the model itself (no hardcoded chips)
- time_preference, booking_priority extraction for agent execution
"""
import json
import re
import logging
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import httpx

logger = logging.getLogger("service_ai.analyzer")

SUPPORTED_CATEGORIES = [
    "plumbing", "electrical", "ac_repair", "appliance_repair",
    "home_cleaning", "car_wash", "painting", "carpentry", "pest_control", "other",
]

SYSTEM_PROMPT = """# Role: Local Service AI Agent

You are an intelligent agent for a local service-booking platform (like Urban Company). You help customers both discover services AND directly book them through natural-language commands.

## Supported service categories
plumbing | electrical | ac_repair | appliance_repair | home_cleaning | car_wash | painting | carpentry | pest_control | other

## Your responsibilities
1. Detect the customer's INTENT: are they reporting a problem (discover), or requesting an action like booking (book), or is it urgent/emergency (urgent)?
2. Extract the service category, issue type, and any booking preferences (time, budget priority).
3. If information is missing, ask a focused follow-up question AND suggest 2–3 short reply options the customer can tap.
4. For electrical hazards (burning smell, sparks, scorch marks), always warn and never suggest DIY.
5. Never invent provider names, prices, or availability — the booking engine handles that.

## Intent detection examples
- "My tap is leaking" → intent: discover
- "Book house cleaning for 2pm" → intent: book
- "Get me the cheapest plumber" → intent: book
- "There is a burning smell from the socket" → intent: urgent
- "Schedule deep cleaning this Saturday morning cheapest option" → intent: book

## Booking priority detection
- "cheapest" / "cheaper" / "affordable" / "budget" / "lowest price" → booking_priority: cheapest
- "fastest" / "quickly" / "urgent" / "ASAP" / "now" → booking_priority: fastest
- "best" / "top rated" / "highest rated" → booking_priority: top_rated
- (default if not stated) → booking_priority: top_rated

## Output — return valid JSON only, this exact structure, no markdown, no commentary:
{
  "problem_summary": "Short plain-English description",
  "category": "home_cleaning",
  "issue_type": "deep_cleaning",
  "confidence": 0.95,
  "intent": "book",
  "time_preference": "2pm",
  "booking_priority": "cheapest",
  "observations": [],
  "missing_information": [],
  "requires_followup": false,
  "follow_up_question": null,
  "suggested_replies": [],
  "safety_warning": null
}

Rules:
- confidence: 0.0–1.0
- intent must be: discover, book, or urgent
- booking_priority must be: cheapest, fastest, or top_rated
- time_preference: extract any stated time (e.g. "2pm", "this Saturday", "tomorrow morning") or null
- suggested_replies: 2–3 short tap-friendly answer options ONLY when requires_followup is true, else empty []
- If ambiguous, set requires_followup true and ask ONE focused question with suggested_replies
- Return JSON only."""


class ProblemAnalysis(BaseModel):
    problem_summary: str
    category: str
    issue_type: str
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    intent: str = Field(default="discover")          # discover | book | urgent
    time_preference: Optional[str] = None
    booking_priority: str = Field(default="top_rated")  # cheapest | fastest | top_rated
    observations: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    requires_followup: bool = False
    follow_up_question: Optional[str] = None
    suggested_replies: List[str] = Field(default_factory=list)   # AI-generated chips
    safety_warning: Optional[str] = None
    raw_thinking: Optional[str] = None


def normalize_category(cat: str) -> str:
    if not cat:
        return "other"
    c = cat.lower().strip().replace(" ", "_").replace("-", "_")
    mapping = {
        "plumbing": "plumbing", "plumber": "plumbing",
        "electrical": "electrical", "electrician": "electrical",
        "ac": "ac_repair", "ac_repair": "ac_repair",
        "air_conditioning": "ac_repair", "air_conditioner": "ac_repair",
        "appliance": "appliance_repair", "appliance_repair": "appliance_repair",
        "cleaning": "home_cleaning", "home_cleaning": "home_cleaning",
        "house_cleaning": "home_cleaning",
        "car_wash": "car_wash", "car_cleaning": "car_wash",
        "painting": "painting", "carpentry": "carpentry",
        "pest_control": "pest_control",
    }
    return mapping.get(c, c if c in SUPPORTED_CATEGORIES else "other")


def normalize_intent(intent: str) -> str:
    i = (intent or "").lower().strip()
    if i in ("book", "booking", "schedule", "order"):
        return "book"
    if i in ("urgent", "emergency", "asap"):
        return "urgent"
    return "discover"


def normalize_priority(priority: str) -> str:
    p = (priority or "").lower().strip()
    if p in ("cheapest", "cheaper", "cheaperst", "cheap", "budget", "affordable", "lowest", "lowest price", "low cost"):
        return "cheapest"
    if p in ("fastest", "fast", "quick", "urgent", "asap", "immediately"):
        return "fastest"
    return "top_rated"


def is_local_service_request(user_input: str, has_image: bool = False) -> bool:
    """Route clear service needs to the booking workflow and other questions to chat."""
    if has_image:
        return True

    text = (user_input or "").lower()
    has_service = re.search(
        r"\b(plumb(?:er|ing)?|tap|faucet|pipe|drain|electrician|electrical|"
        r"socket|switch|ac|air conditioner|washing machine|refrigerator|fridge|"
        r"appliance|clean(?:er|ing)?|maid|car wash|painting|painter|carpenter|"
        r"pest control|termite|cockroach)\b",
        text,
    )
    if not has_service:
        return False

    service_action = re.search(
        r"\b(book|schedule|hire|arrange|find|get|need|want|looking for|"
        r"repair|fix|clean|wash|install|replace|service|cheapest|cheaper|"
        r"cheaperst|affordable|lowest price|low cost|"
        r"fastest|best|top rated|top-rated|available|provider|nearby|near me)\b",
        text,
    )
    reported_issue = re.search(
        r"\b(my|our|isn't|is not|not working|broken|leaking|leak|"
        r"not cooling|making noise|sparking|burning smell|blocked)\b",
        text,
    )
    return bool(service_action or reported_issue)


def extract_json_from_text(text: str) -> Dict[str, Any]:
    if not text:
        raise ValueError("Empty text")
    cleaned = text.strip()

    if "</think>" in cleaned:
        after = cleaned.split("</think>")[-1].strip()
        try:
            return json.loads(after)
        except Exception:
            cleaned = after

    blocks = re.findall(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned)
    for b in reversed(blocks):
        try:
            return json.loads(b.strip())
        except Exception:
            pass

    try:
        return json.loads(cleaned)
    except Exception:
        pass

    last_brace = cleaned.rfind("}")
    if last_brace != -1:
        idx = cleaned.rfind("{", 0, last_brace)
        while idx != -1:
            try:
                return json.loads(cleaned[idx: last_brace + 1])
            except Exception:
                idx = cleaned.rfind("{", 0, idx)

    raise ValueError(f"No valid JSON found: {cleaned[:200]}")


def enforce_safety_rules(analysis: ProblemAnalysis, user_input: str) -> ProblemAnalysis:
    text = (user_input + " " + analysis.problem_summary + " " + analysis.issue_type).lower()
    hazard_kw = ["burning smell", "burnt", "spark", "sparking", "electric shock",
                 "fire", "scorch", "smoke", "smoking", "short circuit"]
    if any(k in text for k in hazard_kw):
        analysis.category = "electrical"
        analysis.intent = "urgent"
        analysis.issue_type = (
            "socket_hazard" if "socket" in text else
            "switch_hazard" if "switch" in text else
            "electrical_hazard"
        )
        analysis.safety_warning = (
            "⚠️ DANGER — ELECTRICAL HAZARD: "
            "1. Do NOT touch or use the affected socket/switch. "
            "2. Switch off the main circuit breaker (MCB) if safe to reach. "
            "3. Do NOT attempt any DIY repair. "
            "4. A licensed emergency electrician is urgently required."
        )
        analysis.observations.append("Potential fire / short-circuit hazard detected.")
    return analysis


async def analyze_problem_with_qwen(
    user_input: str,
    image_base64: Optional[str] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
    ollama_base_url: str = "http://127.0.0.1:11434",
    model_name: str = "qwen3.5:2b",
    timeout: float = 60.0,
) -> ProblemAnalysis:

    user_content = user_input.strip() or "Customer uploaded a problem image."
    msg: Dict[str, Any] = {"role": "user", "content": user_content}
    if image_base64:
        b64 = image_base64.split("base64,")[-1] if "base64," in image_base64 else image_base64
        msg["images"] = [b64]

    messages: List[Dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    # Include prior conversation turns so the model has context for follow-up answers
    if conversation_history:
        messages.extend(conversation_history)
    messages.append(msg)

    payload = {
        "model": model_name,
        "messages": messages,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.2},
    }

    raw_thinking = None
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(f"{ollama_base_url}/api/chat", json=payload)
            if resp.status_code != 200:
                raise RuntimeError(f"Ollama {resp.status_code}: {resp.text}")
            data = resp.json()
            msg_obj = data.get("message", {})
            content = msg_obj.get("content", "")
            raw_thinking = msg_obj.get("thinking")

            try:
                parsed = extract_json_from_text(content)
            except Exception:
                if raw_thinking:
                    parsed = extract_json_from_text(raw_thinking)
                else:
                    raise

            analysis = ProblemAnalysis(
                problem_summary=parsed.get("problem_summary", user_input[:80]),
                category=normalize_category(parsed.get("category", "other")),
                issue_type=parsed.get("issue_type", "general_inquiry"),
                confidence=float(parsed.get("confidence", 0.85)),
                intent=normalize_intent(parsed.get("intent", "discover")),
                time_preference=parsed.get("time_preference"),
                booking_priority=normalize_priority(parsed.get("booking_priority", "top_rated")),
                observations=parsed.get("observations", []) if isinstance(parsed.get("observations"), list) else [],
                missing_information=parsed.get("missing_information", []) if isinstance(parsed.get("missing_information"), list) else [],
                requires_followup=bool(parsed.get("requires_followup", False)),
                follow_up_question=parsed.get("follow_up_question"),
                suggested_replies=parsed.get("suggested_replies", []) if isinstance(parsed.get("suggested_replies"), list) else [],
                safety_warning=parsed.get("safety_warning"),
                raw_thinking=raw_thinking,
            )
            return enforce_safety_rules(analysis, user_input)

    except Exception as exc:
        logger.warning(f"Qwen fallback: {exc}")
        fallback = rule_based_fallback(user_input)
        fallback.raw_thinking = f"Fallback: {exc}"
        return fallback


def rule_based_fallback(user_input: str) -> ProblemAnalysis:
    text = user_input.lower()

    # Detect booking intent
    intent = "discover"
    if any(k in text for k in [
        "book", "schedule", "order", "get me", "find me", "arrange",
        "need a", "need someone", "want a", "want someone", "hire",
        "looking for", "available",
    ]):
        intent = "book"

    # Detect priority
    priority = "top_rated"
    if any(k in text for k in [
        "cheapest", "cheaperst", "cheaper", "cheap", "budget", "affordable",
        "lowest price", "low cost", "least expensive",
    ]):
        priority = "cheapest"
    elif any(k in text for k in ["fastest", "quick", "urgent", "asap"]):
        priority = "fastest"

    # Detect time
    time_pref = None
    time_matches = re.findall(r'\d{1,2}(?::\d{2})?\s*(?:am|pm)|(?:today|tomorrow|saturday|sunday|morning|afternoon|evening)', text)
    if time_matches:
        time_pref = time_matches[0]

    if any(k in text for k in ["tap", "faucet", "leak", "pipe", "drain", "plumb"]):
        return ProblemAnalysis(problem_summary=user_input, category="plumbing",
            issue_type="tap_repair", confidence=0.88, intent=intent, time_preference=time_pref,
            booking_priority=priority, observations=["Water leakage reported"])

    if any(k in text for k in ["ac", "air conditioner", "cooling", "cool"]):
        return ProblemAnalysis(problem_summary=user_input, category="ac_repair",
            issue_type="cooling_problem", confidence=0.85, intent=intent, time_preference=time_pref,
            booking_priority=priority, requires_followup=True,
            follow_up_question="Is the AC blowing air normally, or is the airflow very weak?",
            suggested_replies=["Airflow is very weak", "Air is room temperature", "Fan not running"])

    if any(k in text for k in ["burn", "burning", "socket", "switch", "spark", "electric"]):
        a = ProblemAnalysis(problem_summary=user_input, category="electrical",
            issue_type="socket_hazard", confidence=0.95, intent="urgent", time_preference=time_pref,
            booking_priority="fastest")
        return enforce_safety_rules(a, user_input)

    if any(k in text for k in ["washing machine", "washer", "spinning", "drum"]):
        return ProblemAnalysis(problem_summary=user_input, category="appliance_repair",
            issue_type="washing_machine_noise", confidence=0.90, intent=intent, time_preference=time_pref,
            booking_priority=priority, requires_followup=True,
            follow_up_question="Is the noise more of a banging vibration or a grinding sound from the drum?",
            suggested_replies=["Heavy banging vibration", "Grinding inside drum", "Loud rattling"])

    if any(k in text for k in ["clean", "cleaning", "deep clean", "2bhk", "1bhk", "apartment", "house"]):
        needs_fu = not time_pref
        return ProblemAnalysis(problem_summary=user_input, category="home_cleaning",
            issue_type="deep_cleaning", confidence=0.92, intent=intent, time_preference=time_pref,
            booking_priority=priority,
            requires_followup=needs_fu,
            follow_up_question="When would you like the cleaning done?" if needs_fu else None,
            suggested_replies=["Today afternoon", "Tomorrow morning", "This Saturday"] if needs_fu else [])

    if any(k in text for k in ["car", "vehicle", "wash"]):
        return ProblemAnalysis(problem_summary=user_input, category="car_wash",
            issue_type="car_wash", confidence=0.90, intent=intent, time_preference=time_pref,
            booking_priority=priority)

    # Ambiguous
    return ProblemAnalysis(problem_summary=user_input, category="other",
        issue_type="unclear_request", confidence=0.40, intent="discover",
        requires_followup=True,
        follow_up_question="Could you tell me which appliance or area needs attention and what the problem is?",
        suggested_replies=["Plumbing issue", "Electrical problem", "Need cleaning", "Appliance repair"])
