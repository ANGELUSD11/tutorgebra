# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

TutorGebra turns a natural-language (or photographed) math exercise into a step-by-step lesson: an LLM (via OpenRouter) emits a JSON list of `{command, speech}` steps, the backend synthesizes TTS audio per step, and the browser replays the steps into an embedded GeoGebra applet while the audio plays.

## Commands

```bash
# Setup (requirements.txt is the source of truth — see "Gotchas")
python -m venv .venv
.venv\Scripts\activate            # Windows;  source .venv/bin/activate on Linux/Mac
pip install -r requirements.txt

# Run the dev server (http://localhost:8000) — must be run as a module from the repo root
python -m app.main
# or with reload
uvicorn app.main:app --reload --port 8000

# The only CI check (pr_validation.yml): syntax compilation
python -m py_compile app/*.py app/routers/*.py

# Docker (same image Railway builds)
docker build -t tutorgebra . && docker run -p 8000:8000 -e OPENROUTER_API_KEY=... tutorgebra
```

There is no test suite, linter, or formatter configured. There is no frontend build step.

Deployment is manual: the `Manual Deploy to Railway` workflow (`workflow_dispatch`) runs `railway up --service tutorgebra`.

### Environment variables

| Variable | Purpose |
| :--- | :--- |
| `OPENROUTER_API_KEY` | Server key, used when the user leaves the API key field blank. Loaded from `.env` locally. |
| `REDIS_URL` | Global rate limiting. Optional — if Redis is unreachable the app logs a warning and falls back to the in-memory limiter. |
| `ENVIRONMENT=production` / `RAILWAY_ENVIRONMENT_NAME` | Sets `IS_PRODUCTION`: disables `/docs`, `/redoc`, `/openapi.json` and turns on proxy-header trust by default. |
| `TRUST_PROXY_HEADERS`, `TRUSTED_PROXY_HOPS` | Control how `get_client_ip` reads `X-Forwarded-For` (Nth hop from the right). |
| `ALLOWED_ORIGINS` | Comma-separated extra CORS origins. |
| `PORT` | Listen port (Railway injects it). |

## Architecture

### Request lifecycle (`POST /api/run`)

1. **Gatekeeping** (`app/routers/exercises.py` + `app/security.py`), in this order: `X-Tutor-Client: TutorGebraWeb` header check (403) → client IP resolution → rate limit, 5 req/60s (Redis sliding-window ZSET in `app/redis_rate_limit.py`; in-memory fallback when it returns `False`) → size-capped streaming body read (6 MB) → per-field type/length checks → model allowlist → gTTS voice allowlist.
2. **LLM** (`app/agent.py::generate_geogebra_script`, sync, run via `asyncio.to_thread`):
   - `selected_model == "auto"` triggers Smart Routing: a `gpt-4o-mini` call does OCR + `basic`/`advanced` classification. `basic` stays on `gpt-4o-mini`. `advanced` replaces the image with the extracted text (to avoid vision cost) and sends OpenRouter the fallback list `[gpt-4o, claude-sonnet-5.5, gpt-4o-mini]`.
   - A 3-attempt loop narrows the model list on failure (attempt 2 → `gpt-4o`, attempt 3 → `gpt-4o-mini`). A manually selected model is retried as-is.
   - A response with no JSON object at all is not an error: it is wrapped as a single speech-only step (this is how topic refusals reach the user).
   - `sanitize_geogebra_command` rewrites `name = y = ...` to `name: y = ...`. It is the only deterministic post-processing of LLM output; everything else is enforced through the prompt.
3. **TTS** (`app/bot.py`): one task per step, either Edge TTS (async, when `edge_voice` is sent) or gTTS (blocking, in a thread), both bounded by `global_tts_semaphore` (4). Each MP3 is written to `audios/<session_id>/`, immediately base64-inlined into the step as `audio_url`, then deleted. So `audios/` normally holds only empty session folders.
4. **Response** is an SSE stream over the POST body (`data: {...}\n\n`) with `status` of `progress` (`message`, `percent`), `done` (`steps`, `session_id`, `meta`) or `error` (`detail`). Errors after the stream starts arrive as an `error` event, not an HTTP status. The frontend reads it with `response.body.getReader()`, not `EventSource`.

Session folders are removed by `/api/cleanup/{session_id}` (called via `navigator.sendBeacon`; strict UUID parse + realpath confinement in `app/routers/sessions.py`) and by a background task in `app/main.py` that every 10 minutes deletes folders older than 30 minutes and sweeps the in-memory rate-limit dict.

### `app/system_prompt.md` is core logic

This file is read from disk on every request and is where most GeoGebra-correctness "bug fixes" land. It encodes hard-won applet quirks (points must start uppercase or they become vectors; no single-letter or underscore names; `:` not `=` for named equations; no `RegularPolygon`, `Incenter`, `Circumcenter`; `Focus`/`Vertex`/`Extremum` return un-indexable tuples; 2D only; explicit `*` for matrices).

Convention when adding rules (see `docs/HallucinationReduction.md`): one standalone bullet per rule, prefixed with a bold capitalized severity tag such as `**[TOPIC] (CRITICAL):**` or `(FATAL ERROR)`, with a correct and an incorrect example. The output contract is `{"language": "...", "steps": [{"command", "speech"}]}`; GeoGebra commands are always English, `speech` is in the user's language.

### Frontend (`static/`)

Vue 3 global build, Tailwind and the GeoGebra applet are loaded from CDNs; `static/app.js` and `static/components/*.js` are plain ES modules served as-is. `index.html` holds the template and is served by `GET /` with no-cache headers. `app.js` owns the player: it iterates the steps, simulates typing the command, calls `ggbAppletInstance.evalCommand(cmd)`, and plays the step's inline audio. Images are downscaled client-side to max 1600px JPEG before upload.

Values duplicated between frontend and backend that must be changed together:

- Model list: `app.js` options ↔ `ALLOWED_MODELS` in `app/security.py` ↔ model IDs hardcoded in `app/agent.py`.
- gTTS voices: `app.js` options ↔ `ALLOWED_GTTS_VOICES` (maps to fixed `(lang, tld)` tuples — never derive `tld` from user input, gTTS interpolates it into a hostname).
- Prompt limit: `MAX_PROMPT_CHARS` (550) in both `app.js` and `app/security.py`.
- Bot header: `X-Tutor-Client: TutorGebraWeb`.

When changing `app.js`, bump the `?v=N` query on its `<script>` tag in `index.html`; `/static` is cached by browsers even though `index.html` is not.

## Gotchas

- `python app/main.py` (as written in `docs/README.md`) fails with an import error because modules use absolute `app.*` imports; use `python -m app.main`.
- `pyproject.toml` and `uv.lock` are stale: they list `google-genai` and lack `openrouter`, `redis` and `python-dotenv`, and the `tutorgebra:main` script entry does not exist. The Dockerfile and install scripts use `requirements.txt`.
- CI and the deploy workflow compile `app/*.py` only, so syntax errors in `app/routers/` are not caught by them.
- The docs still describe the pre-refactor layout and a slightly different retry order than `app/agent.py`; trust the code. `docs/architecture.md` (Spanish) is accurate for the security pipeline.
- User-facing HTTP error details are in Spanish; log messages and code comments are in English.
- User-supplied `api_key` values bypass the server key but still go through the same model allowlist and rate limit.
