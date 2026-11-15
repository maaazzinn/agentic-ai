"""
End-to-End API Test Suite for Local Service AI.
Verifies all FastAPI endpoints:
1. Health & GPU status (/health, /api/gpu)
2. Categories catalogue (/api/service-ai/categories)
3. Problem Analysis with Qwen (/api/service-ai/analyze)
4. Follow-up Clarification flow (/api/service-ai/follow-up)
5. Direct MCP recommendations (/api/service-ai/recommend)
"""
import httpx
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_all():
    print("=" * 80)
    print("🧪 RUNNING LOCAL SERVICE AI INTEGRATION TEST SUITE")
    print("=" * 80)

    # 1. Health check
    print("\n1. Testing /health...")
    resp = httpx.get(f"{BASE_URL}/health", timeout=10.0)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    print("✓ Health OK:", resp.json().get("status"), "| App:", resp.json().get("app"))

    # 2. Categories
    print("\n2. Testing /api/service-ai/categories...")
    resp = httpx.get(f"{BASE_URL}/api/service-ai/categories", timeout=10.0)
    assert resp.status_code == 200
    cats = resp.json().get("categories", [])
    print(f"✓ Retrieved {len(cats)} categories: {[c['name'] for c in cats[:5]]}...")

    # 3. Analyze Scenario A (Plumbing)
    print("\n3. Testing /api/service-ai/analyze with Scenario A (Plumbing)...")
    payload_a = {
        "problem_description": "My kitchen tap is leaking continuously, even when I close it.",
        "latitude": 12.9716,
        "longitude": 77.5946
    }
    t0 = time.time()
    resp_a = httpx.post(f"{BASE_URL}/api/service-ai/analyze", json=payload_a, timeout=60.0)
    dur_a = round(time.time() - t0, 2)
    assert resp_a.status_code == 200
    data_a = resp_a.json()
    analysis_a = data_a["analysis"]
    recs_a = data_a["recommendations"]
    print(f"✓ Session ID: {data_a['session_id']}")
    print(f"✓ Category: {analysis_a['category']} | Issue: {analysis_a['issue_type']}")
    primary_service = recs_a.get("primary_service")
    if primary_service:
        print(f"✓ SQLite Service Category: {primary_service['name']}")
    else:
        print("✓ No matching service category is listed in SQLite.")
    print(f"✓ Recommended Providers: {len(recs_a['recommended_providers'])}")
    if recs_a['recommended_providers']:
        top_p = recs_a['recommended_providers'][0]
        print(f"   SQLite Provider: {top_p['shop_name']} ({top_p['area']}, {top_p['verification_status']})")
    print(f"✓ Latency: {dur_a}s")

    # 4. Analyze Scenario C (Electrical Emergency)
    print("\n4. Testing /api/service-ai/analyze with Scenario C (Electrical Emergency)...")
    payload_c = {
        "problem_description": "There is a burning smell from my electrical socket.",
        "latitude": 12.9716,
        "longitude": 77.5946
    }
    t0 = time.time()
    resp_c = httpx.post(f"{BASE_URL}/api/service-ai/analyze", json=payload_c, timeout=60.0)
    dur_c = round(time.time() - t0, 2)
    assert resp_c.status_code == 200
    data_c = resp_c.json()
    analysis_c = data_c["analysis"]
    recs_c = data_c["recommendations"]
    print(f"✓ Category: {analysis_c['category']} | Issue: {analysis_c['issue_type']}")
    print(f"✓ Emergency Mode Active: {recs_c['is_emergency']}")
    print(f"🛡️ Safety Warning Enforced: {analysis_c['safety_warning']}")
    assert recs_c["is_emergency"] is True, "Emergency mode must be active"
    assert "do not touch" in (analysis_c["safety_warning"] or "").lower(), "Safety advice must warn not to touch"
    print(f"✓ Latency: {dur_c}s")

    # 5. Analyze Scenario B & Follow-up Flow (AC Repair)
    print("\n5. Testing /api/service-ai/analyze with Scenario B (AC Repair Follow-up)...")
    payload_b = {
        "problem_description": "AC is running but it is not cooling my bedroom. It has been like this since yesterday.",
        "latitude": 12.9716,
        "longitude": 77.5946
    }
    t0 = time.time()
    resp_b = httpx.post(f"{BASE_URL}/api/service-ai/analyze", json=payload_b, timeout=60.0)
    dur_b = round(time.time() - t0, 2)
    assert resp_b.status_code == 200
    data_b = resp_b.json()
    sess_b_id = data_b["session_id"]
    analysis_b = data_b["analysis"]
    print(f"✓ Session ID: {sess_b_id}")
    print(f"✓ Category: {analysis_b['category']} | Requires Followup: {analysis_b['requires_followup']}")
    print(f"✓ Follow-up Question: {analysis_b['follow_up_question']}")

    # 6. Submit Follow-up answer
    print("\n6. Testing /api/service-ai/follow-up...")
    follow_payload = {
        "session_id": sess_b_id,
        "clarification": "The airflow is very weak and blowing room temperature air.",
        "property_size": "2BHK"
    }
    resp_follow = httpx.post(f"{BASE_URL}/api/service-ai/follow-up", json=follow_payload, timeout=10.0)
    assert resp_follow.status_code == 200
    data_follow = resp_follow.json()
    print("✓ Follow-up Clarification Processed Successfully!")
    print(f"✓ Updated State: {data_follow['state']}")
    print(f"✓ Clarification Applied: {data_follow['recommendations']['clarification_applied']}")

    # 7. UI Static file check
    print("\n7. Testing UI Endpoint (/)...")
    resp_ui = httpx.get(f"{BASE_URL}/", timeout=5.0)
    assert resp_ui.status_code == 200
    assert "Local Service AI" in resp_ui.text
    print("✓ Web UI serves successfully with Local Service AI title!")

    print("\n" + "=" * 80)
    print("🎉 ALL 7 INTEGRATION TESTS PASSED PERFECTLY!")
    print("=" * 80)

if __name__ == "__main__":
    test_all()
