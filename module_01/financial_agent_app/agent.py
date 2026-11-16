"""The Module 1 portfolio assistant and its ADK tool wiring."""

from collections.abc import Callable, Sequence
from pathlib import Path

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.skills.models import Skill
from google.adk.tools import FunctionTool
from google.adk.tools.skill_toolset import SkillToolset

from .portfolio import calculate_shock, get_holdings, get_position_values, get_stock_price
from .skills import PORTFOLIO_STRESS_TEST, SKILL_AUTHOR, stage_skill_draft


load_dotenv(Path(__file__).resolve().parents[2] / ".env.local")
MODEL = "gemini-3.5-flash-lite"
RESERVED_TOOL_NAMES = {
    "get_stock_price", "get_holdings", "get_position_values", "calculate_shock", "stage_skill_draft",
    "list_skills", "load_skill", "load_skill_resource", "run_skill_script",
    "search_skills", "unload_skill",
}


def validate_extra_tool_names(names: Sequence[str]) -> None:
    taken = RESERVED_TOOL_NAMES.copy()
    for name in names:
        if not name or name in taken:
            raise ValueError(f"Choose a unique name for the reviewed tool. Unavailable name: {name!r}.")
        taken.add(name)


def build_agent(
    *,
    extra_skills: Sequence[Skill] = (),
    extra_tools: Sequence[Callable[..., dict]] = (),
) -> Agent:
    """Add a reviewed skill and its Python functions to a fresh agent."""
    validate_extra_tool_names([getattr(tool, "__name__", "") for tool in extra_tools])
    skill_tools = SkillToolset(
        skills=[PORTFOLIO_STRESS_TEST, SKILL_AUTHOR, *extra_skills],
        additional_tools=[calculate_shock, stage_skill_draft, *extra_tools],
    )
    return Agent(
        model=MODEL,
        name="financial_assistant",
        instruction=(
            "You are the Lumenridge workshop portfolio assistant. Use the simulated data and "
            "portfolio values returned by your tools. For a simple quote, use "
            "get_stock_price directly. Label values as simulated and show money to two decimal "
            "places. Load a matching skill for portfolio analyses and explicit requests to "
            "draft a new skill. Follow the loaded skill's instructions. If a tool reports an "
            "error, explain it without inventing a value."
        ),
        tools=[
            FunctionTool(get_stock_price),
            FunctionTool(get_holdings),
            FunctionTool(get_position_values),
            skill_tools,
        ],
    )


root_agent = build_agent()
