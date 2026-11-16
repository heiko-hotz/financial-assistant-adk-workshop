"""Use a selected retrieval strategy in a live ADK analyst turn."""

import os
from collections.abc import Callable
from pathlib import Path

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.agents.run_config import RunConfig
from google.adk.runners import InMemoryRunner
from google.adk.tools import FunctionTool
from google.genai import types


async def run_agent(
    question: str, search: Callable[[str], list[dict[str, str]]]
) -> str:
    """Show the tool excerpts and return the analyst's answer."""
    load_dotenv(Path(__file__).resolve().parents[1] / ".env.local")
    if not os.environ.get("GOOGLE_API_KEY"):
        raise RuntimeError("Set GOOGLE_API_KEY in the repository's .env.local to run the analyst.")

    searched = False

    def search_documents() -> dict:
        """Retrieve excerpts for the user's original question."""
        nonlocal searched
        passages = [
            {**passage, "citation": f"S{index}"}
            for index, passage in enumerate(search(question), start=1)
        ]
        searched = True
        return {"passages": passages}

    def configure_search(callback_context, llm_request):
        # A second call with this question would repeat the same retrieval.
        llm_request.config.tool_config = types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(
                mode="NONE" if searched else "ANY"
            )
        )

    search_tool = FunctionTool(search_documents)
    agent = Agent(
        model="gemini-3.5-flash-lite",
        name="lumenridge_analyst",
        instruction=(
            "You are an analyst in the fictional Lumenridge workshop. Call "
            "search_documents once before answering. Base your answer only on its "
            "excerpts. Cite each factual claim using the passage's citation ID "
            "in brackets, for example [S1]. "
            "If the evidence covers only part of the question, say which part you "
            "can answer and what the excerpts do not establish."
        ),
        tools=[search_tool],
        before_model_callback=configure_search,
    )
    used_search = False
    answer = []
    async with InMemoryRunner(agent=agent, app_name="rag_lab") as runner:
        session = await runner.session_service.create_session(
            app_name=runner.app_name, user_id="learner"
        )
        async for event in runner.run_async(
            user_id=session.user_id,
            session_id=session.id,
            new_message=types.Content(role="user", parts=[types.Part(text=question)]),
            run_config=RunConfig(max_llm_calls=3),
        ):
            for response in event.get_function_responses():
                if response.name == search_tool.name and "passages" in (response.response or {}):
                    used_search = True
                    passages = response.response["passages"]
                    print(f"Tool {search_tool.name} returned {len(passages)} excerpt(s).")
                    for passage in passages:
                        print(f"\n[{passage['citation']}] {passage['source']}\n{passage['text']}")
            if event.is_final_response() and event.content:
                answer.extend(
                    part.text for part in event.content.parts or [] if part.text and not part.thought
                )
    if not used_search:
        raise RuntimeError("The analyst did not retrieve excerpts for the question.")
    if not answer:
        raise RuntimeError("The analyst returned no answer.")
    return "\n".join(answer)
