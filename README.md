# AI Agent Workshop 🚀

Welcome to the **AI Agent Workshop**. In this workshop, you will learn how to build, deploy, and scale AI Agents using the **Google Agent Development Kit (ADK)** and **Gemini** models.

## Project Overview

In this workshop, participants build a **Financial Assistant Agent** designed for JP Morgan employees. This agent evolves from a simple script into a sophisticated, multi-agent system capable of complex financial reasoning and grounded data analysis.

## The Financial Assistant Agent

The agent you will build is a specialized AI system that acts as a digital companion for financial analysts. Over the course of the workshop, you will implement:

- **Real-Time Data Access**: Unlike standard LLMs, your agent will use **Tools** to fetch current market data and simulated stock prices.
- **Grounded Intelligence (RAG)**: The agent will be connected to internal JPM documents (Investment Policies, Strategy Papers) using Retrieval-Augmented Generation, ensuring its advice is consistent with firm standards and current outlooks.
- **Sophisticated Orchestration**: You will move from a single agent to a **Manager-Worker** architecture, where a lead agent coordinates specialized researchers and analysts to solve multi-step problems.
- **Professional Persona**: The agent is tuned to maintain a professional, analytical tone suitable for a banking environment.

## Project Structure

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
