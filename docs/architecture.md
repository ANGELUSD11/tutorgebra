# Flujo de Arquitectura y Ciclo de Vida: TutorGebra AI

Este diagrama ilustra el viaje completo de una petición en TutorGebra, desde el clic del usuario hasta la renderización matemática y reproducción de voz.

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
        API_Run["🔌 Endpoint /api/run\n(SSE Stream)"]
        ThreadPool["⚙️ ThreadPoolExecutor\n(200 Hilos I/O)"]
        
        subgraph Agent ["🤖 Agente de IA (agent.py)"]
            Prompt["📝 system_prompt.md\n(Reglas GeoGebra)"]
            GeminiClient["🧠 Gemini API Client"]
        end
        
        subgraph TTS ["🗣️ Módulo TTS (bot.py)"]
            Edge["🎙️ Edge TTS\n(Asíncrono)"]
            Gtts["🎙️ gTTS\n(Hilos Nativos)"]
            Base64["📦 Codificación Base64\n(Memoria Volátil)"]
        end
    end
    
    %% APIs Externas
    ExtGemini["🌐 Google Gemini API"]
    ExtMS["🌐 Microsoft Edge Servers"]
    ExtG["🌐 Google Translate Servers"]
    
    %% Ejecución Frontend
    subgraph Player ["🎬 Reproductor Frontend"]
        GeoGebra["📐 GeoGebra JS API\n(evalCommand)"]
        AudioCtx["🎵 HTML5 Audio\n(Base64 Playback)"]
    end

    %% ------------------- Conexiones y Flujo -------------------
    
    %% 1. Petición inicial
    User -- "1. Escribe Prompt + API Key\nClic en 'Generate'" --> UI
    UI -- "2. POST /api/run\n(Payload JSON)" --> CF
    CF -- "3. Tráfico Limpio / HTTPS" --> RLB
    RLB -- "4. Enruta a Réplica\n(Round-Robin)" --> RateLimit
    
    %% 2. Backend Processing
    RateLimit -- "Permitido" --> API_Run
    RateLimit -. "Bloqueado" .-> UI
    API_Run -- "5. Inicia Tarea Asíncrona" --> ThreadPool
    ThreadPool -- "Llama Agente" --> GeminiClient
    Prompt -. "Inyecta Restricciones" .-> GeminiClient
    GeminiClient -- "6. Request GenAI" --> ExtGemini
    ExtGemini -- "JSON Crudo" --> GeminiClient
    GeminiClient -- "Lista de Pasos\n(Comandos + Texto)" --> ThreadPool
    
    %% 3. Audio Synthesis
    ThreadPool -- "Procesa Pasos" --> Edge
    ThreadPool -- "Procesa Pasos" --> Gtts
    Edge -- "Request" --> ExtMS
    Gtts -- "Request" --> ExtG
    ExtMS -- ".mp3 temporal" --> Base64
    ExtG -- ".mp3 temporal" --> Base64
    Base64 -- "Destruye archivo local,\ndevuelve String 100% Stateless" --> API_Run
    
    %% 4. Respuesta SSE
    API_Run -- "7. Stream (SSE)\nJSON + Base64 Audio" --> UI
    
    %% 5. Ejecución Frontend
    UI == "8. Extrae Paso Actual" ===> GeoGebra
    GeoGebra -. "Simula Tecleo" .-> GeoGebra
    GeoGebra -. "Inyecta Fórmula" .-> GeoGebra
    GeoGebra == "9. Reproduce Audio" ===> AudioCtx
    AudioCtx == "Termina (onended)\nAvanza Siguiente" ===> UI

    %% ------------------- Estilos -------------------
    classDef frontend fill:#3b82f6,stroke:#1d4ed8,stroke-width:2px,color:#fff;
    classDef cloud fill:#f59e0b,stroke:#b45309,stroke-width:2px,color:#fff;
    classDef backend fill:#10b981,stroke:#047857,stroke-width:2px,color:#fff;
    classDef ai fill:#8b5cf6,stroke:#5b21b6,stroke-width:2px,color:#fff;
    classDef tts fill:#ec4899,stroke:#be185d,stroke-width:2px,color:#fff;
    classDef external fill:#6b7280,stroke:#374151,stroke-width:2px,color:#fff,stroke-dasharray: 5 5;
    
    class UI,Player,GeoGebra,AudioCtx frontend;
    class CF,RLB cloud;
    class API_Run,RateLimit,ThreadPool,Base64 backend;
    class GeminiClient,Prompt ai;
    class Edge,Gtts tts;
    class ExtGemini,ExtMS,ExtG external;
```
