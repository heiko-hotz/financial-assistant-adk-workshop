"""Offline ADK checks for Module 1 skill activation and draft review."""

import io
import sys
import tempfile
import unittest
from contextlib import ExitStack, redirect_stderr
from pathlib import Path
from unittest.mock import AsyncMock, patch

from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.skills import load_skill_from_dir
from google.adk.tools.skill_toolset import SkillToolset
from google.adk.tools.tool_context import ToolContext
from google.genai import types

from module_01 import portfolio_lab
from module_01.financial_agent_app.agent import build_agent
from module_01.financial_agent_app.skills import stage_skill_draft


TARGET_WEIGHT_MARKDOWN = """---
name: target-weight
description: Calculate the position price change required to reach a target weight.
metadata:
  adk_additional_tools:
    - calculate_target_weight
---

Use the holdings and quotes, then call `calculate_target_weight`.
"""


def calculate_target_weight(
    current_position_value: float, other_portfolio_value: float, target_weight: float
) -> dict:
    target_value = other_portfolio_value * target_weight / (1 - target_weight)
    return {"required_move_pct": 100 * (target_value / current_position_value - 1)}


class ScriptedModel(BaseLlm):
    """Supply model replies offline and check each real ADK model request."""

    steps: list[tuple[set[str], set[str], types.Part]]

    async def generate_content_async(self, llm_request, stream=False):
        required, excluded, reply = self.steps.pop(0)
        actual = set(llm_request.tools_dict)
        if required - actual or excluded & actual:
            raise AssertionError(f"Unexpected tools in the model request: {sorted(actual)}")
        yield LlmResponse(
            content=types.Content(role="model", parts=[reply]),
            usage_metadata=types.GenerateContentResponseUsageMetadata(
                prompt_token_count=1, candidates_token_count=1, total_token_count=2
            ),
        )


class PortfolioSkillsTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.agent = build_agent()
        self.sessions = InMemorySessionService()

    async def new_context(self, *, agent=None):
        session = await self.sessions.create_session(
            app_name="portfolio-tests", user_id="learner"
        )
        return self.context_for(session, agent=agent)

    def context_for(self, session, *, agent=None):
        return ToolContext(
            InvocationContext(
                invocation_id=f"run-{session.id}",
                agent=agent or self.agent,
                session=session,
                session_service=self.sessions,
            )
        )

    async def skill_tools(self, context, *, agent=None):
        toolset = next(
            tool
            for tool in (agent or self.agent).tools
            if isinstance(tool, SkillToolset)
        )
        return {tool.name: tool for tool in await toolset.get_tools(context)}

    async def load_skill(self, context, skill_name, *, agent=None):
        tools = await self.skill_tools(context, agent=agent)
        return await tools["load_skill"].run_async(
            args={"skill_name": skill_name}, tool_context=context
        )

    async def test_runner_exposes_calculator_on_next_model_request(self):
        model = ScriptedModel(
            model="offline",
            steps=[
                (
                    {"get_stock_price", "get_holdings", "load_skill"},
                    {"calculate_shock", "stage_skill_draft"},
                    types.Part.from_function_call(
                        name="load_skill", args={"skill_name": "portfolio-stress-test"}
                    ),
                ),
                (
                    {"calculate_shock"},
                    {"stage_skill_draft"},
                    types.Part.from_function_call(
                        name="calculate_shock",
                        args={
                            "holdings": {"LUMR": 20, "AAPL": 100},
                            "quotes": {"LUMR": 245.5, "AAPL": 180},
                            "cash": 77_090,
                            "changes_pct": {"LUMR": -10},
                        },
                    ),
                ),
                (set(), set(), types.Part.from_text(text="The portfolio falls to $99,509.")),
            ],
        )
        self.agent.model = model
        runner = Runner(
            agent=self.agent,
            app_name="portfolio-tests",
            session_service=self.sessions,
            auto_create_session=True,
        )
        try:
            events = [
                event async for event in runner.run_async(
                    user_id="learner",
                    session_id="stress-test",
                    new_message=types.Content(
                        role="user", parts=[types.Part.from_text(text="What if LUMR drops 10%?")]
                    ),
                )
            ]
        finally:
            await runner.close()

        responses = [response for event in events for response in event.get_function_responses()]
        self.assertEqual([response.name for response in responses], ["load_skill", "calculate_shock"])
        self.assertEqual(responses[0].response["skill_name"], "portfolio-stress-test")
        self.assertEqual(responses[1].response["ending_value"], 99_509)
        self.assertEqual(responses[1].response["change_dollars"], -491)
        self.assertFalse(model.steps)

    async def test_activation_persists_only_in_the_session_that_loaded_it(self):
        original = await self.new_context()
        result = await self.load_skill(original, "skill-author")
        self.assertEqual(result["skill_name"], "skill-author")
        await self.sessions.append_event(
            original.session, Event(author=self.agent.name, actions=original.actions)
        )

        restored = await self.sessions.get_session(
            app_name="portfolio-tests", user_id="learner", session_id=original.session.id
        )
        self.assertIsNotNone(restored)
        restored_tools = await self.skill_tools(self.context_for(restored))
        fresh_tools = await self.skill_tools(await self.new_context())
        self.assertIn("stage_skill_draft", restored_tools)
        self.assertNotIn("stage_skill_draft", fresh_tools)

    async def test_approved_draft_can_be_loaded_and_used_in_a_fresh_session(self):
        original = await self.new_context()
        await self.load_skill(original, "skill-author")
        author_tools = await self.skill_tools(original)

        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / "target-weight"
            marker = Path(directory) / "executed.txt"
            python_source = (
                "from pathlib import Path\n"
                f"Path({str(marker)!r}).touch()\n"
                "\ndef calculate_target_weight(current_position_value, other_portfolio_value, target_weight):\n"
                "    target_value = other_portfolio_value * target_weight / (1 - target_weight)\n"
                "    return {'required_move_pct': 100 * (target_value / current_position_value - 1)}\n"
            )
            draft_result = await author_tools["stage_skill_draft"].run_async(
                args={
                    "skill_name": "target-weight",
                    "skill_markdown": TARGET_WEIGHT_MARKDOWN,
                    "python_source": python_source,
                },
                tool_context=original,
            )
            self.assertFalse(marker.exists(), "Staging a draft ran its Python source")
            self.assertFalse(folder.exists(), "Staging a draft wrote the proposed skill")
            self.assertEqual(draft_result["status"], "drafted")
            self.assertEqual(draft_result["python_source"], python_source)
            self.assertIn("error", await self.load_skill(original, "target-weight"))

            # Simulate a learner saving the Markdown and supplying a reviewed helper.
            folder.mkdir()
            (folder / "SKILL.md").write_text(draft_result["skill_markdown"], encoding="utf-8")
            reviewed_agent = build_agent(
                extra_skills=[load_skill_from_dir(folder)],
                extra_tools=[calculate_target_weight],
            )
            fresh = await self.new_context(agent=reviewed_agent)
            self.assertNotIn(
                "calculate_target_weight", await self.skill_tools(fresh, agent=reviewed_agent)
            )
            loaded = await self.load_skill(fresh, "target-weight", agent=reviewed_agent)
            self.assertEqual(loaded["skill_name"], "target-weight")
            fresh_tools = await self.skill_tools(fresh, agent=reviewed_agent)
            self.assertNotIn("stage_skill_draft", fresh_tools)
            result = await fresh_tools["calculate_target_weight"].run_async(
                args={
                    "current_position_value": 4_000,
                    "other_portfolio_value": 95_000,
                    "target_weight": 0.05,
                },
                tool_context=fresh,
            )
            self.assertAlmostEqual(result["required_move_pct"], 25)

    def test_draft_requires_both_markdown_and_python(self):
        for markdown, source in ((" ", "def example(): pass"), (TARGET_WEIGHT_MARKDOWN, " ")):
            with self.subTest(markdown=markdown, source=source):
                result = stage_skill_draft("target-weight", markdown, source)
                self.assertIn("error", result)

    def test_draft_rejects_a_path_as_a_skill_name(self):
        result = stage_skill_draft(
            "../target-weight", TARGET_WEIGHT_MARKDOWN, "def calculate_target_weight(): pass"
        )
        self.assertIn("error", result)


class ReviewedSkillCliTest(unittest.TestCase):
    def setUp(self):
        stack = ExitStack()
        self.addCleanup(stack.close)
        self.workspace = Path(stack.enter_context(tempfile.TemporaryDirectory()))
        stack.enter_context(patch.object(sys, "path", [str(self.workspace), *sys.path]))
        self.skill_dir = self.workspace / "target-weight"
        self.skill_dir.mkdir()
        self.skill_file = self.skill_dir / "SKILL.md"
        self.skill_file.write_text(TARGET_WEIGHT_MARKDOWN, encoding="utf-8")
        self.module_name = "module_1_reviewed_skill_test_fixture"
        self.tool_file = self.workspace / f"{self.module_name}.py"
        self.addCleanup(sys.modules.pop, self.module_name, None)

    def reviewed_args(self, tool=None):
        tool = tool or f"{self.module_name}:calculate_target_weight"
        return ["--reviewed-skill", str(self.skill_dir), "--reviewed-tool", tool]

    def assert_cli_error(self, args, message):
        stderr = io.StringIO()
        with (
            patch.object(sys, "argv", ["portfolio_lab", *args]),
            patch.object(portfolio_lab, "chat", new_callable=AsyncMock) as chat,
            redirect_stderr(stderr),
            self.assertRaises(SystemExit) as exit_context,
        ):
            portfolio_lab.main()
        self.assertEqual(exit_context.exception.code, 2)
        self.assertIn(message, stderr.getvalue())
        chat.assert_not_called()

    def test_reserved_tool_rejected_before_module_import(self):
        marker = self.workspace / "imported.txt"
        self.tool_file.write_text(
            "from pathlib import Path\n"
            f"Path({str(marker)!r}).touch()\n"
            "def get_stock_price(): return {'price': 100}\n"
            "def load_skill(): return {'skill_name': 'unexpected'}\n",
            encoding="utf-8",
        )
        for name in ("get_stock_price", "load_skill"):
            with self.subTest(name=name):
                self.skill_file.write_text(
                    TARGET_WEIGHT_MARKDOWN.replace("calculate_target_weight", name),
                    encoding="utf-8",
                )
                self.assert_cli_error(
                    self.reviewed_args(f"{self.module_name}:{name}"),
                    f"Unavailable name: {name!r}",
                )
                self.assertFalse(marker.exists(), "The rejected tool module was imported")

    def test_malformed_reviewed_arguments_are_cli_errors(self):
        self.assert_cli_error(self.reviewed_args()[:2], "Supply --reviewed-skill")
        self.assert_cli_error(self.reviewed_args()[2:], "Supply --reviewed-skill")
        for value in (self.module_name, ":calculate_target_weight", f"{self.module_name}:"):
            with self.subTest(value=value):
                self.assert_cli_error(self.reviewed_args(value), "MODULE:FUNCTION syntax")

    def test_unloadable_reviewed_skill_or_tool_is_a_cli_error(self):
        self.skill_file.unlink()
        self.assert_cli_error(self.reviewed_args(), "SKILL.md not found")

        self.skill_file.write_text("---\ninvalid: [\n---\nTest", encoding="utf-8")
        self.assert_cli_error(self.reviewed_args(), "Invalid YAML")

        self.skill_file.write_text(TARGET_WEIGHT_MARKDOWN, encoding="utf-8")
        self.assert_cli_error(self.reviewed_args(), f"No module named '{self.module_name}'")

        self.tool_file.write_text("def broken syntax", encoding="utf-8")
        self.assert_cli_error(self.reviewed_args(), f"{self.module_name}.py, line 1")

    def test_reviewed_skill_and_file_backed_tool_reach_chat(self):
        self.tool_file.write_text(
            "def calculate_target_weight(current: float, other: float, target: float) -> dict:\n"
            "    value = other * target / (1 - target)\n"
            "    return {'required_move_pct': 100 * (value / current - 1)}\n",
            encoding="utf-8",
        )

        async def check_reviewed_tool(agent, interval):
            sessions = InMemorySessionService()
            session = await sessions.create_session(app_name="portfolio-tests", user_id="learner")
            context = ToolContext(
                InvocationContext(
                    invocation_id="reviewed-cli-test",
                    agent=agent,
                    session=session,
                    session_service=sessions,
                )
            )
            toolset = next(tool for tool in agent.tools if isinstance(tool, SkillToolset))
            tools = {tool.name: tool for tool in await toolset.get_tools(context)}
            result = await tools["load_skill"].run_async(
                args={"skill_name": "target-weight"}, tool_context=context
            )
            self.assertEqual(result["skill_name"], "target-weight")
            tools = {tool.name: tool for tool in await toolset.get_tools(context)}
            result = await tools["calculate_target_weight"].run_async(
                args={"current": 4_000, "other": 95_000, "target": 0.05}, tool_context=context
            )
            self.assertAlmostEqual(result["required_move_pct"], 25)
            self.assertEqual(interval, 0)

        with (
            patch.object(sys, "argv", ["portfolio_lab", *self.reviewed_args()]),
            patch.object(portfolio_lab, "chat", side_effect=check_reviewed_tool) as chat,
        ):
            portfolio_lab.main()
        chat.assert_awaited_once()

    def test_agent_rejects_duplicate_and_reserved_tool_names(self):
        def load_skill():
            return {}

        for tools, name in (
            ([calculate_target_weight, calculate_target_weight], "calculate_target_weight"),
            ([load_skill], "load_skill"),
        ):
            with self.subTest(name=name):
                with self.assertRaisesRegex(ValueError, f"Unavailable name: {name!r}"):
                    build_agent(extra_tools=tools)


if __name__ == "__main__":
    unittest.main()
