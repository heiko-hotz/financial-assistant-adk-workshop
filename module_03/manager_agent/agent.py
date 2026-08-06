
import os
import sys
import asyncio
from dotenv import load_dotenv
from typing import Annotated

from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

# 1. Setup Environment & Imports
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
env_path = os.path.join(project_root, ".env.local")
load_dotenv(env_path)

if "GOOGLE_API_KEY" not in os.environ:
    print(f"⚠️ Warning: GOOGLE_API_KEY not found in {env_path}")

# Add project root to path to allow importing sibling modules
if project_root not in sys.path:
    sys.path.append(project_root)

# Import the sub-agents
try:
    from module_01.financial_agent_app.agent import root_agent as financial_agent
    from module_02.rag_agent.agent import root_agent as rag_agent
    print("✅ Sub-agents imported successfully.")
except ImportError as e:
    print(f"❌ Failed to import sub-agents: {e}")
    # We don't exit here to allow inspection, but the tools will fail.

# 2. Define Delegation Tools

async def ask_financial_quant(
    question: Annotated[str, "The financial question to ask (e.g. stock price, ROI)"]
) -> str:
    """Delegates a question to the Financial Quant agent (Module 1)."""
    print(f"   [Manager] Delegating to Financial Agent: '{question}'")
    
    # Spin up a temporary runner for the sub-agent
    runner = Runner(
        agent=financial_agent,
        app_name="financial_sub_task",
        session_service=InMemorySessionService(),
        auto_create_session=True
    )
    
    response_text = ""
    async for event in runner.run_async(
        user_id="manager",
        session_id="session_1", # Re-use session for simple stateles queries
        new_message=types.Content(role="user", parts=[types.Part(text=question)])
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    response_text += part.text
    
    return response_text

async def ask_rag_analyst(
    question: Annotated[str, "The document-based question to ask (policies, strategy)"]
) -> str:
    """Delegates a question to the RAG Analyst agent (Module 2)."""
    print(f"   [Manager] Delegating to RAG Agent: '{question}'")
    
    runner = Runner(
        agent=rag_agent,
        app_name="rag_sub_task",
        session_service=InMemorySessionService(),
        auto_create_session=True
    )
    
    response_text = ""
    async for event in runner.run_async(
        user_id="manager",
        session_id="session_1",
        new_message=types.Content(role="user", parts=[types.Part(text=question)])
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    response_text += part.text
    
    return response_text

# 3. Create the Manager Agent
root_agent = Agent(
    model="gemini-3.5-flash-lite",
    name="manager_agent",
    tools=[
        FunctionTool(ask_financial_quant), 
        FunctionTool(ask_rag_analyst)
    ],
    instruction=(
        "You are a Senior Investment Manager. \n"
        "You have a team of experts:\n"
        "1. Financial Quant: Ask for real-time data like stock prices.\n"
        "2. RAG Analyst: Ask for internal knowledge like policies and strategy.\n\n"
        "Routing Rules:\n"
        "- If the user asks about 'price', 'value', or 'market data', ask the Financial Quant.\n"
        "- If the user asks about 'policy', 'strategy', 'guidelines', or 'outlook', ask the RAG Analyst.\n"
        "- Always synthesize the answer and present it professionally."
    )
)
