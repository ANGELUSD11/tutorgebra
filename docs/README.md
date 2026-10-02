# TutorGebra AI 📐🤖

TutorGebra AI is an automated, multilingual, interactive geometry and mathematics tutor. 

You provide a mathematical exercise in natural language, and the system uses **OpenRouter** to route your requests to powerful AI models (like Google's latest Gemini) to break it down into a pedagogical step-by-step lesson plan. It then renders a beautifully integrated **Interactive GeoGebra Player** right in your browser, drawing the exercise step-by-step while a native **Text-to-Speech (TTS)** engine reads the mathematical explanations out loud in your preferred language and accent!

## ✨ Features
- **Embedded Interactive Player:** No external windows required! Watch the math unfold in a fully interactive embedded GeoGebra applet with Play, Pause, and Replay controls.
- **Multilingual & Native Accents:** Automatically detects your input language and allows you to customize the teacher's accent (e.g., Spanish from Spain/Mexico, English from US/UK/Australia, French).
- **Simulated Typing Terminal:** A modern, floating terminal overlay simulates the bot typing algebraic commands in real-time before executing them.
- **Dynamic Interactivity:** Automatically enforces the creation of interactive sliders for dynamic variables, allowing you to manipulate the geometry after the automated lesson finishes.
- **Responsive & Fullscreen Modes:** Works smoothly on different screen sizes and includes a gorgeous Fullscreen mode with a cinematic dark backdrop to focus entirely on the math.

---

## 🛠️ Requirements & Dependencies

To run this project, you will need:
- **Python 3.12+**
- **OpenRouter API Key** (You can get one for free at [openrouter.ai/keys](https://openrouter.ai/keys))

### Libraries Used:
- `fastapi` & `uvicorn` (Web server & REST API)
- `openrouter` (High-availability SDK for auto-routing to AI models)
- `gTTS` (Google Text-to-Speech synthesis)
- `Vue 3` & `TailwindCSS` (Frontend framework and styling)
- `GeoGebra JS API` (Interactive math rendering)

---

## 🚀 How to Install and Run

### The "1-Click" Way (Recommended)
We've included automated setup scripts that create a virtual environment, install all dependencies, and start the server for you.
- **Windows:** Double-click `install_and_run.bat`
- **Linux/Mac:** Run `bash install_and_run.sh` in your terminal.

### The Manual Way
1. Clone or download the repository.
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows: .venv\Scripts\activate
   # Mac/Linux: source .venv/bin/activate
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the TutorGebra server:
   ```bash
   python app/main.py
   ```
5. Open your browser and visit: **http://localhost:8000**

---

## 🧠 How to Use

1. Once the web interface is open, if you don't know how to get an API Key, click on the **"¿Cómo obtenerla?"** button for a quick tutorial.
2. Paste your **OpenRouter API Key** in the designated field (or leave it blank to use the server's default free key).
3. Select your preferred **Teacher Voice / Accent**.
4. Type an exercise prompt in your language of choice. 
   *Example: "Draw a right triangle, calculate its hypotenuse using the Pythagorean theorem, and draw a circumscribed circle."*
5. Click on **"Generar Lección"**.
6. Enjoy the show! Use the **Player Controls** to pause, advance to the next step, or restart the explanation at your own pace. Click the **Fullscreen** button on the top right of the board to maximize your focus.

## ⚠️ Potential API Key Errors (And How to Fix Them)

Since this project connects to a high-availability AI router (**OpenRouter**) using your API Key, you might occasionally encounter some error messages. Here is what they mean and how to handle them:

### 1. "This request requires more credits"
* **Why it happens:** OpenRouter checks if your account has enough funds/credits to cover the *maximum* possible tokens a model could generate before processing the request. Even if the models are virtually free, if your account balance is strictly $0.00 and you haven't enabled free tier limits, it might block the request.
* **What to do:** TutorGebra caps tokens to `2500` to prevent this, but if you still see it, ensure you have generated a valid key at `openrouter.ai/keys`. If using the free tier, ensure you are not hitting the rate limits of the free models.

### 2. "Service Unavailable" (Error 503)
* **Why it happens:** OpenRouter has an automatic **Fallback System**. If Google Gemini servers are saturated, it will automatically try to route you to Claude 3.5 Haiku, then GPT-4o-Mini, and so on. If *all* backup models are saturated (which is incredibly rare), you will get this error.
* **What to do:** Wait 30 seconds and click "Generate Lesson" again. The traffic jam will clear up.

### 3. "Invalid API Key" (Error 401)
* **Why it happens:** When copying and pasting your key from OpenRouter, you might have missed a letter or accidentally copied a blank space at the beginning. OpenRouter keys always start with `sk-or-v1-`.
* **What to do:** Delete the key you pasted in TutorGebra, go back to OpenRouter, copy it again, and paste it carefully.

---

## 🧪 Disclaimer & Contributing

**1. Experimental Project:** Please note that TutorGebra AI is an highly experimental project. It is currently being developed and maintained by a developer who does not possess advanced or specialized mathematical knowledge. Because mathematics is incredibly vast, many edge cases, complex geometrical constructions, and advanced calculus scenarios are not yet fully covered by the AI's internal guardrails. As a result, the application might occasionally crash, the AI might hallucinate invalid GeoGebra commands, or it might construct a mathematically flawed explanation.

**2. Contributions are Highly Encouraged:** If you encounter hallucinations, bad text formatting in the UI, GeoGebra syntax crashes, or mathematical logic errors, your help is warmly welcomed! Please feel free to open an **Issue** on the repository to report the bug, or submit a **Pull Request (PR)** if you know how to fix it in the code or system prompt. 

**3. Calling All Mathematicians:** This project relies on continuous collaboration. We desperately need the support of mathematicians, teachers, and domain experts who *actually* know the math to help us refine the model's inference rules. Your expertise can help us write better, stricter guardrails in the `system_prompt.md` to prevent the AI from making complex mathematical mistakes, ultimately creating a more robust and reliable educational tool for everyone.

---

## 💡 Example Prompts to Test / Prompts de Ejemplo

You can copy and paste any of these prompts directly into the TutorGebra interface to test different mathematical domains and GeoGebra tools. Prompts can be entered in Spanish, English, or any other supported language.

### 🟢 Geometría Básica (Basic Geometry)

* **Triángulo Rectángulo y Teorema de Pitágoras:**
  > *"Dibuja un triángulo rectángulo con catetos de longitud 3 y 4. Calcula la hipotenusa usando el teorema de Pitágoras y traza la circunferencia circunscrita."*

* **Puntos Notables de un Triángulo (Baricentro y Medianas):**
  > *"Construye un triángulo con vértices en A=(1,1), B=(7,2) y C=(3,6). Traza las medianas de cada lado y encuentra su baricentro."*

* **Polígono Regular e Incentro:**
  > *"Dibuja un pentágono regular centrado en el origen con radio 4. Traza las bisectrices de dos de sus ángulos y halla su circunferencia inscrita."*

---

### 🎛️ Geometría Dinámica y Deslizadores (Interactive Sliders)

* **Parábola Interactiva con Parámetros:**
  > *"Crea tres deslizadores: 'a' entre -5 y 5, 'b' entre -5 y 5, y 'c' entre -5 y 5. Grafica la función cuadrática f(x) = a*x^2 + b*x + c y marca su vértice."*

* **Círculo con Radio Dinámico y Recta Tangente:**
  > *"Crea un deslizador 'r' para el radio entre 1 y 10. Traza una circunferencia de radio r con centro en (0,0), coloca un punto sobre ella y traza su recta tangente."*

---

### 📈 Funciones y Geometría Analítica (Analytic Geometry)

* **Intersección de Recta y Circunferencia:**
  > *"Grafica la circunferencia x^2 + y^2 = 25 y la recta y = 2*x + 1. Encuentra y resalta los puntos de intersección entre ambas."*

* **Elipse y sus Focos:**
  > *"Dibuja una elipse con ecuación x^2/25 + y^2/9 = 1. Identifica y grafica sus focos, sus vértices y sus ejes mayor y menor."*

---

### 📐 Trigonometría (Trigonometry)

* **Círculo Unitario y Proyección de Seno y Coseno:**
  > *"Dibuja la circunferencia unitaria centrada en el origen. Crea un deslizador de ángulo 'alpha' de 0 a 360 grados, un punto móvil P sobre el círculo y segmentos perpendiculares a los ejes que ilustren el seno y el coseno de ese ángulo."*

---

### 🚀 Cálculo (Calculus)

* **Recta Tangente y Pendiente en una Cúbica:**
  > *"Grafica la función cúbica f(x) = x^3 - 3*x. Crea un deslizador 'x0' y traza la recta tangente a la función en el punto (x0, f(x0)) mostrando su pendiente."*

* **Derivadas y Puntos Críticos:**
  > *"Grafica la función f(x) = x^4 - 4*x^2. Calcula y grafica su derivada f'(x), y marca los puntos de máximos y mínimos locales."*