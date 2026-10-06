# LLM Classifier for TutorGebra

This document details the Artificial Intelligence models used in **TutorGebra**, their strengths, weaknesses in the mathematical domain, and their ideal use cases within the application.

TutorGebra uses a **Smart Routing** system that evaluates the difficulty of each problem and dynamically assigns the most suitable model, although the user can also manually select one.

---

## 1. GPT-4o-mini (`openai/gpt-4o-mini`)

OpenAI's lightest, fastest, and most cost-effective model, optimized for everyday reasoning tasks.

* **Strengths:**
  * **Speed and Cost:** Extremely fast response times and minimal cost per token.
  * **Basic Geometry:** Excellent at interpreting simple geometric shapes (squares, circles, elementary triangles).
  * **School-level Arithmetic and Algebra:** Solves linear and quadratic equations seamlessly.
* **Weaknesses:**
  * **Complex Spatial Reasoning:** Tends to "hallucinate" or fail when calculating precise coordinates in 3D or perspective problems.
  * **Advanced Mathematics:** Struggles with complex differential calculus or advanced analytical geometry.
* **Ideal Use Case in TutorGebra:**
  * Serves as the default "workhorse". It acts as the initial classifier to determine a problem's difficulty (preliminary OCR) and is used to render elementary or high-school level exercises that do not require deep analysis.

---

## 2. GPT-4o (`openai/gpt-4o`)

OpenAI's flagship multimodal model, designed for advanced reasoning and visual understanding.

* **Strengths:**
  * **Computer Vision (OCR & Graphics):** State-of-the-art vision capabilities. It is the best model for understanding user-uploaded mathematical diagrams, reading handwritten formulas, and grasping spatial relationships in an image.
  * **High-Level Mathematics:** Exceptional understanding of Analytical Geometry, Calculus, Physics, and Linear Algebra.
  * **Instruction Following:** Strictly adheres to the `system_prompt` to generate the exact JSON format required by GeoGebra.
* **Weaknesses:**
  * **Computational Cost:** More expensive and slightly slower to invoke compared to its mini version.
* **Ideal Use Case in TutorGebra:**
  * **Image Processing:** Whenever the user uploads a complex image, this is the recommended model.
  * University-level problems and calculations requiring multiple logical steps.
  * Automatic fallback (rescue model) when the mini model fails to generate a valid JSON.

---

## 3. Claude 3.5 Sonnet (`anthropic/claude-sonnet-5.5`)

Anthropic's industry-leading model for code generation and logical consistency.

* **Strengths:**
  * **Logical Consistency & Code:** Unbeatable at structuring commands (scripting). It generates GeoGebra commands (`Polygon`, `Segment`, `Intersect`) with astonishing syntactic precision.
  * **Zero-Shot Reasoning:** Rarely makes logical calculation errors in mathematical proofs or the construction of complex algebraic curves.
* **Weaknesses:**
  * **Visual Analysis:** While it possesses vision capabilities, GPT-4o usually performs slightly better in contexts involving very noisy or hand-drawn mathematical diagrams.
* **Ideal Use Case in TutorGebra:**
  * Solving abstract mathematical problems or purely textual logical proofs (without images).
  * Generating complex GeoGebra scripts with multiple variable dependencies (e.g., defining a slider and linking it to a function).

---

## 💡 The "Auto" System (Smart Routing)

When the user selects **"Auto"**, TutorGebra executes the following workflow:

1. **Pre-analysis (Cost-saving):** Calls `gpt-4o-mini`, passing the user's text and image, to extract any mathematical text and classify the difficulty as `"basic"` or `"advanced"`.
2. **If `"basic"`:** It continues using `gpt-4o-mini` to generate the GeoGebra commands and the tutor's voice script. This saves waiting time and API costs.
3. **If `"advanced"`:** It discards the original image to save unnecessary Vision API costs (since the text was extracted in step 1) and routes the pure text request to `gpt-4o` or `Claude 3.5 Sonnet` to resolve complex spatial reasoning with maximum accuracy.
