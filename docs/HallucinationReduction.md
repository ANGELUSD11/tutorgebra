# TutorGebra AI

TutorGebra AI is an automated, interactive geometry tutor that translates user mathematical exercises into step-by-step GeoGebra scripts, accompanied by pedagogical TTS explanations.

## LLM Hallucination Reduction Findings

During the development and testing of the GeoGebra script generation agent, we encountered significant challenges with LLMs exhibiting "selective attention"—specifically, ignoring negative constraints (e.g., "Do NOT use X") when those constraints contradicted their strong internal priors or were buried in dense paragraphs.

**Key Finding:** 
The most effective approach to force strict compliance and eliminate hallucinations (like inventing non-existent variables or using prohibited commands like `RegularPolygon` or `Incircle` for n-gons) is **Extreme Visual Restructuring in the System Prompt**.

Instead of writing dense paragraphs of rules, negative constraints MUST be broken down into explicit, standalone bullet points prefixed with capitalized severity labels such as:
* **(CRITICAL):**
* **(FATAL ERROR):**
* **(FATAL SYNTAX WARNING):**

By decoupling the constraints into highly visible, independent items, the LLM parses them as distinct absolute rules rather than ignorable suggestions, resulting in a near-perfect zero-hallucination execution.

See `architecture.md` for a deeper dive into how the model makes decisions and obeys constraints.
