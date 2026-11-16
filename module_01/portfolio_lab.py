"""Run the Module 1 lab with `python -m module_01.portfolio_lab`.

After reviewing a draft, save SKILL.md in a directory named for the skill and
save its function in an importable Python module. Start a fresh chat with
`--reviewed-skill DIRECTORY --reviewed-tool MODULE:FUNCTION` to try it.
"""

import argparse
import asyncio
from dataclasses import dataclass
from importlib import import_module
from math import isfinite
from pathlib import Path

from google.adk.agents import Agent
from google.adk.agents.run_config import RunConfig
from google.adk.plugins.base_plugin import BasePlugin
from google.adk.runners import InMemoryRunner, Runner
from google.adk.skills import load_skill_from_dir
from google.genai import types
from yaml import YAMLError

from module_01.financial_agent_app.agent import build_agent, validate_extra_tool_names


@dataclass
class Turn:
    text: str
    calls: list[types.FunctionCall]
    responses: list[types.FunctionResponse]


class ModelCallPacer(BasePlugin):
    """Optionally leave time between requests when running on a low quota."""

    def __init__(self, interval: float):
        super().__init__(name="model_call_pacer")
        self.interval = interval
        self.next_call = 0.0
        self.lock = asyncio.Lock()

    async def before_model_callback(self, *, callback_context, llm_request):
        async with self.lock:
            clock = asyncio.get_running_loop().time
            delay = self.next_call - clock()
            if delay > 0:
                await asyncio.sleep(delay)
            self.next_call = clock() + self.interval


def model_call_interval(value: str) -> float:
    interval = float(value)
    if not isfinite(interval) or interval < 0:
        raise argparse.ArgumentTypeError("Use a finite, nonnegative number of seconds.")
    return interval


async def run_turn(runner: Runner, user_id: str, session_id: str, prompt: str) -> Turn:
    """Collect the visible answer and the ADK tool trace for a chat turn."""
    turn = Turn(text="", calls=[], responses=[])
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=types.Content(role="user", parts=[types.Part(text=prompt)]),
        run_config=RunConfig(max_llm_calls=12),
    ):
        turn.calls.extend(event.get_function_calls())
        turn.responses.extend(event.get_function_responses())
        if event.is_final_response() and event.content and event.content.parts:
            turn.text += "\n".join(
                part.text for part in event.content.parts if part.text and not part.thought
            )
    return turn


async def chat(agent: Agent, interval: float) -> None:
    plugins = [ModelCallPacer(interval)] if interval else []
    async with InMemoryRunner(agent=agent, app_name="portfolio_lab", plugins=plugins) as runner:
        session = await runner.session_service.create_session(
            app_name=runner.app_name, user_id="learner"
        )
        while True:
            try:
                prompt = input("You > ").strip()
            except EOFError:
                break
            if not prompt:
                break
            turn = await run_turn(runner, session.user_id, session.id, prompt)
            print("Tool calls:", " → ".join(str(call.name) for call in turn.calls) or "none")
            for response in turn.responses:
                data = response.response or {}
                if response.name == "stage_skill_draft" and data.get("status") == "drafted":
                    print(f"\nDraft {data['skill_name']}/SKILL.md\n{data['skill_markdown']}")
                    print(f"\nDraft Python tool\n{data['python_source']}\n")
                elif response.name == "load_skill":
                    print(f"Loaded skill: {data.get('skill_name', data.get('error'))}")
                elif response.name != "list_skills":
                    print(f"{response.name}: {data}")
            print(f"Agent > {turn.text}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviewed-skill", type=Path, help="Directory with a reviewed SKILL.md")
    parser.add_argument("--reviewed-tool", help="Reviewed, importable Python function (MODULE:FUNCTION)")
    parser.add_argument(
        "--model-call-interval", type=model_call_interval, default=0,
        help="Minimum seconds between model calls; use 13 for a 5 requests/minute quota.",
    )
    args = parser.parse_args()
    if bool(args.reviewed_skill) != bool(args.reviewed_tool):
        parser.error("Supply --reviewed-skill and --reviewed-tool together.")
    if args.reviewed_skill:
        module, separator, name = args.reviewed_tool.partition(":")
        if not separator or not name.isidentifier() or not all(
            part.isidentifier() for part in module.split(".")
        ):
            parser.error("--reviewed-tool must use MODULE:FUNCTION syntax.")
        try:
            validate_extra_tool_names([name])
            skill = load_skill_from_dir(args.reviewed_skill)
            expected_tools = skill.frontmatter.metadata.get("adk_additional_tools", [])
            if expected_tools != [name]:
                raise ValueError("The skill's adk_additional_tools must name the reviewed function.")
            tool = getattr(import_module(module), name, None)
            if not callable(tool) or getattr(tool, "__name__", None) != name:
                raise ValueError("The module must define the named callable.")
            agent = build_agent(extra_skills=[skill], extra_tools=[tool])
        except (OSError, ValueError, ImportError, SyntaxError, YAMLError) as error:
            parser.error(str(error))
    else:
        agent = build_agent()
    asyncio.run(chat(agent, args.model_call_interval))


if __name__ == "__main__":
    main()
