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

---

## Pipeline de Seguridad, Blindaje y Validación (Zero-Trust)

Para garantizar la estabilidad y proteger la infraestructura en producción (Railway), se implementó una arquitectura de defensa en profundidad orientada a neutralizar vectores de ataque web (Path Traversal, SSRF, saturación de memoria/tokens, bypass de Rate Limiting y fuga de secretos).

### 1. Pipeline de Validación en `/api/run`

Toda solicitud entrante debe superar una serie de compuertas deterministas antes de que se autorice la llamada al agente de inteligencia artificial o a los motores de síntesis de voz.

```mermaid
flowchart TD
    Req["Petición HTTP POST /api/run"] --> C1{"Cabecera Anti-Bot<br/>X-Tutor-Client == 'TutorGebraWeb'"}
    C1 -->|"No / Falsificado"| R1["403 Forbidden"]
    C1 -->|"Válido"| C2["Resolución Segura de IP<br/>get_client_ip()"]
    
    C2 --> C3{"Rate Limiting<br/>(5 req / 60s)"}
    C3 -->|"Redis Online"| RL1["Sliding Window ZSET en Redis"]
    C3 -->|"Redis Offline"| RL2["Fallback Memoria Local<br/>+ sweep_rate_limit_memory()"]
    RL1 -->|"Excedido"| R2["429 Too Many Requests"]
    RL2 -->|"Excedido"| R2
    
    RL1 -->|"Permitido"| C4["Lectura de Body con Límite Duro<br/>read_json_body()"]
    RL2 -->|"Permitido"| C4
    
    C4 --> C5{"Tamaño Total Body<br/>≤ 6 MB"}
    C5 -->|"Excede / Chunked Abusivo"| R3["413 Payload Too Large"]
    C5 -->|"JSON Malformado / No Objeto"| R4["400 Bad Request"]
    
    C5 -->|"Válido"| C6{"Longitud del Prompt<br/>len(prompt) ≤ 550"}
    C6 -->|"Excede 550 chars"| R5["413 Payload Too Large"]
    
    C6 -->|"≤ 550 chars"| C7{"Prompt Vacío & Sin Imagen?<br/>not prompt.strip() and not image_b64"}
    C7 -->|"Vacío"| R6["400 Bad Request"]
    
    C7 -->|"Válido"| C8{"Lista Blanca de Modelos<br/>selected_model in ALLOWED_MODELS"}
    C8 -->|"Modelo no permitido"| R7["400 Bad Request<br/>(Anti-Cost Abuse)"]
    
    C8 -->|"Válido"| C9{"Lista Blanca de Voz gTTS<br/>voice in ALLOWED_GTTS_VOICES"}
    C9 -->|"Voz no permitida"| R8["400 Bad Request<br/>(Anti-SSRF en TLD)"]
    
    C9 -->|"Válido"| AI["Ejecución Autorizada:<br/>Smart Routing & Agent Pipeline"]

    classDef reject fill:#fee2e2,stroke:#dc2626,stroke-width:2px,color:#991b1b;
    classDef pass fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#166534;
    classDef check fill:#e0f2fe,stroke:#0284c7,stroke-width:2px,color:#0369a1;

    class R1,R2,R3,R4,R5,R6,R7,R8 reject;
    class AI pass;
    class C1,C2,C3,C4,C5,C6,C7,C8,C9,RL1,RL2 check;
```

### 2. Ciclo de Vida y Limpieza Segura de Sesiones (`/api/cleanup/{session_id}`)

Para eliminar de forma segura los audios temporales sin permitir ataques de borrado masivo o transversal de directorios (*Arbitrary File Deletion / Path Traversal*):

```mermaid
flowchart TD
    Client["Cliente (sendBeacon al cerrar pestaña)"] --> Req["POST / DELETE /api/cleanup/{session_id}"]
    Req --> V1{"1. Validación Sintáctica:<br/>uuid.UUID(session_id)"}
    V1 -->|"ValueError (.., /, \, scripts, etc.)"| Err400["400 Bad Request<br/>'Formato de session_id inválido'"]
    
    V1 -->|"UUID Válido"| V2["2. Resolución Canónica de Ruta<br/>folder = realpath(audios_path / safe_uuid)"]
    V2 --> V3{"3. Verificación de Confinamiento:<br/>dirname(folder) == realpath(audios_path)"}
    V3 -->|"Falso (Symlink o escape)"| Err400
    
    V3 -->|"Verdadero"| V4{"4. Carpeta Existe y es Directorio?<br/>os.path.isdir(folder)"}
    V4 -->|"Sí"| Rmtree["shutil.rmtree(folder)<br/>(Eliminación segura de la sesión)"]
    V4 -->|"No"| RespOk["200 OK {'status': 'ok'}"]
    Rmtree --> RespOk
    
    V2 -.->|"Excepción Inesperada"| Catch["Captura Genérica:<br/>logger.error(detalle)<br/>500 Internal Server Error (Mensaje Genérico)"]

    classDef reject fill:#fee2e2,stroke:#dc2626,stroke-width:2px,color:#991b1b;
    classDef pass fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#166534;
    classDef check fill:#e0f2fe,stroke:#0284c7,stroke-width:2px,color:#0369a1;

    class Err400,Catch reject;
    class RespOk,Rmtree pass;
    class V1,V2,V3,V4 check;
```

### 3. Matriz de Controles y Validaciones Implementadas

| Componente | Vulnerabilidad / Riesgo Mitigado | Mecanismo de Validación |
| :--- | :--- | :--- |
| **Sesiones (`/api/cleanup`)** | Path Traversal / Borrado masivo arbitrario de archivos con secuencias `%2e%2e` o `..`. | Validación estricta `uuid.UUID()` + confinamiento canónico mediante `os.path.realpath()`. |
| **Síntesis de Voz (`voice`)** | SSRF (*Server-Side Request Forgery*) mediante manipulación del parámetro TLD en Google Translate (`translate.google.{tld}`). | Lista blanca cerrada `ALLOWED_GTTS_VOICES` mapeada a tuplas fijas e inmutables `(lang, tld)`. |
| **Selección de Modelo (`selected_model`)** | Abuso de costes de API contra la clave del servidor (`OPENROUTER_API_KEY`). | Lista blanca `ALLOWED_MODELS` restringida a los 4 modelos oficiales de la interfaz. |
| **Identificación de Cliente (`get_client_ip`)** | Evasión de Rate Limiting mediante falsificación de cabeceras `X-Forwarded-For`. | Extracción determinista del salto confiable del proxy de Railway (`TRUSTED_PROXY_HOPS`) y normalización con la librería `ipaddress`. |
| **Memoria de Rate Limit (`ip_requests`)** | Fuga de memoria / DoS por acumulación infinita de claves en el diccionario de IPs en memoria. | Límite máximo de IPs rastreadas (`MAX_TRACKED_IPS = 10,000`) y barrido periódico automático (`sweep_rate_limit_memory`). |
| **Tamaño de Carga (`read_json_body`)** | Saturación de memoria RAM por cuerpos JSON masivos o transferencias fragmentadas (*chunked*). | Lectura de flujo de red con corte estricto a los 6 MB (`MAX_BODY_BYTES`). |
| **Campo de Entrada (`prompt`)** | Consumo abusivo de tokens en llamadas LLM y desbordamiento de búfer lógico. | Límite estricto de 550 caracteres en backend (`413`) + contador y deshabilitación reactiva en frontend (`:disabled="!canGenerate"`). |
| **Procesamiento de Imágenes (`handleImageUpload`)** | Latencia y sobrecoste de tokens de visión en OpenRouter por fotos de alta resolución. | Redimensionamiento y recompresión *client-side* en Canvas HTML5 a JPEG máx 1600px antes de codificar en base64. |
| **Construcción de Contenedores (`.dockerignore`)** | Filtración involuntaria de claves de API (`.env`) en capas públicas de la imagen Docker. | Exclusión explícita de `.env` y `*.env` en el archivo `.dockerignore`. |

