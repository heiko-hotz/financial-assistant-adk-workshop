# Module 1: The Zero-to-One Agent 🚀

In this module, you will build your very first **AI Agent** using the Google Agent Development Kit (ADK).

![ADK Workshop Module 1](adk-workshop-module1.png)

## What does this Agent do?

In this module, you build a **Financial Assistant** that bridges the gap between static LLM reasoning and real-world data.

- **Overcoming Data Cut-offs**: By using an ADK **Tool** (`get_stock_price`), the agent can fetch "current" market data that was not available in its original training set. This workshop uses the fictitious Lumenridge ticker `LUMR` and a simulated price rather than live market data.
- **Analyzing vs. Fetching**: The agent doesn't just read back numbers. It uses its internal reasoning to interpret the stock prices, enabling it to answer complex questions like "How does the price of LUMR compare to Apple?" or "Provide an analysis of the current market leaders."
- **Interactive Persona**: Configured with a professional banking persona, the agent handles multi-turn conversations, maintaining context as you explore different financial queries.

## Learning Objectives
- Understand the core components of an AI Agent (Reasoning, Acting, Reflecting).
- Use the `google-adk` and `google-genai` libraries.
- Create and integrate a custom **Tool** (Python function) for fetching stock prices.
- Run an interactive chat session with your agent.

## Key Files
- `01_fast_track_agent.ipynb`: The main workshop notebook.
- `adk-workshop-module1.png`: Architecture diagram for the agent.
- `financial_agent_app/`: Production-ready version of the agent logic.

## Getting Started
Open the notebook [01_fast_track_agent.ipynb](01_fast_track_agent.ipynb) and follow the step-by-step instructions.
