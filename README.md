# AI Agent Workshop 🚀

Welcome to the **AI Agent Workshop**. In this workshop, you will learn how to build, deploy, and scale AI Agents using the **Google Agent Development Kit (ADK)** and **Gemini** models.

## project Overview

This project is a comprehensive guide to mastering AI Agents. You will progress through four distinct modules, starting from a basic financial assistant to complex multi-agent workflows.

## project Structure

The workshop is organized into the following modules:

- **[Module 1: The Zero-to-One Agent](module_01/01_fast_track_agent.ipynb)**: Build your first agent with tools to fetch stock prices.
- **[Module 2: RAG-Powered Agents](module_02/02_rag_agent.ipynb)**: Enhance agents with Retrieval-Augmented Generation (RAG) to query internal documents (Investment Policies, Market Outlooks).
- **[Module 3: Workflow Agents](module_03/03_workflow_agent.ipynb)**: Implement multi-step reasoning and manager-worker agent patterns.
- **[Module 4: Complex Multi-Agent Systems](module_04/04_complex_workflows.ipynb)**: Orchestrate complex workflows with specialized agents.

## Getting Started

### 1. Prerequisites
- Python 3.10+
- A Google AI Studio API Key

### 2. Environment Setup
Create a `.env.local` file in the root directory with your API key:
```bash
GOOGLE_API_KEY=your_api_key_here
```

### 3. Installation
Install the required dependencies:
```bash
pip install google-adk google-genai python-dotenv
```

## Technologies Used
- **Google ADK**: Framework for agent construction and orchestration.
- **Gemini Models**: State-of-the-art LLMs for reasoning and acting.
- **Python**: Core language for logic and integration.
