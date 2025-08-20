## YouTube to MP3 (Private Backend)

A minimal full‑stack app that converts a YouTube link to an MP3 using a self‑hosted backend powered by FastAPI and `yt-dlp`.

Important:
- Only download content that you own or have permission to use. Respect creators’ rights and the platform’s Terms of Service.
- Public YouTube‑to‑MP3 APIs are unstable; this project runs a private backend you can deploy yourself (Docker/Render/Heroku/VPS).

### Tech stack
- Backend: FastAPI (Python), `yt-dlp`, `ffmpeg`
- Frontend: Static HTML/JS

### Local development
1. System dependency: `ffmpeg` must be installed and available in `PATH`.
2. Create a virtual environment and install Python deps:
   ```bash
   cd /workspace
   python3 -m venv .venv
   source .venv/bin/activate
   pip install --upgrade pip
   pip install -r server/requirements.txt
   ```
3. Run the server:
   ```bash
   uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload
   ```
4. Open the UI at `http://localhost:8000/`.

### Docker
Build and run locally:
```bash
docker build -t yt2mp3 .
docker run --rm -p 8000:8000 yt2mp3
```

### Deploying
- Render: Create a Web Service from this repo. Use the Dockerfile or a Python environment with a Start Command like `uvicorn server.main:app --host 0.0.0.0 --port 10000`. Ensure `ffmpeg` is installed (Docker image recommended).
- Railway/Heroku/VPS: Use the Dockerfile or install `ffmpeg` and run the same command.

### API
- `GET /api/download?url=<youtube_url>` → returns an MP3 file download.
- `GET /health` → `{ "status": "ok" }`

### Notes
- Conversion uses `yt-dlp` with `FFmpegExtractAudio` to produce a 192kbps MP3.
- Temporary files are cleaned up after each request.

