
# Live integration smoke test for Module 4 (Complex Workflows)
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
    outputs_by_author = {}
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id,
        new_message=types.Content(role="user", parts=[types.Part(text=query)])
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    text = part.text.strip()
                    if text:
                        outputs_by_author.setdefault(event.author, []).append(text)
                        print(f"\n[{event.author}]\n{text}")

    required_authors = {
        "goal_refiner",
        "rag_agent",
        "compliance_officer",
        "reporter",
    }
    missing_authors = required_authors - outputs_by_author.keys()
    if missing_authors:
        missing = ", ".join(sorted(missing_authors))
        raise RuntimeError(f"Missing text output from required agents: {missing}")

    compliance_outputs = outputs_by_author["compliance_officer"]
    if not any(text.lstrip().startswith("READY_FOR_SUMMARY") for text in compliance_outputs):
        raise RuntimeError("Compliance never approved the evidence for summary.")

    memo = "\n".join(outputs_by_author["reporter"])
    memo_lower = memo.lower()
    expected_facts = ("lumenridge", "p/e", "15%", "clean future", "12%", "5%", "-15%")
    missing_facts = [fact for fact in expected_facts if fact not in memo_lower]
    if missing_facts:
        raise RuntimeError(
            "The final memo omitted expected grounded facts: "
            + ", ".join(missing_facts)
        )

    forbidden_claims = ("gdpr", "basel", "eu ai act", "kubernetes", "pii")
    unsupported_claims = [claim for claim in forbidden_claims if claim in memo_lower]
    if unsupported_claims:
        raise RuntimeError(
            "The final memo contained unsupported claims: "
            + ", ".join(unsupported_claims)
        )

    print("\n✅ Module 4 Test Passed!")

if __name__ == "__main__":
    asyncio.run(run_test())
