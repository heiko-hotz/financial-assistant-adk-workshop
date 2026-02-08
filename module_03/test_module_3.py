
# Unit Test for Module 3 (Manager Agent)
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
    query1 = "What is the price of JPM?" 
    print(f"\nUser > {query1}")
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id,
        new_message=types.Content(role="user", parts=[types.Part(text=query1)])
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                print(f"Manager > {part.text}")

    # Test Case 2: RAG Query
    query2 = "Summarize our investment policy." 
    print(f"\nUser > {query2}")
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id,
        new_message=types.Content(role="user", parts=[types.Part(text=query2)])
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                print(f"Manager > {part.text}")

    print("\n✅ Module 3 Test Complete!")

if __name__ == "__main__":
    asyncio.run(run_test())
