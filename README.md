# AI Agent Workshop 🚀

Welcome to the **AI Agent Workshop**. In this hands-on course, you will learn how to architect, build, and deploy production-grade AI Agents using the **Google Agent Development Kit (ADK)** and **Gemini** models.

## Project Overview

You will build a **Autonomous Financial Research Team** designed for enterprise use. This system evolves from a simple script into a sophisticated, multi-agent organization capable of complex financial reasoning, deep research, and executive reporting.

## The Agent Evolution

The workshop follows a progressive "Crawl, Walk, Run" methodology, where you build layers of capability module by module:

### Phase 1: The Specialist (Module 1 & 2)
You start by building individual experts:
*   **The Quant**: connected to live market data tools to fetch stock prices and perform financial math.
*   **The Analyst**: grounded in internal knowledge (Investment Policies, Strategy Papers) using Retrieval-Augmented Generation (RAG).

### Phase 2: The Manager (Module 3)
You introduce hierarchy:
*   **The Manager**: A routing agent that understands user intent and delegates tasks to the appropriate specialist, synthesizing their outputs into a coherent answer.

### Phase 3: The Organization (Module 4)
You implement complex orchestration:
*   **The Autonomous Team**: A full research department that can take a high-level goal (e.g., "Analyze our AI strategy"), break it down, perform iterative research loops with self-correction and compliance checks, and produce a polished executive memo.

## Workshop Structure

| Module | Topic | Key Concepts |
| :--- | :--- | :--- |
| **[Module 1](module_01/)** | **The Zero-to-One Agent** | Tools, Function Calling, Basic Reasoning |
| **[Module 2](module_02/)** | **RAG-Powered Agents** | Vector Ops, Embedding, Grounding, MCP |
| **[Module 3](module_03/)** | **Workflow Agents** | Hierarchical Delegation, Routing, State |
| **[Module 4](module_04/)** | **Complex Multi-Agent Systems** | Sequential & Loop Flows, Custom Logic, Self-Correction |

## Getting Started

### 1. Prerequisites
-   Python 3.10+
-   A Google AI Studio API Key

### 2. Environment Setup
1.  **Clone the repository**:
    ```bash
    git clone https://github.com/heiko-hotz/jpmorgan-ai-agent-workshop.git
    cd jpmorgan-ai-agent-workshop
    ```

2.  **Create a virtual environment**:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install google-adk google-genai python-dotenv chromadb
    ```

4.  **Configure API Key**:
    Create a `.env.local` file in the root directory:
    ```bash
    GOOGLE_API_KEY=your_api_key_here
    ```

### 3. Running the Workshop
Each module contains a Jupyter Notebook (`.ipynb`) for learning and a Python folder (e.g., `financial_agent_app/`) for the production-ready code.

Start with Module 1:
```bash
jupyter notebook module_01/01_fast_track_agent.ipynb
```

## Technologies Used
-   **Google ADK**: Framework for agent construction, orchestration, and evaluation.
-   **Gemini 2.5 Flash**: High-performance, cost-effective LLM for reasoning.
-   **ChromaDB**: Open-source embedding database for RAG.
-   **Model Context Protocol (MCP)**: Standard interface for connecting AI models to data.
