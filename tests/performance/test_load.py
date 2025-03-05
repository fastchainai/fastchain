"""Load testing using Locust for FastChain AI."""
from locust import HttpUser, task, between
import json

class APILoadTest(HttpUser):
    wait_time = between(1, 2)  # Wait 1-2 seconds between tasks
    
    def on_start(self):
        """Initialize test data."""
        self.headers = {"Content-Type": "application/json"}
        self.test_message = {
            "message": "Test message for load testing",
            "context": {"test": True}
        }

    @task(2)
    def test_chat_endpoint(self):
        """Test the chat endpoint under load."""
        self.client.post("/api/v1/chat/", 
                        json=self.test_message,
                        headers=self.headers)

    @task(1)
    def test_intent_classification(self):
        """Test the intent classification endpoint under load."""
        intent_data = {
            "text": "What is the weather like today?",
            "context": {"domain": "weather"}
        }
        self.client.post("/api/v1/intent/classify",
                        json=intent_data,
                        headers=self.headers)

    @task(1)
    def test_system_status(self):
        """Test the system status endpoint under load."""
        self.client.get("/api/v1/system/status")

    @task(1)
    def test_agent_registry(self):
        """Test the agent registry endpoint under load."""
        self.client.get("/api/v1/agents/registry/")

"""
To run this test:
1. Start the FastAPI server
2. Run: locust -f tests/performance/test_load.py --host=http://localhost:5000
3. Access Locust web interface at http://localhost:8089
"""
