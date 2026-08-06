# Module 4: Complex Multi-Agent Systems 🕸️

Master the orchestration of **Complex Workflows** using specialized agents working in concert.

![ADK Workshop Module 4](adk-workshop-module4.png)

## Overview

In this module, you build a **Autonomous Research Team**—a production-grade system where specialized AI personas collaborate to perform deep financial research, validate findings, and generate executive-level reports.

Unlike previous modules where a single agent handled tasks, this system uses **hierarchical orchestration** to break a complex problem (creating a strategy memo) into distinct phases: **Planning**, **Execution & Validation**, and **Reporting**.

## Agent Architecture

The core agent, `research_team`, is a **Sequential Agent** that orchestrates a three-stage pipeline:


### 1. Goal Refiner (The Planner)
*   **Type**: `Agent` (Gemini 3.5 Flash-Lite)
*   **Role**: Acts as the project lead. It takes the user's high-level, potentially vague question (e.g., "AI strategy?") and expands it into a detailed, technical research prompt suitable for a specialist analyst.
*   **Goal**: Ensure the downstream agents have clear, actionable instructions and use only facts retrieved from the simulated workshop documents.

### 2. Research Loop (The Execution Engine)
*   **Type**: `LoopAgent`
*   **Role**: Iteratively researches and reviews information to ensure quality *before* the final report is written.
*   **Components**:
    *   **RAG Analyst**: (Reused from Module 2) Uses the RAG tools to fetch simulated data from the Lumenridge Financial Group docs.
    *   **Compliance Officer**: (The Critic) Reviews the Analyst's findings for completeness, professional tone, and document support. It rejects unsupported claims and provides feedback for the next iteration. If the findings are fully grounded and sufficient, it outputs `READY_FOR_SUMMARY`.
    *   **Termination Checker**: A custom `BaseAgent` that monitors the Compliance Officer. If the review starts with the `READY_FOR_SUMMARY` signal, it immediately stops the loop, preventing unnecessary API calls.

### 3. Reporter (The Writer)
*   **Type**: `Agent` (Gemini 3.5 Flash-Lite)
*   **Role**: Uses only verified facts retrieved from the workshop documents to synthesize a polished **Lumenridge Financial Group Executive Memo**, without filling evidence gaps from general knowledge.
*   **Output**: A professionally formatted Markdown document with headers, bullet points, and strategic insights.

## Key Concepts Demonstrated

*   **Agent Reuse**: Importing the `root_agent` from Module 2 (`rag_analyst`) to use as a sub-agent in this new system.
*   **Loop Primitives**: Using `LoopAgent` for iterative refinement and self-correction.
*   **Custom Control Logic**: Implementing `TerminationChecker` (`BaseAgent`) to programmatically control workflow state based on LLM output.
*   **Sequential Pipelines**: Chaining agents where the output of one becomes the context for the next.

## Output Example

When you run this agent, you will see a trace of the team working:

1.  **Goal Refiner**: *"I will research the specific technical pillars of..."*
2.  **RAG Analyst**: *[Simulated Tool Calls to fetch docs]*
3.  **Compliance Officer**: *"The data looks good. READY_FOR_SUMMARY."*
4.  **Reporter**:

    ```markdown
    # Lumenridge Financial Group Executive Memo
    **To:** Executive Leadership Team
    **Subject:** AI Infrastructure Growth Strategy
    ...
    ```

## How to Run

You can test this complex workflow using the included test script:

```bash
python module_04/test_module_4.py
```

Or explore the architecture in the notebook:
*   `04_complex_workflows.ipynb`
