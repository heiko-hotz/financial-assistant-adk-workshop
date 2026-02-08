# Module 3: Workflow Agents ⚙️

Take your agents beyond simple chat and move into **Complex Reasonings** and **Manager-Worker** patterns.

## What does this Agent do?

In this module, you build a **Hierarchical Workflow Agent** capable of delegating tasks and managing multi-step reasoning processes.

- **Manager-Worker Architecture**: You will implement a "Lead Agent" (The Manager) that doesn't do the work itself but instead analyzes the user's intent and delegates specific tasks to specialized "Worker" agents.
- **Workflow Orchestration**: Learn how to chain agent actions together, where the output of one agent becomes the context for the next, enabling the system to solve problems that are too complex for a single LLM call.
- **State Management**: The agent learns how to track the progress of a multi-step financial inquiry, ensuring that all sub-tasks are completed before delivering a final, synthesized answer to the user.

## Learning Objectives
- Design multi-step agent workflows.
- Implement hierarchical agent structures (Manager agents delegating to specialized worker agents).
- Manage state and dependencies between workflow steps.
- Handle agent hand-offs and collaboration.

## Key Files
- `03_workflow_agent.ipynb`: Focuses on manager-worker architectures.
- `manager_agent/`: Production-ready multi-agent orchestration code.

## Getting Started
Open [03_workflow_agent.ipynb](03_workflow_agent.ipynb) to start building hierarchical agent systems.
