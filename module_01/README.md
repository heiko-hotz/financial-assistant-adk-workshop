# Module 1: From a Quote Tool to Portfolio Skills

Build an ADK assistant that works with simulated stock quotes and holdings. Start with a Python quote tool, then use an ADK skill to coordinate several tools for a portfolio analysis. Finally, ask the agent to draft a new skill and calculation tool for you to review and try.

1. **Look up a quote.** Ask for LUMR’s simulated price and use the tool trace to see how a direct lookup works. Try an unknown ticker to see how the tool reports missing data.
2. **Stress the portfolio.** Ask what happens if LUMR falls 10%. The agent loads the portfolio stress skill, gathers holdings and quotes, and calls a Python calculator. The simulated portfolio falls from $100,000 to $99,509, a loss of $491 (0.491%).
3. **Draft and reuse a skill.** Ask the agent for a target-weight skill. It returns the proposed `SKILL.md` and Python function as text. Review both before optionally registering them in a fresh agent session.

Open [01_fast_track_agent.ipynb](01_fast_track_agent.ipynb) from the workshop’s Python 3.10+ environment. The lab was tested with Google ADK 2.8.0. Start with `RUN_LIVE = False` to run the local calculator exercises. Set `RUN_LIVE = True` to try the agent with Gemini 3.5 Flash-Lite. Live examples use `GOOGLE_API_KEY` from the repository’s `.env.local`. Register a reviewed draft in the final section.

For the terminal version, run this from the repository root with the workshop environment activated. Adjust the interval to match your project's Gemini request limit.

```bash
python -m module_01.portfolio_lab --model-call-interval 5
```

The notebook and CLI share the fixtures, calculator, and agent in [financial_agent_app/](financial_agent_app/).
