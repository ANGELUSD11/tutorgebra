# Flujo de Arquitectura y Ciclo de Vida: TutorGebra AI (v2 - OpenRouter Edition)

Este diagrama ilustra el viaje completo de una petición en TutorGebra, incluyendo la nueva **Gestión de Contenidos Inteligente (Smart Routing)**, el sistema de **Auto-Recuperación de Fallos (Retry Loop)** y la orquestación a través de **OpenRouter**.

```mermaid
flowchart TD
    %% ------------------- Nodos Principales -------------------
    User(("🧑‍🎓 Usuario Final"))
    UI["🖥️ Interfaz Vue.js (app.js)"]
    
    subgraph Infraestructura ["🛡️ Infraestructura en la Nube"]
        CF["☁️ Cloudflare WAF & DNS"]
        RLB["🔀 Railway Load Balancer"]
    end
    
    subgraph Backend ["⚡ Backend FastAPI (Python)"]
        RateLimit{"🚦 Rate Limiter\n(5 req / min)"}
        API_Run["🔌 Endpoint /api/run"]
        
        subgraph Routing ["🧠 Smart Content Routing"]
            OCR["👁️ gpt-4o-mini\n(Lector OCR & Clasificador)"]
            Decision{"🔀 Dificultad"}
            Strip["🗑️ Borrado de Imagen\n(Ahorro de Tokens Vision)"]
        end
        
        subgraph Recovery ["🛡️ Auto-Recovery Retry Loop"]
            Att1["1️⃣ Intento 1:\nClaude Sonnet 5.5\n(El Físico Genio)"]
            Att2["2️⃣ Intento 2 (Fallback 10s):\nGPT-4o\n(El Respaldo Rápido)"]
            Att3["3️⃣ Intento 3 (Fallback Dinero/Crash):\nGPT-4o-Mini\n(El Salvador Gratis)"]
            Rules["📝 system_prompt.md\n(Reglas de Letras Mayúsculas)"]
        end
        
        subgraph TTS ["🗣️ Módulo TTS (bot.py)"]
            Edge["🎙️ Edge TTS"]
            Base64["📦 Codificación Base64"]
        end
    end
    
    %% APIs Externas
    ExtOR["🌐 OpenRouter API"]
    ExtMS["🌐 Microsoft Edge Servers"]
    
    %% Ejecución Frontend
    subgraph Player ["🎬 Reproductor Frontend"]
        GeoGebra["📐 GeoGebra JS API\n(evalCommand)"]
        AudioCtx["🎵 HTML5 Audio"]
    end

    %% ------------------- Conexiones y Flujo -------------------
    
    %% 1. Petición inicial
    User -- "1. Texto y/o Imagen" --> UI
    UI -- "2. POST /api/run" --> CF
    CF -- "3. Tráfico Limpio" --> RLB
    RLB -- "4. Enruta a Réplica" --> RateLimit
    RateLimit -- "Permitido" --> API_Run
    
    %% 2. Smart Routing
    API_Run -- "5. Envía Prompt Crudo" --> OCR
    OCR -- "Petición OCR" --> ExtOR
    ExtOR -- "Texto Extraído + JSON" --> OCR
    OCR -- "Evalúa" --> Decision
    
    %% 3. Flujo de Decisión
    Decision -- "Básico\n(Álgebra/Geo)" --> Att3
    Decision -- "Avanzado\n(Cálculo/Variable Compleja)" --> Strip
    Strip -- "Extrae solo texto" --> Att1
    
    %% 4. Retry Loop
    Rules -. "Inyecta Restricciones de Geogebra" .-> Att1
    Rules -. "Inyecta Restricciones de Geogebra" .-> Att2
    Rules -. "Inyecta Restricciones de Geogebra" .-> Att3
    
    Att1 -- "Petición Lenta" --> ExtOR
    ExtOR -- "JSON Cortado (10s) o 402" --> Att1
    Att1 -- "Falla: JSONDecodeError" --> Att2
    
    Att2 -- "Petición Rápida" --> ExtOR
    ExtOR -- "Error 402 / Crash" --> Att2
    Att2 -- "Falla General" --> Att3
    
    ExtOR -- "Éxito JSON" --> TTS
    
    %% 5. Audio Synthesis
    TTS -- "Genera voz" --> Edge
    Edge -- "Solicita MP3" --> ExtMS
    ExtMS -- "Audio" --> Base64
    Base64 -- "JSON + Audio String" --> API_Run
    
    %% 6. Ejecución
    API_Run -- "Stream SSE" --> UI
    UI -- "Itera cada paso" --> Player
    Player -- "Grafica sin fallar (Puntos Mayúsculas)" --> GeoGebra
    Player -- "Habla" --> AudioCtx

    %% ------------------- Estilos -------------------
    classDef frontend fill:#3b82f6,stroke:#1d4ed8,stroke-width:2px,color:#fff;
    classDef cloud fill:#f59e0b,stroke:#b45309,stroke-width:2px,color:#fff;
    classDef backend fill:#10b981,stroke:#047857,stroke-width:2px,color:#fff;
    classDef routing fill:#f59e0b,stroke:#b45309,stroke-width:2px,color:#fff;
    classDef recovery fill:#ef4444,stroke:#991b1b,stroke-width:2px,color:#fff;
    classDef external fill:#6b7280,stroke:#374151,stroke-width:2px,color:#fff,stroke-dasharray: 5 5;
    
    class UI,Player,GeoGebra,AudioCtx frontend;
    class CF,RLB cloud;
    class API_Run,TTS,Edge,Base64,RateLimit backend;
    class OCR,Decision,Strip routing;
    class Att1,Att2,Att3,Rules recovery;
    class ExtOR,ExtMS external;
```

## Análisis de los Modelos en la Arquitectura

El sistema de enrutamiento distribuye inteligentemente el tráfico basándose en las fortalezas y debilidades de cada modelo, optimizando los costos de la API de OpenRouter.

### 1. `gpt-4o-mini` (El Portero y Clasificador)
* **Rol:** Ejecutar OCR (Reconocimiento Óptico de Caracteres), clasificar la dificultad y resolver álgebra clásica.
* **Por qué es bueno:** Es increíblemente rápido y su costo por procesar imágenes es fraccional. Es brillante aislando variables algebraicamente (ej. despejar $y$ en $2x + 3y = 12$) y escribiendo código JSON sin romperlo.
* **Por qué es malo:** Tiene un razonamiento espacial pésimo. Alucina posiciones geométricas, ubica los polos matemáticos en lugares incorrectos y no tiene la profundidad académica para ecuaciones diferenciales o topología.

### 2. `claude-sonnet-5.5` (El Físico Matemático)
* **Rol:** Modelo primario para problemas universitarios avanzados.
* **Por qué es bueno:** Es el rey indiscutible de la deducción lógica compleja. Puede estructurar lecciones pedagógicas de altísimo nivel.
* **Por qué es malo:** Es muy costoso para procesar visión pesada (lo cual solucionamos extirpando la imagen). En OpenRouter sufre problemas de timeout (10 segundos) que cortan la respuesta JSON a la mitad si se toma demasiado tiempo pensando en problemas largos.

### 3. `gpt-4o` (El Respaldo de Alta Velocidad)
* **Rol:** Modelo secundario de emergencia para problemas avanzados.
* **Por qué es bueno:** Tiene una inteligencia académica casi idéntica a Claude, pero transmite (streams) los resultados mucho más rápido a través de OpenRouter, eludiendo eficazmente los bloqueos de 10 segundos.
* **Por qué es malo:** Debido a su vasta base de datos matemáticos, tiene un sesgo inherente hacia la notación matemática estándar (ej. usar $z_1$, $z_2$ minúsculas en Variable Compleja). Esto obligó a la arquitectura a imponer restricciones estrictas en el System Prompt para forzarlo a usar Mayúsculas en los puntos y evitar crashear GeoGebra.
