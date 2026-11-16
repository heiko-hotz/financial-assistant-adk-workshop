"""Live Gemini checks. Run from the repository root.

The default is the short quote smoke test. Run --case stress and --case author
separately when working with a small API quota. --case all runs the full suite.
"""

import argparse
import ast
import asyncio
import math
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from google.adk.runners import InMemoryRunner
from google.adk.skills import load_skill_from_dir

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from module_01.financial_agent_app.agent import build_agent
from module_01.portfolio_lab import ModelCallPacer, Turn, model_call_interval, run_turn


async def new_session(runner: InMemoryRunner) -> str:
    session = await runner.session_service.create_session(app_name=runner.app_name, user_id="tester")
    return session.id


async def ask(runner: InMemoryRunner, prompt: str, session_id: str | None = None) -> Turn:
    if session_id is None:
        session_id = await new_session(runner)
    turn = await run_turn(runner, "tester", session_id, prompt)
    print(f"User > {prompt}")
    print("Tools:", " → ".join(str(call.name) for call in turn.calls) or "none")
    print(f"Agent > {turn.text}")
    if not turn.text.strip():
        raise AssertionError("Expected a final answer from the agent.")
    return turn


def tool_result(turn: Turn, name: str) -> dict:
    for response in turn.responses:
        if response.name == name:
            return response.response or {}
    raise AssertionError(f"No response from {name}.")


def check_skill(turn: Turn, skill_name: str, tool_name: str) -> None:
    for response in turn.responses:
        if response.name == "load_skill" and (response.response or {}).get("skill_name") == skill_name:
            return
        if response.name == tool_name:
            break
    raise AssertionError(f"Expected to load {skill_name} before using {tool_name}.")


async def check_quotes(runner: InMemoryRunner) -> None:
    quote = await ask(runner, "What is the simulated price of LUMR?")
    result = tool_result(quote, "get_stock_price")
    assert result.get("price") == 245.50 and result.get("source") == "simulated", result
    assert "245.50" in quote.text and "simulat" in quote.text.lower(), quote.text
    assert not any(call.name == "load_skill" for call in quote.calls), quote.calls

    unknown = await ask(runner, "What's the simulated quote for ZZZZ?")
    result = tool_result(unknown, "get_stock_price")
    assert result.get("error") and "price" not in result, result
    assert "ZZZZ" in unknown.text and "$" not in unknown.text, unknown.text


async def check_stress(runner: InMemoryRunner) -> None:
    turn = await ask(runner, "What happens to my portfolio if LUMR drops 10%?")
    check_skill(turn, "portfolio-stress-test", "calculate_shock")
    assert tool_result(turn, "get_holdings").get("cash") == 77_090
    assert tool_result(turn, "calculate_shock") == {
        "starting_value": 100_000,
        "ending_value": 99_509,
        "change_dollars": -491,
        "change_pct": -0.491,
    }
    assert "99509" in turn.text.replace(",", ""), turn.text

    session_id = await new_session(runner)
    unclear = await ask(runner, "What happens to my portfolio if LUMR drops?", session_id)
    assert not any(call.name == "calculate_shock" for call in unclear.calls), unclear.calls
    assert "?" in unclear.text, unclear.text
    clarified = await ask(runner, "LUMR falls 10%, and AAPL rises 5%.", session_id)
    assert tool_result(clarified, "calculate_shock") == {
        "starting_value": 100_000,
        "ending_value": 100_409,
        "change_dollars": 409,
        "change_pct": 0.409,
    }


def calculate_target_weight(
    current_position_value: float, other_portfolio_value: float, target_weight: float
) -> dict:
    """Reference calculator used to exercise reviewed skill registration in the live test."""
    if current_position_value <= 0 or other_portfolio_value <= 0 or not 0 < target_weight < 1:
        return {"error": "Provide positive values and a target weight between 0 and 1."}
    target_value = other_portfolio_value * target_weight / (1 - target_weight)
    return {"required_move_pct": (target_value / current_position_value - 1) * 100}


async def check_author(runner: InMemoryRunner, pacer: ModelCallPacer) -> None:
    draft_turn = await ask(
        runner,
        "Create a new skill called target-weight for finding the price move needed to "
        "reach a target portfolio weight. Name its Python tool calculate_target_weight.",
    )
    check_skill(draft_turn, "skill-author", "stage_skill_draft")
    draft = tool_result(draft_turn, "stage_skill_draft")
    assert draft.get("status") == "drafted" and draft.get("skill_name") == "target-weight"
    # Inspect the generated source as data. Use a known callable for the live reload check.
    [definition] = ast.parse(draft["python_source"]).body
    assert isinstance(definition, ast.FunctionDef) and definition.name == "calculate_target_weight"
    with TemporaryDirectory() as directory:
        skill_dir = Path(directory) / "target-weight"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(draft["skill_markdown"], encoding="utf-8")
        skill = load_skill_from_dir(skill_dir)
    assert skill.frontmatter.metadata["adk_additional_tools"] == ["calculate_target_weight"]
    assert "get_position_values" in skill.instructions, skill.instructions
    agent = build_agent(extra_skills=[skill], extra_tools=[calculate_target_weight])
    async with InMemoryRunner(
        agent=agent, app_name="reviewed_skill_test", plugins=[pacer]
    ) as reviewed_runner:
        applied = await ask(
            reviewed_runner,
            "How much would LUMR have to rise to reach 5% of my portfolio? Keep everything else flat.",
        )
    check_skill(applied, "target-weight", "calculate_target_weight")
    position = tool_result(applied, "get_position_values")
    assert position["current_position_value"] == 4_910, position
    assert position["other_portfolio_value"] == 95_090, position
    expected = calculate_target_weight(4_910, 95_090, 0.05)["required_move_pct"]
    actual = tool_result(applied, "calculate_target_weight")["required_move_pct"]
    assert math.isclose(actual, expected, abs_tol=0.00001), (actual, expected)
    assert "%" in applied.text, applied.text


CHECKS = {"quotes": check_quotes, "stress": check_stress, "author": check_author}


async def run_tests(case: str, interval: float) -> None:
    pacer = ModelCallPacer(interval)
    async with InMemoryRunner(
        agent=build_agent(), app_name="portfolio_skills_test", plugins=[pacer]
    ) as runner:
        for name, check in CHECKS.items():
            if case in ("all", name):
                if name == "author":
                    await check_author(runner, pacer)
                else:
                    await check(runner)
                print(f"PASS {name}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", choices=["all", *CHECKS], default="quotes")
    parser.add_argument("--model-call-interval", type=model_call_interval, default=5)
    args = parser.parse_args()
    asyncio.run(run_tests(args.case, args.model_call_interval))
