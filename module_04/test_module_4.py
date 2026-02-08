
# Unit Test for Module 4 (Complex Workflows)
import sys
import os
import asyncio
import uuid
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService

# 1. Dynamic Path Setup
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

# 2. Import the Complex Agent
try:
    from module_04.complex_agent.agent import root_agent as research_team
    print("✅ Successfully imported module_04.complex_agent.agent")
except ImportError as e:
    print(f"❌ Failed to import Complex Agent: {e}")
    exit(1)

async def run_test():
    print("🤖 Starting Module 4 (Complex Workflow) Test...")
    
    runner = Runner(
        agent=research_team, 
        app_name="module_4_test",
        session_service=InMemorySessionService(),
        auto_create_session=True
    )
    
    session_id = str(uuid.uuid4())
    user_id = "complex_tester"

    query = "What is the tech growth strategy for AI infrastructure?"
    print(f"\nUser > {query}\n")

    print("--- Workflow Trace ---")
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id,
        new_message=types.Content(role="user", parts=[types.Part(text=query)])
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    # Clean up long outputs for trace
                    text = part.text.strip()
                    source = event.agent_name if hasattr(event, 'agent_name') else "System"
                    print(f"[{source}] {text[:100]}...")

    print("\n✅ Module 4 Test Complete!")

if __name__ == "__main__":
    asyncio.run(run_test())
