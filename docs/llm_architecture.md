# Architecture & Agent Logic

This document details the internal decision-making architecture of the TutorGebra AI agent, specifically focusing on how it interprets constraints and navigates the idiosyncratic behavior of the GeoGebra engine.

## The Challenge: LLM "Magic Wand" Syndrome
GeoGebra has a very specific web-engine dictionary. For instance, `AngleBisector` expects 3 points, `Incircle` expects a triangle, and `Polygon` takes adjacent vertices. However, when an LLM is prompted by a user to "draw the incircle of a pentagon", its internal priors strongly associate the word "incircle" with the GeoGebra command `Incircle()`. This causes the LLM to hallucinate variables (like `V3`) to satisfy the command's requirements, completely breaking the execution context.

## System Prompt Constraint Architecture
To force the LLM to make correct geometric decisions, the system relies on a heavily engineered `system_prompt.md`.

### 1. The Breakdown Strategy
LLMs suffer from "selective attention" when reading long paragraphs, especially if those paragraphs contain negative constraints ("Do NOT do X"). To fix this, constraints are extracted into single, visually distinct bullet points.

### 2. Severity Tagging
We use capitalized labels such as `(CRITICAL)`, `(FATAL ERROR)`, and `(FATAL SYNTAX WARNING)`. 
* **Mechanism:** The LLM's attention mechanism heavily weights capitalized, emotionally loaded words like "FATAL" or "CRITICAL". This forces the model to evaluate that specific bullet point before applying its standard heuristic prior.
* **Result:** When the LLM decides how to draw an incircle for a polygon, the `(FATAL ERROR)` tag overrides its impulse to use the `Incircle()` command, forcing it to fall back to the prescribed mathematical alternative (finding the midpoint and drawing a generic `Circle()`).

### 3. Constructive Alternatives (The "Shortcut" Method)
Telling an LLM "Don't do X" is often insufficient if it doesn't know what to do instead. The architecture dictates that every negative constraint MUST be immediately followed by a hardcoded geometric alternative.
* *Example:* Instead of just banning `AngleBisector` for polygons, the prompt provides the exact alternative: "The bisector of an interior angle at vertex V1 is simply `Line(Center, V1)`."
* *Decision Path:* User asks for bisector -> LLM wants to use `AngleBisector` -> LLM sees `(CRITICAL)` constraint banning it -> LLM reads the constructive alternative -> LLM implements `Line(Center, V1)`.

### 4. Empirical Discoveries (The `Vertex` workaround)
During user testing, it was discovered that while the LLM hallucinates when blindly passing a Polygon to commands expecting points, you *can* successfully force commands like `Incircle()` and `AngleBisector()` to work on regular polygons by explicitly extracting the vertices dynamically using `Vertex(polygon, n)`. 
By formatting this exact syntax requirement with a `**(CRITICAL):**` tag in the system prompt, the LLM reliably adopts the working syntax instead of inventing non-existent commands like `Polygon(center, vertex)`. This empirically proved that visual severity tagging is the most effective way to dictate LLM decision-making and restriction obedience.

## Conclusion
By treating the LLM as a system that requires explicit, visually aggressive interruption of its statistical priors, TutorGebra achieves near 100% compliance with GeoGebra's strict, undocumented engine quirks.
