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
            Att1["1️⃣ Intento 1:\nLista de respaldo OpenRouter\nGPT-4o → Claude Sonnet 5.5 → GPT-4o-Mini"]
            Att2["2️⃣ Intento 2 (JSON inválido / error):\nGPT-4o"]
            Att3["3️⃣ Intento 3 (último recurso):\nGPT-4o-Mini"]
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

**Orden real de intentos (`app/agent.py`):** en modo `auto`, un problema `basic` se resuelve con `gpt-4o-mini`. Un problema `advanced` envía a OpenRouter la lista de respaldo `[gpt-4o, claude-sonnet-5.5, gpt-4o-mini]`, que OpenRouter recorre en ese orden si un proveedor falla. Si la respuesta no es un JSON válido o la llamada da error, el segundo intento fuerza `gpt-4o` y el tercero `gpt-4o-mini`. Si el usuario elige un modelo manualmente, los tres intentos se hacen con ese mismo modelo.

### 1. `gpt-4o-mini` (El Portero y Clasificador)
* **Rol:** Ejecutar OCR (Reconocimiento Óptico de Caracteres), clasificar la dificultad y resolver álgebra clásica.
* **Por qué es bueno:** Es increíblemente rápido y su costo por procesar imágenes es fraccional. Es brillante aislando variables algebraicamente (ej. despejar $y$ en $2x + 3y = 12$) y escribiendo código JSON sin romperlo.
* **Por qué es malo:** Tiene un razonamiento espacial pésimo. Alucina posiciones geométricas, ubica los polos matemáticos en lugares incorrectos y no tiene la profundidad académica para ecuaciones diferenciales o topología.

### 2. `claude-sonnet-5.5` (El Físico Matemático)
* **Rol:** Segundo modelo de la lista de respaldo para problemas universitarios avanzados.
* **Por qué es bueno:** Es el rey indiscutible de la deducción lógica compleja. Puede estructurar lecciones pedagógicas de altísimo nivel.
* **Por qué es malo:** Es muy costoso para procesar visión pesada (lo cual solucionamos extirpando la imagen). En OpenRouter sufre problemas de timeout (10 segundos) que cortan la respuesta JSON a la mitad si se toma demasiado tiempo pensando en problemas largos.

### 3. `gpt-4o` (El Respaldo de Alta Velocidad)
* **Rol:** Modelo primario para problemas avanzados y modelo forzado en el segundo intento.
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
    
    C5 -->|"Válido"| C6{"Longitud del Prompt<br/>len(prompt) ≤ MAX_PROMPT_CHARS (1000)"}
    C6 -->|"Excede el límite"| R5["413 Payload Too Large"]
    
    C6 -->|"Dentro del límite"| C7{"Prompt Vacío & Sin Imagen?<br/>not prompt.strip() and not image_b64"}
    C7 -->|"Vacío"| R6["400 Bad Request"]
    
    C7 -->|"Válido"| C8{"Lista Blanca de Modelos<br/>selected_model in ALLOWED_MODELS"}
    C8 -->|"Modelo no permitido"| R7["400 Bad Request<br/>(Anti-Cost Abuse)"]
    
    C8 -->|"Válido"| C9{"Lista Blanca de Voz gTTS<br/>voice in ALLOWED_GTTS_VOICES"}
    C9 -->|"Voz no permitida"| R8["400 Bad Request<br/>(Anti-SSRF en TLD)"]
    
    C9 -->|"Válido"| C10{"Lista Blanca de Voz Edge<br/>edge_voice in ALLOWED_EDGE_VOICES"}
    C10 -->|"Voz no permitida"| R9["400 Bad Request<br/>(Anti-Inyección SSML)"]
    
    C10 -->|"Válido"| AI["Ejecución Autorizada:<br/>Smart Routing & Agent Pipeline"]

    classDef reject fill:#fee2e2,stroke:#dc2626,stroke-width:2px,color:#991b1b;
    classDef pass fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#166534;
    classDef check fill:#e0f2fe,stroke:#0284c7,stroke-width:2px,color:#0369a1;

    class R1,R2,R3,R4,R5,R6,R7,R8,R9 reject;
    class AI pass;
    class C1,C2,C3,C4,C5,C6,C7,C8,C9,C10,RL1,RL2 check;
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
| **Voz Edge TTS (`edge_voice`)** | Inyección de SSML en la petición a Microsoft: `edge-tts` interpola el nombre de la voz sin escaparlo. | Lista blanca cerrada `ALLOWED_EDGE_VOICES` con las 6 voces de la interfaz; cualquier otra devuelve `400`. |
| **Selección de Modelo (`selected_model`)** | Abuso de costes de API contra la clave del servidor (`OPENROUTER_API_KEY`). | Lista blanca `ALLOWED_MODELS` restringida a los 4 modelos oficiales de la interfaz. |
| **Identificación de Cliente (`get_client_ip`)** | Evasión de Rate Limiting mediante falsificación de cabeceras `X-Forwarded-For`. | Extracción determinista del salto confiable del proxy de Railway (`TRUSTED_PROXY_HOPS`) y normalización con la librería `ipaddress`. |
| **Memoria de Rate Limit (`ip_requests`)** | Fuga de memoria / DoS por acumulación infinita de claves en el diccionario de IPs en memoria. | Límite máximo de IPs rastreadas (`MAX_TRACKED_IPS = 10,000`) y barrido periódico automático (`sweep_rate_limit_memory`). |
| **Tamaño de Carga (`read_json_body`)** | Saturación de memoria RAM por cuerpos JSON masivos o transferencias fragmentadas (*chunked*). | Lectura de flujo de red con corte estricto a los 6 MB (`MAX_BODY_BYTES`). |
| **Campo de Entrada (`prompt`)** | Consumo abusivo de tokens en llamadas LLM. | Límite de `MAX_PROMPT_CHARS` (1000) definido una sola vez en `app/security.py`; el backend responde `413` y el frontend recibe el mismo valor inyectado (contador y deshabilitación reactiva del botón). |
| **Errores del stream (`event_stream`)** | Fuga de información interna (estado de la cuenta de OpenRouter, respuestas crudas del modelo, trazas). | `logger.exception()` registra el detalle y el traceback solo en el servidor; el cliente recibe un mensaje genérico en el evento `error`. |
| **Procesamiento de Imágenes (`handleImageUpload`)** | Latencia y sobrecoste de tokens de visión en OpenRouter por fotos de alta resolución. | Redimensionamiento y recompresión *client-side* en Canvas HTML5 a JPEG máx 1600px antes de codificar en base64. |
| **Construcción de Contenedores (`.dockerignore`)** | Filtración involuntaria de claves de API (`.env`) en capas públicas de la imagen Docker. | Exclusión explícita de `.env` y `*.env` en el archivo `.dockerignore`. |

### 4. Configuración Compartida con el Frontend

El límite de caracteres del prompt se define una sola vez, en `MAX_PROMPT_CHARS` de `app/security.py`. Para que la interfaz use el mismo valor sin duplicarlo, `GET /` (`serve_ui` en `app/main.py`) inyecta en el `<head>` de la página servida:

```html
<script>window.TUTOR_CONFIG = {"maxPromptChars": 1000};</script>
```

`static/app.js` lee `window.TUTOR_CONFIG.maxPromptChars` al arrancar y lo expone a la plantilla (contador, aviso y botón deshabilitado). Para cambiar el límite basta con editar `MAX_PROMPT_CHARS` y reiniciar el servidor. El valor inyectado es solo informativo: el backend valida siempre con su propia variable.

---

## Presupuesto de Salida y Cobertura del System Prompt

### 1. Presupuesto de salida

La generación principal usa `max_tokens=1800` (`app/agent.py`), pensado para lecciones de 25 a 30 pasos sin que el JSON se trunque y dispare el bucle de reintentos. Va ligado a dos reglas de `app/system_prompt.md`:

* **Longitud del `speech`:** en lecciones de 12 pasos o menos, 2 o 3 frases por paso con los valores concretos y el porqué; en lecciones de más de 12 pasos, una sola frase de 20 palabras como máximo.
* **Cierre del JSON:** una lección admite hasta 30 pasos y el modelo nunca debe dejar el JSON sin cerrar.

Si se cambia `max_tokens`, hay que revisar esos límites del prompt, y viceversa.

### 2. Reglas generales añadidas

* **Dejar que GeoGebra calcule:** dentro de `command` no se escriben a mano valores que un comando puede calcular (intersecciones, áreas, pendientes). En el `speech` sí se calculan y se dicen.
* **Nombres distintos de los comandos:** ningún objeto se llama igual que un comando (`Center`, `Vertex`, `Area`...); se usa un sufijo (`CenterO`, `areaValue`).
* **Todo resultado numérico con nombre:** integrales, sumas y límites se asignan a un nombre descriptivo, porque GeoGebra asigna letras sueltas (`a`, `b`) a los resultados sin nombre.

### 3. Familias de comandos del diccionario

El modelo solo puede usar los comandos listados en el prompt, así que el diccionario define la cobertura. Además de la geometría básica, incluye:

| Área | Comandos |
| :--- | :--- |
| Medidas | `Area`, `Perimeter`, `Length`, `Slope`, `Radius`, `Circumference` |
| Intersecciones y puntos | `Intersect(obj1, obj2, n)`, `Point(objeto)` |
| Triángulos | `TriangleCenter(A, B, C, 4)` (ortocentro) |
| Cónicas | `Hyperbola`, `Parabola`, `MajorAxis`, `MinorAxis`, `Directrix`, `Asymptote`, `Eccentricity` |
| Funciones | `If` (a trozos), `Function` (dominio restringido), `Curve` (paramétricas) |
| Cálculo | `Limit`, `Derivative(f, 2)`, `InflectionPoint`, `TaylorPolynomial`, `IntegralBetween`, `UpperSum`, `LowerSum` |
| Vista y estilo | `ZoomIn`, `ShowGrid`, `ShowAxes`, `SetColor`, `SetLineThickness`, `SetPointSize`, `SetFilling`, `SetLineStyle`, `ShowLabel`, `SetVisibleInView` |
| Listas y lugares geométricos | `Sequence`, `Locus` |
| Estadística | `Mean`, `Median`, `SD`, `FitLine`, `BarChart`, `Histogram`, `BoxPlot` |

---

## Validación en CI

Los workflows `pr_validation.yml` y `manual_deploy.yml` validan la sintaxis con `python -m compileall -q app`, que recorre `app/` de forma recursiva e incluye `app/routers/`.
