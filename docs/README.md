# TutorGebra AI 📐🤖

TutorGebra AI is an automated, multilingual, interactive geometry and mathematics tutor. 

You provide a mathematical exercise in natural language, and the system uses **Gemini 2.5 Flash** to break it down into a step-by-step lesson plan. It then uses **Playwright** to take control of a Chromium browser, opens **GeoGebra Classic Web**, and physically draws the exercise step-by-step while a **Text-to-Speech (TTS)** engine reads the pedagogical explanations out loud in your preferred language.

## ✨ Features
- **Multilingual Support:** The AI automatically detects your input language (English, Spanish, French, etc.) and generates both the audio and UI responses in the same language.
- **Human-like Browser Automation:** Uses Bezier curves and deliberate cognitive pauses to simulate realistic human mouse movements and typing on the GeoGebra canvas.
- **Dynamic Interactivity:** Automatically enforces the creation of interactive sliders for dynamic variables, allowing you to manipulate the geometry after the automated lesson finishes.
- **Clean Architecture:** Built on a modern FastAPI backend with a beautiful Vue 3 + TailwindCSS frontend.

---

## 🛠️ Requirements & Dependencies

To run this project, you will need:
- **Python 3.12+**
- **uv** (The blazing-fast Python package manager)
- **Google Gemini API Key** (You can get one for free at Google AI Studio)

### Libraries Used:
- `fastapi` & `uvicorn` (Web server & REST API)
- `google-genai` (Official Gemini SDK for AI reasoning)
- `playwright` (Browser automation)
- `gTTS` (Google Text-to-Speech synthesis)
- `pygame` (Asynchronous audio playback)

---

## 🚀 How to Install and Run

**1. Clone or download the repository.**

**2. Open your terminal in the project root (`tutorgebra`) and initialize the virtual environment:**
```bash
uv venv
```

**3. Activate the virtual environment:**
- On Windows:
  ```bash
  .venv\Scripts\activate
  ```
- On macOS/Linux:
  ```bash
  source .venv/bin/activate
  ```

**4. Install the required dependencies:**
```bash
uv pip install -r requirements.txt
```

**5. Install the Chromium browser binaries for Playwright:**
```bash
playwright install chromium
```

**6. Start the TutorGebra server:**
```bash
python app/main.py
```

**7. Open the Web Interface:**
Go to your browser and visit: **http://localhost:8000**

---

## 🧠 How to Use

1. Once the web interface is open, paste your **Gemini API Key** in the designated field.
2. Type an exercise prompt in your language of choice. 
   *Example: "Draw a right triangle, calculate its hypotenuse using the Pythagorean theorem, and draw a circumscribed circle."*
3. Click on **"Summon the Tutor"**.
4. A Chromium window will open. **Do not touch your mouse or keyboard**. Watch as the AI types the algebraic commands and teaches you the mathematical concepts out loud!

---

## 💡 Example Prompts to Test / Prompts de Ejemplo

You can copy and paste any of these prompts directly into the TutorGebra interface to test different mathematical domains and GeoGebra tools. Prompts can be entered in Spanish, English, or any other supported language.

### 🟢 Geometría Básica (Basic Geometry)

* **Triángulo Rectángulo y Teorema de Pitágoras:**
  > *"Dibuja un triángulo rectángulo con catetos de longitud 3 y 4. Calcula la hipotenusa usando el teorema de Pitágoras y traza la circunferencia circunscrita."*
  > 
  > *(English)*: *"Draw a right triangle with legs of length 3 and 4. Calculate the hypotenuse using the Pythagorean theorem and draw its circumscribed circle."*

* **Puntos Notables de un Triángulo (Baricentro y Medianas):**
  > *"Construye un triángulo con vértices en A=(1,1), B=(7,2) y C=(3,6). Traza las medianas de cada lado y encuentra su baricentro."*
  > 
  > *(English)*: *"Construct a triangle with vertices at A=(1,1), B=(7,2), and C=(3,6). Draw the medians of each side and find its centroid."*

* **Polígono Regular e Incentro:**
  > *"Dibuja un pentágono regular centrado en el origen con radio 4. Traza las bisectrices de dos de sus ángulos y halla su circunferencia inscrita."*
  > 
  > *(English)*: *"Draw a regular pentagon centered at the origin with radius 4. Draw angle bisectors and show its incircle."*

---

### 🎛️ Geometría Dinámica y Deslizadores (Interactive Sliders)

* **Parábola Interactiva con Parámetros:**
  > *"Crea tres deslizadores: 'a' entre -5 y 5, 'b' entre -5 y 5, y 'c' entre -5 y 5. Grafica la función cuadrática f(x) = a*x^2 + b*x + c y marca su vértice."*
  > 
  > *(English)*: *"Create three sliders: 'a' from -5 to 5, 'b' from -5 to 5, and 'c' from -5 to 5. Plot the quadratic function f(x) = a*x^2 + b*x + c and mark its vertex."*

* **Círculo con Radio Dinámico y Recta Tangente:**
  > *"Crea un deslizador 'r' para el radio entre 1 y 10. Traza una circunferencia de radio r con centro en (0,0), coloca un punto sobre ella y traza su recta tangente."*
  > 
  > *(English)*: *"Create a slider 'r' for the radius from 1 to 10. Draw a circle of radius r centered at (0,0), place a point on it, and draw its tangent line."*

---

### 📈 Funciones y Geometría Analítica (Analytic Geometry)

* **Intersección de Recta y Circunferencia:**
  > *"Grafica la circunferencia x^2 + y^2 = 25 y la recta y = 2*x + 1. Encuentra y resalta los puntos de intersección entre ambas."*
  > 
  > *(English)*: *"Plot the circle x^2 + y^2 = 25 and the line y = 2*x + 1. Find and highlight the intersection points between them."*

* **Elipse y sus Focos:**
  > *"Dibuja una elipse con ecuación x^2/25 + y^2/9 = 1. Identifica y grafica sus focos, sus vértices y sus ejes mayor y menor."*
  > 
  > *(English)*: *"Draw an ellipse with equation x^2/25 + y^2/9 = 1. Identify and plot its foci, vertices, and major and minor axes."*

---

### 📐 Trigonometría (Trigonometry)

* **Círculo Unitario y Proyección de Seno y Coseno:**
  > *"Dibuja la circunferencia unitaria centrada en el origen. Crea un deslizador de ángulo 'alpha' de 0 a 360 grados, un punto móvil P sobre el círculo y segmentos perpendiculares a los ejes que ilustren el seno y el coseno de ese ángulo."*
  > 
  > *(English)*: *"Draw the unit circle at the origin. Create an angle slider 'alpha' from 0 to 360 degrees, a point P on the circle, and segments showing sine and cosine projections."*

---

### 🚀 Cálculo (Calculus)

* **Recta Tangente y Pendiente en una Cúbica:**
  > *"Grafica la función cúbica f(x) = x^3 - 3*x. Crea un deslizador 'x0' y traza la recta tangente a la función en el punto (x0, f(x0)) mostrando su pendiente."*
  > 
  > *(English)*: *"Plot the cubic function f(x) = x^3 - 3*x. Create a slider 'x0' and draw the tangent line to the curve at (x0, f(x0)) showing its slope."*

* **Derivadas y Puntos Críticos:**
  > *"Grafica la función f(x) = x^4 - 4*x^2. Calcula y grafica su derivada f'(x), y marca los puntos de máximos y mínimos locales."*
  > 
  > *(English)*: *"Plot the function f(x) = x^4 - 4*x^2. Plot its derivative f'(x) and highlight its local extrema (maxima and minima)."*