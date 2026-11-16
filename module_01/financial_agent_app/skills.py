"""The two skills used in the Python lab, represented inline as ADK Skills."""

import re

from google.adk.skills.models import Frontmatter, Skill


PORTFOLIO_STRESS_TEST = Skill(
    frontmatter=Frontmatter(
        name="portfolio-stress-test",
        description="Estimate how hypothetical stock price changes affect a simulated portfolio.",
        metadata={"adk_additional_tools": ["calculate_shock"]},
    ),
    instructions="""
1. If the user has not specified a ticker or the size and direction of its price change,
   ask for the missing detail. Do not assume a shock size.
2. Call get_holdings for the share counts and cash, and get_stock_price for each held
   stock. If a required quote is unavailable, report it and stop the calculation.
3. Call calculate_shock with the holdings, a mapping of tickers to unit prices, cash,
   and the price changes specified by the user. Pass whole percentages, so a 10% fall
   is -10. The calculator keeps cash and all other prices flat.
4. Report the starting value, ending value, and change in dollars and percent using the
   calculator's result. Identify the result as a simulated scenario.
""".strip(),
)


SKILL_AUTHOR = Skill(
    frontmatter=Frontmatter(
        name="skill-author",
        description="Draft a new reusable ADK skill and its Python calculation tool on request.",
        metadata={"adk_additional_tools": ["stage_skill_draft"]},
    ),
    instructions="""
Use this skill when asked to create or draft a new skill, even if the request mentions
a topic already covered by a different skill. Write a draft for the learner to review.

Draft a complete SKILL.md with YAML frontmatter followed by short instructions. Use
this example structure and adapt the name, description, function name, and steps:

---
name: example-analysis
description: Explain what the analysis does and when to use it.
metadata:
  adk_additional_tools:
    - calculate_example
---
1. Retrieve share counts and cash with get_holdings and quotes with get_stock_price.
2. Describe the inputs to calculate_example and when to ask the user for missing information.
3. Explain which results to report and how to handle unavailable data.

Write the named calculation function in plain Python with type annotations, a docstring,
and a dictionary result. Use a single top-level function with no other top-level code.
Use only the input values and ordinary arithmetic. Retrieve fixture data with the
existing agent tools. Check the input domain and explain the result units in the
function docstring. The function name must match the additional tool in the frontmatter.

For a target portfolio weight, tell the skill to call get_position_values(ticker).
Pass its current_position_value and other_portfolio_value directly to the calculator.
These two fields already include the relevant valuation and cash. If the tool returns
an error, report it and stop. The calculator also takes target_weight as a fraction
such as 0.05.
The position changes while the other value stays fixed. Return the required change as
a signed percentage under required_move_pct. A $4,000 position and $95,000 elsewhere
need a 25% rise to reach a 5% target. Negative values represent a fall.

Call stage_skill_draft with the skill's name, the complete Markdown text, and only the
Python source. Pass raw file contents without outer code fences. Tell the learner that
the draft is ready for review and explain one example they can use to check it.
""".strip(),
)


def stage_skill_draft(skill_name: str, skill_markdown: str, python_source: str) -> dict:
    """Return proposed SKILL.md and Python source for human review as plain text."""
    if len(skill_name) > 64 or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", skill_name):
        return {"error": "Use a lowercase kebab-case skill name of at most 64 characters."}
    if not skill_markdown.strip() or not python_source.strip():
        return {"error": "Include both the Markdown skill and the Python function."}
    return {
        "status": "drafted",
        "skill_name": skill_name,
        "skill_markdown": skill_markdown,
        "python_source": python_source,
    }
