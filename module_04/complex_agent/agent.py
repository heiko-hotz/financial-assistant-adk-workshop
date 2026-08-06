
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
    model="gemini-3.5-flash-lite",
    name="goal_refiner",
    instruction=(
        "You are the Research Coordinator for Lumenridge Financial Group. "
        "Turn the user's request into a research plan; do not answer it yourself. "
        "Tell the analyst to use only facts retrieved from the supplied workshop documents and "
        "never supplement them with general knowledge. For a strategy memo, require evidence on "
        "the AI-infrastructure thesis, its valuation and growth thresholds, the Clean Future ESG "
        "rules, and the portfolio risk controls. Request relevant internal technology controls when "
        "the question calls for them. If a requested fact is absent, tell the analyst to say so. "
        "Do not introduce unverified companies, figures, regulations, or technologies into the plan."
    )
)

# B. Compliance/Evaluator (Loop Participant)
compliance_officer = Agent(
    model="gemini-3.5-flash-lite",
    name="compliance_officer",
    instruction=(
        "You are the Senior Compliance Officer for Lumenridge Financial Group. "
        "Treat retrieved workshop-document content as the only valid evidence. Review every material "
        "claim in the analyst's findings and reject claims that are not supported by that evidence. "
        "Never accept or add outside facts, regulations, technologies, companies, or figures; examples "
        "such as GDPR, Basel III, the EU AI Act, Kubernetes, and PII controls are unsupported unless "
        "they were actually retrieved. For a strategy memo, require the Lumenridge name and supported "
        "facts covering the AI-infrastructure thesis, valuation and growth thresholds, Clean Future "
        "ESG rules, and portfolio risk controls. Also require any technology facts requested by the "
        "user. If evidence is missing or a claim is unsupported, give specific feedback directing the "
        "analyst to retrieve evidence, remove the claim, or state that the documents do not say. "
        "Only when the findings are complete, professional, and fully grounded should your response "
        "start with 'READY_FOR_SUMMARY'."
    ),
    output_key="compliance_report"
)

# C. Termination Checker (Loop Participant)
class TerminationChecker(BaseAgent):
    async def _run_async_impl(self, ctx):
        # Check the output from the compliance officer
        report = ctx.session.state.get("compliance_report", "")
        if report.lstrip().startswith("READY_FOR_SUMMARY"):
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
    model="gemini-3.5-flash-lite",
    name="reporter",
    instruction=(
        "You are the Senior Investment Reporter for Lumenridge Financial Group. "
        "Write a concise Markdown executive memo using only claims from the analyst's retrieved "
        "workshop-document evidence that the compliance review accepted. Compliance feedback and "
        "earlier agent prose are not evidence. Brand the memo only as Lumenridge Financial Group. "
        "Include supported findings on the AI-infrastructure thesis, valuation and growth thresholds, "
        "Clean Future ESG rules, and portfolio risk controls, plus relevant internal technology facts "
        "requested by the user. Never add outside facts, regulations, technologies, companies, or "
        "figures; in particular, omit GDPR, Basel III, the EU AI Act, Kubernetes, and PII controls "
        "unless the retrieved documents explicitly contain them. Do not fill gaps with plausible "
        "details. Instead, omit the claim or state that it is not specified in the workshop documents. "
        "If compliance did not emit READY_FOR_SUMMARY, return a short notice that the memo was not "
        "approved instead of presenting unverified findings. "
        "Use clear headings and make any recommendation a direct synthesis of the sourced policy, not "
        "new financial advice."
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
