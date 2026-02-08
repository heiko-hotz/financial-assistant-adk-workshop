
import os
import asyncio
from dotenv import load_dotenv
from google.adk.agents import Agent, LoopAgent
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

load_dotenv(".env.local")

# Define 1: Worker Agent
worker = Agent(
    model="gemini-2.5-flash",
    name="worker",
    instruction="You are a worker. Just say 'I worked' when asked."
)

# Define 2: Critic Agent
# The Critic needs to stop the loop eventually.
critic = Agent(
    model="gemini-2.5-flash",
    name="critic",
    instruction="You are a critic. If the worker says 'I worked', you MUST try to stop the loop. Check if you have an 'escalate' tool or similar. If not, just say 'STOP'."
)

# Callback to inspect stop condition
def stop_check(**kwargs):
    print(f"[Callback Debug] Keys: {list(kwargs.keys())}")
    
    # Try to extract event from kwargs
    # Based on previous errors, 'callback_context' is definitely there.
    # Let's inspect it.
    ctx = kwargs.get('callback_context')
    if ctx:
        # ctx likely has .agent and .event attributes or similar
        print(f"[Callback Debug] Context dir: {dir(ctx)}")

    return None

# Define 3: Loop Agent
loop_agent = LoopAgent(
    sub_agents=[worker, critic],
    name="loop_team",
    max_iterations=5,
    after_agent_callback=stop_check
)

async def test_loop():
    print("--- Starting Loop Test ---")
    runner = Runner(
        agent=loop_agent,
        app_name="loop_test",
        session_service=InMemorySessionService(),
        auto_create_session=True
    )

    async for event in runner.run_async(
        user_id="tester",
        session_id="loop_session",
        new_message=types.Content(role="user", parts=[types.Part(text="Start working")])
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                print(f"[Event] {part.text}")
        else:
            print(f"[Event Metadata] {event}")

if __name__ == "__main__":
    asyncio.run(test_loop())
