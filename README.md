# AI Astrologer — Setup & Run Guide

An AI-powered astrology web app. The backend uses **Flask** + **Groq** (hosted LLM) with optional **Tavily** web search. The frontend is a single `index.html` that calls the backend.

---

## Project Layout
```
.
├── astrologer_backend.py   # Flask API (Groq + Tavily)
├── index.html              # Frontend UI (vanilla HTML/JS)
├── requirements.txt        # Python dependencies
└── .env                    # Environment variables (you create this)
```
> Port: **8000** (backend).  
> Default API base URL in `index.html`: `http://localhost:8000`.

---

## Prerequisites
- Python **3.9+** (3.10/3.11 recommended)
- A **Groq API key** (required to generate readings)
- A **Tavily API key** (optional, used for search context)
- (Optional) A simple static server to serve `index.html` (recommended)

---

## 1) Python Environment
Create and activate a virtual environment:
```bash
python -m venv venv
# macOS/Linux
source venv/bin/activate
# Windows (PowerShell)
./venv/Scripts/Activate.ps1
```

Install dependencies:
```bash
pip install -r requirements.txt
# The backend uses the Groq SDK but it's not pinned in requirements.txt.
# Install it explicitly if needed:
pip install groq
```
> Note: `llama-cpp-python` is listed in `requirements.txt` but the provided backend does **not** import or use it.  
> You can keep it or remove it to speed up installation.

---

## 2) Environment Variables (`.env`)
Create a `.env` file in the project root with:
```
GROQ_API_KEY=your_groq_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here   # optional
```
- **GROQ_API_KEY** is **required** (the backend will otherwise reply: *“Sorry, Groq API is not configured.”*).
- **TAVILY_API_KEY** is optional; if set, the backend enriches responses with Tavily search results.

---

## 3) Start the Backend
Run the Flask app:
```bash
python astrologer_backend.py
```
You should see logs like:
```
 AI Astrologer Backend (Groq-powered) Starting...
Groq API configured: ✅/❌
Tavily API configured: ✅/❌
Server running on http://localhost:8000
```

Health check:
```bash
curl http://localhost:8000/health
```
Returns JSON:
```json
{
  "status": "healthy",
  "groq_configured": true,
  "tavily_configured": true
}
```

### Endpoints
- `POST /generate-reading`
  - **Body**:
    ```json
    {
      "name": "Jane Doe",
      "birthDate": "1998-05-05",
      "birthTime": "14:30",
      "birthPlace": "Guwahati, India"
    }
    ```
  - **Response**:
    ```json
    {
      "success": true,
      "reading": "…",
      "zodiac_sign": "Taurus"
    }
    ```

- `POST /ask-question`
  - **Body**:
    ```json
    {
      "name": "Jane Doe",
      "birthDate": "1998-05-05",
      "birthTime": "14:30",
      "birthPlace": "Guwahati, India",
      "question": "What does my chart say about career?"
    }
    ```
  - **Response**:
    ```json
    {
      "success": true,
      "answer": "…"
    }
    ```

- `GET /health` → status + whether Groq/Tavily are configured.

**Model**: The backend uses Groq with `MODEL_NAME = "llama3-8b-8192"` by default.  
You can change it in `astrologer_backend.py` (other commented options may include `mixtral-8x7b-32768`, `gemma-7b-it`).

---

## 4) Frontend
Open the UI:
- **Recommended:** serve the file to avoid file-origin quirks
  ```bash
  # from the project root
  python -m http.server 5500
  # then open http://localhost:5500/index.html
  ```
- **Alternative:** open `index.html` directly in the browser (the backend enables CORS).

**Workflow:**
1. Fill **Name**, **Birth Date**, **Birth Time**, **Birth Place**.
2. Click **Generate Astrology Reading** → calls `POST /generate-reading`.
3. Ask a follow-up question → calls `POST /ask-question`.

---

## Troubleshooting
- **401/403 or empty responses**: verify `GROQ_API_KEY` in `.env` and restart the backend.
- **`/health` shows `groq_configured: false`**: `.env` not loaded or variable name incorrect.
- **CORS/Network errors**: ensure the backend is running at `http://localhost:8000`. If you opened `index.html` from the file system, try serving it with `python -m http.server`.
- **Slow/timeout on Tavily**: Tavily is optional; unset `TAVILY_API_KEY` to skip web search context.

---

## Notes for Developers
- Logging is set to **INFO** level.
- Birth data validation enforces: `name`, `birthDate` (YYYY-MM-DD), `birthTime` (HH:MM), `birthPlace`.
- The backend computes **zodiac sign** from the birth date and may include it in responses.
- Prompting is tuned for **150–250 words**, personalized and practical.
- You can adjust `MODEL_NAME`, temperatures, and token limits inside `astrologer_backend.py`.

---


