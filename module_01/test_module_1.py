
# Unit Test for Module 1 (Financial Agent)
import sys
import os
import asyncio
import uuid
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService

# Ensure we can import the agent
# Ensure we can import the agent
# Add the project root to sys.path so we can import 'module_01'
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

try:
    from module_01.financial_agent_app.agent import root_agent
    print("✅ Successfully imported module_01.financial_agent_app.agent")
except ImportError as e:
    print(f"❌ Failed to import agent: {e}")
    exit(1)

async def run_test():
    print("🤖 Starting Module 1 (Financial) Test Chat...")
    
    runner = Runner(
        agent=root_agent,
        app_name="module_1_test",
        session_service=InMemorySessionService(),
        auto_create_session=True
    )
    
    session_id = str(uuid.uuid4())
    query = "What is the price of JPM?" 
    print(f"User > {query}")

    try:
        async for event in runner.run_async(
            user_id="test_user",
            session_id=session_id,
            new_message=types.Content(role="user", parts=[types.Part(text=query)])
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(f"Agent > {part.text}")
        print("\n✅ Module 1 Test Passed!")
    except Exception as e:
        print(f"\n❌ Module 1 Test Failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_test())
