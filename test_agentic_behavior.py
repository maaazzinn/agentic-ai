import asyncio
import unittest
from unittest.mock import AsyncMock, patch

from services.agent_booking import execute_agent_booking
from services.analyzer import ProblemAnalysis, is_local_service_request


class RequestRoutingTests(unittest.TestCase):
    def test_general_questions_use_chat_routing(self):
        self.assertFalse(is_local_service_request("What is photosynthesis?"))
        self.assertFalse(is_local_service_request("What does home cleaning usually include?"))

    def test_service_requests_use_service_routing(self):
        self.assertTrue(is_local_service_request("Book house cleaning at 2pm, cheapest"))
        self.assertTrue(is_local_service_request("My kitchen tap is leaking"))
        self.assertTrue(is_local_service_request("Find the best plumber nearby"))


class AgentBookingTests(unittest.TestCase):
    def make_analysis(self, time_preference):
        return ProblemAnalysis(
            problem_summary="Book house cleaning at 2pm",
            category="home_cleaning",
            issue_type="deep_cleaning",
            intent="book",
            time_preference=time_preference,
            booking_priority="cheapest",
        )

    def test_books_cheapest_provider_with_requested_time(self):
        analysis = self.make_analysis("2pm")
        analysis.booking_priority = "cheapest"
        result = execute_agent_booking(analysis)

        self.assertTrue(result["success"])
        self.assertEqual(result["booking_status"], "demo_confirmed")
        self.assertEqual(result["selected_provider"]["name"], "UrbanGlow Home Sanitization")
        self.assertEqual(result["selected_slot"], "Today 02:00 PM")
        self.assertIn("No external provider has been contacted", result["agent_message"])
        self.assertEqual(result["pricing"]["estimated_total"], 3938)

    def test_common_cheapest_typo_maps_to_cheapest_priority(self):
        from services.analyzer import rule_based_fallback

        analysis = rule_based_fallback("Book house cleaning at 2pm, cheaperst option")
        self.assertEqual(analysis.booking_priority, "cheapest")

    def test_does_not_claim_booking_when_requested_time_is_unavailable(self):
        result = execute_agent_booking(self.make_analysis("Today 04:00 PM"))

        self.assertFalse(result["success"])
        self.assertIn("No provider has an available slot", result["message"])
        self.assertTrue(result["available_slots"])


class GeneralAnswerEndpointTests(unittest.TestCase):
    def test_unrelated_question_gets_model_answer(self):
        import main

        class FakeResponse:
            status_code = 200

            @staticmethod
            def json():
                return {"message": {"content": "Photosynthesis turns light into chemical energy."}}

        class FakeClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return None

            async def post(self, url, json):
                self.payload = json
                return FakeResponse()

        client = FakeClient()
        request = main.ProblemInputRequest(
            problem_description="What is photosynthesis?",
            conversation_history=[{"role": "user", "content": "I am studying biology."}],
        )
        with patch("main.httpx.AsyncClient", return_value=client):
            result = asyncio.run(main.analyze_problem(request))

        self.assertEqual(result["mode"], "chat")
        self.assertEqual(result["answer"], "Photosynthesis turns light into chemical energy.")
        self.assertEqual(client.payload["messages"][-2]["content"], "I am studying biology.")
        self.assertEqual(client.payload["messages"][-1]["content"], "What is photosynthesis?")

    def test_booking_request_runs_agent_for_requested_time_and_priority(self):
        import main
        from services.analyzer import rule_based_fallback

        query = "Book house cleaning at 2pm, cheaperst option"
        request = main.ProblemInputRequest(problem_description=query)
        analysis = rule_based_fallback(query)
        with patch("main.analyze_problem_with_qwen", new=AsyncMock(return_value=analysis)):
            result = asyncio.run(main.analyze_problem(request))

        self.assertEqual(result["mode"], "agent")
        self.assertTrue(result["agent_result"]["success"])
        self.assertEqual(result["agent_result"]["priority_applied"], "cheapest")
        self.assertEqual(result["agent_result"]["selected_slot"], "Today 02:00 PM")


if __name__ == "__main__":
    unittest.main()
