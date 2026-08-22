# Prompt Engineering Document

**Checkpoint 2, Deliverable 6.** Source of truth: `src/rag/prompts.py`
(this document explains and justifies what's implemented there — it should
never drift out of sync with the code).

FitGen uses three structured prompts, layered together for every request:
a system prompt (identity + hard rules), a context prompt (injects
retrieved chunks + conversation memory), and implicit few-shot examples
embedded in the system prompt for edge cases.

---

## 1. System Prompt — Identity & Hard Rules

**Purpose:** Constrain the model's role and behavior *before* it ever sees
a user question, so grounding and safety rules apply consistently across
every turn rather than being re-stated per message.

```
You are FitGen, a certified-trainer-style fitness assistant. You generate
personalized workout plans and answer exercise questions using ONLY the
exercise and training-principle context provided to you below — never
invent exercises, sets/reps schemes, or safety claims that are not
supported by that context.

Rules you must always follow:
1. Ground every recommendation in the retrieved context...
2. Respect every constraint the user states...
3. You are not a medical professional...
4. If a question is unrelated to fitness/exercise/nutrition-for-training...
5. Keep answers structured and skimmable...
```
(Full text in `src/rag/prompts.py::SYSTEM_PROMPT`.)

**How it prevents hallucination/off-topic answers:** Rule 1 explicitly
forbids inventing exercises or safety claims not present in retrieved
context — this is the single biggest hallucination lever in a RAG system;
without it, an LLM will happily "fill in" a plausible-sounding exercise
even when retrieval returns weak matches. Rule 4 prevents scope creep
(e.g., a user asking FitGen to write their essay).

**Example it prevents:**
> User: "What's the capital of France?"
> Without Rule 4, a generic chatbot answers "Paris" — technically correct
> but outside the product's purpose and a sign the grounding isn't being
> enforced. With Rule 4, FitGen redirects to fitness topics instead.

---

## 2. Context Prompt — Retrieval Grounding + Memory Injection

**Purpose:** Deliver the actual retrieved chunks and recent conversation
history to the model in a structured format the model can't confuse with
its own general knowledge.

```
Retrieved context (use this, and only this, as your factual basis):
---
{context}
---

Conversation so far:
{chat_history}

User's new message: {question}
...
```
(Full text in `src/rag/prompts.py::CONTEXT_PROMPT_TEMPLATE`.)

**How it prevents hallucination:** By visually fencing off the retrieved
context (`---` delimiters) and explicitly instructing "use this, and only
this," the model is discouraged from blending retrieved facts with
parametric (training-data) knowledge about generic fitness advice, which
is exactly where unsupported claims sneak in.

**Example it prevents:**
> User: "Give me a 5-day advanced bodybuilding split with drop sets."
> If retrieval returns only beginner full-body content (because the
> dataset is thin on advanced bodybuilding-specific techniques like drop
> sets), the context fence makes it clear to the model that "drop sets"
> isn't in scope — the correct behavior is for FitGen to build the closest
> supported plan and flag the gap, rather than confidently inventing a
> drop-set protocol that isn't in the reference material.

---

## 3. Safety Refusal Prompting (embedded in System Prompt, Rule 3)

**Purpose:** Handle the single highest-stakes failure mode of a fitness
chatbot — recommending an exercise that could injure someone who has
already reported pain.

```
3. You are not a medical professional. For red-flag symptoms
(sharp/radiating pain, numbness, swelling, instability) tell the user to
stop and consult a doctor or physical therapist rather than prescribing
an exercise.
```

This is paired with `docs` context from
`data/raw/training_principles/04_injury_safety_modifications.md`, which
gives retrieval something concrete to surface (e.g., "squats hurt my
knees" → regression suggestions; "sharp shooting pain" → stop and see a
professional).

**Example it prevents:**
> User: "My shoulder makes a popping sound and hurts sharply when I raise
> my arm, what exercise should I do for it?"
> Without Rule 3, the model might try to be "helpful" and suggest a
> lighter shoulder exercise anyway. With Rule 3 + the injury-safety
> reference document in context, FitGen correctly refuses to prescribe
> anything and recommends professional care instead.

---

## Design rationale: why layering three prompts instead of one mega-prompt
Splitting identity/rules (system) from per-turn data (context) keeps the
system prompt reusable and cache-friendly (most LLM APIs, including
Gemini, cache/re-use the system instruction across a session more
efficiently than re-sending it inline every turn), while the context
prompt can change completely on every single message as retrieval results
change. It also makes each prompt independently testable and reviewable —
exactly what this document is doing.
