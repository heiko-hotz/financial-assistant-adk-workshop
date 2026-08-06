
# Live integration smoke test for Module 3 (Manager Agent)
import sys
import os
import asyncio
import uuid
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService

# Ensure we can import the agent
# Add the project root to sys.path so we can import 'module_03'
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from module_03.manager_agent.agent import root_agent
    print("✅ Successfully imported module_03.manager_agent.agent")
except ImportError as e:
    print(f"❌ Failed to import Manager Agent: {e}")
    exit(1)

async def run_test():
    print("🤖 Starting Module 3 (Manager) Test Chat...")
    
    runner = Runner(
        agent=root_agent, 
        app_name="module_3_test",
        session_service=InMemorySessionService(),
        auto_create_session=True
    )
    
    session_id = str(uuid.uuid4())
    user_id = "manager_tester"

    # Test Case 1: Financial Query
    query1 = "What is the price of LUMR?"
    print(f"\nUser > {query1}")
    responses = []
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id,
        new_message=types.Content(role="user", parts=[types.Part(text=query1)])
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text and part.text.strip():
                    text = part.text.strip()
                    responses.append(text)
                    print(f"Manager > {text}")

    if not responses:
        raise RuntimeError("The manager returned no text for the financial query.")
    financial_response = "\n".join(responses).lower()
    if "lumr" not in financial_response or "245.50" not in financial_response:
        raise RuntimeError("The manager did not return the expected LUMR price.")

    # Test Case 2: RAG Query
    query2 = "Summarize our investment policy." 
    print(f"\nUser > {query2}")
    responses = []
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id,
        new_message=types.Content(role="user", parts=[types.Part(text=query2)])
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text and part.text.strip():
                    text = part.text.strip()
                    responses.append(text)
                    print(f"Manager > {text}")

    if not responses:
        raise RuntimeError("The manager returned no text for the policy query.")
    policy_response = "\n".join(responses).lower()
    expected_facts = ("p/e", "15%", "clean future", "12%")
    missing_facts = [fact for fact in expected_facts if fact not in policy_response]
    if missing_facts:
        raise RuntimeError(
            "The manager's policy response omitted expected facts: "
            + ", ".join(missing_facts)
        )

    print("\n✅ Module 3 Test Passed!")

if __name__ == "__main__":
    asyncio.run(run_test())
