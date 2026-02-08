
import os
import sys
from dotenv import load_dotenv

from google.adk.agents import Agent, SequentialAgent, LoopAgent, BaseAgent
from google.adk.events import Event, EventActions
from google.genai import types

# 1. Setup Environment
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
env_path = os.path.join(project_root, ".env.local")
load_dotenv(env_path)

# Add project root to path
if project_root not in sys.path:
    sys.path.append(project_root)

# 2. Import Base Agents (Specialists)
try:
    from module_02.rag_agent.agent import root_agent as rag_analyst
    print("✅ RAG Analyst imported.")
except ImportError as e:
    print(f"❌ Failed to import RAG Agent: {e}")
    exit(1)

# 3. Define the Research Team Components

# A. Goal Refiner (Sequential Step 1)
goal_refiner = Agent(
    model="gemini-2.5-flash",
    name="goal_refiner",
    instruction=(
        "You are a Research Coordinator. "
        "Your job is to take a raw user query and turn it into a clear, detailed research prompt "
        "for an analyst. Focus on technical details and specific banking context."
    )
)

# B. Compliance/Evaluator (Loop Participant)
compliance_officer = Agent(
    model="gemini-2.5-flash",
    name="compliance_officer",
    instruction=(
        "You are a Senior Compliance Officer. "
        "Review the analyst's findings. If the report is incomplete or lacks professional tone, "
        "provide specific feedback. "
        "If the report is perfect and ready, start your response with 'READY_FOR_SUMMARY'."
    ),
    output_key="compliance_report"
)

# C. Termination Checker (Loop Participant)
class TerminationChecker(BaseAgent):
    async def _run_async_impl(self, ctx):
        # Check the output from the compliance officer
        report = ctx.session.state.get("compliance_report", "")
        if "READY_FOR_SUMMARY" in report:
            # Signal the loop to stop
            yield Event(
                author=self.name,
                actions=EventActions(escalate=True)
            )
        else:
            # Continue the loop
            yield Event(author=self.name)

termination_checker = TerminationChecker(name="termination_checker")

# D. Research Loop (Sequential Step 2)
research_loop = LoopAgent(
    name="research_loop",
    sub_agents=[rag_analyst, compliance_officer, termination_checker],
    max_iterations=4
)

# E. Reporter (Sequential Step 3)
reporter = Agent(
    model="gemini-2.5-flash",
    name="reporter",
    instruction=(
        "You are a Senior Investment Reporter. "
        "Take the raw analyst data and compliance feedback, and compile it into a "
        "beautifully formatted JPMorgan Executive Memo. Use markdown headers."
    )
)

# 4. Define the Final Sequential Research Team
research_team = SequentialAgent(
    name="research_team",
    sub_agents=[goal_refiner, research_loop, reporter],
    description="An autonomous research team that refines goals, fetch data, reviews it, and reports."
)

# Alias for external use
root_agent = research_team
