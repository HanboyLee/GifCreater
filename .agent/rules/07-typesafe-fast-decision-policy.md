# TypeSafe Fast Decision Policy (Always-On System 1 Policy)

To ensure sub-second response times, minimize model latency, and eliminate hallucination, all decisions, branch routings, and option selections in this project MUST strictly follow this policy:

## 1. Default to Fast Thinking (System 1 First)

- For any tasks involving **Choice selection**, **Branch routing**, **Condition evaluation (Noul)**, or **Action/Risk scoring**, the agent **MUST NOT** let general-purpose LLMs generate arbitrary natural language or reasoning text.
- The agent **MUST** unconditionally employ the TypeSafe (`/typesafe-ai`) System One specification as an underlying programming primitive to achieve sub-second, calibrated judgments.

## 2. Follow Official TypeSafe Primitives

- **Choice (Multi-Option Selection)**: Select the optimal option from mutually exclusive candidates with full probability distributions and confidence scores.
- **Noul (Condition / Boolean Probability)**: Independently estimate the probability that a specific condition holds (True/Yes probability).
- **Score (Graded Dimension Scoring)**: Provide probability-weighted placement along a described, graded scale.
- **Speculative Fan-out**: Package all related decision branches and prospective follow-up questions within a single request against the same state. Never perform serial round-trips.

## 3. Verify and Escalate Mechanism

- **High Confidence (**`confidence >= 0.85`**)**: Treat as clear System 1 instinct. Directly consume and execute the selected action in milliseconds without waking the slow-thinking reasoning engine.
- **Low Confidence (**`confidence < 0.85`**)** or **Blockers Detected (**`has_blocker` **is True)**: Treat as ambiguous or high-risk. Immediately trigger the escalation cascade, engaging the System 2 engine (Reasoning models / Antigravity Chain-of-Thought) for deep contextual deduction, corrective reflection, or user clarification.

## 4. Code Owns the Workflow

- Deterministic code or the Agent CLI must always retain workflow ownership and state transitions.
- The model provides programmable semantic common sense only where strict business logic requires semantic understanding. Never allow the model to emit arbitrary executable code or volatile selectors directly.

