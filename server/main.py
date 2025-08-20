from __future__ import annotations

import shutil
import tempfile
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse

# yt_dlp must be installed and ffmpeg available in PATH
from yt_dlp import YoutubeDL

app = FastAPI(title="YouTube to MP3 (Private Backend)")

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "web"


@app.get("/health")
async def health() -> dict:
	return {"status": "ok"}


def _sanitize_filename(name: str) -> str:
	invalid = '<>:/\\|?*"\n\r\t'
	for ch in invalid:
		name = name.replace(ch, "_")
	return name.strip().strip(".") or f"audio_{uuid.uuid4().hex}"


@app.get("/api/download")
async def download(url: str = Query(..., description="YouTube video URL")) -> FileResponse:
	if not url or not isinstance(url, str):
		raise HTTPException(status_code=400, detail="Missing or invalid 'url'")

	# Create an isolated temp dir per request
	temp_dir_obj = tempfile.TemporaryDirectory(prefix="yt2mp3_")
	temp_dir = Path(temp_dir_obj.name)

	# Configure yt-dlp to extract audio as mp3
	output_template = str(temp_dir / "%(title)s.%(ext)s")
	ydl_opts = {
		"format": "bestaudio/best",
		"outtmpl": output_template,
		"postprocessors": [
			{
				"key": "FFmpegExtractAudio",
				"preferredcodec": "mp3",
				"preferredquality": "192",
			}
		],
		"noprogress": True,
		"nocheckcertificate": True,
		"quiet": True,
	}

	try:
		with YoutubeDL(ydl_opts) as ydl:
			info = ydl.extract_info(url, download=True)
			title = info.get("title") or "audio"
			target_name = _sanitize_filename(title) + ".mp3"

		# Find the resulting mp3 in temp dir
		mp3_candidates = sorted(temp_dir.glob("*.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)
		if not mp3_candidates:
			raise HTTPException(status_code=500, detail="Conversion failed: no MP3 produced")
		produced_file = mp3_candidates[0]

		# Move to a stable temp path so we can close the TemporaryDirectory and still serve
		stable_dir = Path(tempfile.gettempdir()) / "yt2mp3_downloads"
		stable_dir.mkdir(parents=True, exist_ok=True)
		stable_path = stable_dir / f"{uuid.uuid4().hex}_{target_name}"
		shutil.move(str(produced_file), str(stable_path))
	finally:
		# Cleanup the per-request temp directory
		temp_dir_obj.cleanup()

	headers = {
		"Cache-Control": "no-store",
		"Content-Disposition": f"attachment; filename=\"{stable_path.name}\"",
	}
	return FileResponse(
		path=str(stable_path),
		media_type="audio/mpeg",
		headers=headers,
	)


@app.get("/", response_class=HTMLResponse)
async def root_index() -> HTMLResponse:
	index_file = FRONTEND_DIR / "index.html"
	if index_file.exists():
		return FileResponse(str(index_file))
	# Minimal fallback UI
	return HTMLResponse(content=(
		"""<!doctype html>
<html>
<head>
<meta charset=\"utf-8\" />
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
<title>YouTube to MP3</title>
<style>
	body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;line-height:1.4;padding:24px;background:#0b1020;color:#e6e8f2}
	.card{max-width:720px;margin:0 auto;background:#121735;border:1px solid #232a4a;border-radius:14px;padding:24px;box-shadow:0 10px 30px rgba(0,0,0,0.35)}
	input[type=url]{width:100%;padding:12px 14px;border-radius:10px;border:1px solid #2a335c;background:#0f1430;color:#e6e8f2}
	button{margin-top:12px;padding:12px 16px;border:0;border-radius:10px;background:#5b8cff;color:#fff;font-weight:600;cursor:pointer}
	button:disabled{opacity:.6;cursor:not-allowed}
	.small{opacity:.75;font-size:.9rem}
	footer{margin-top:18px;opacity:.7}
	.notice{background:#1b2145;border:1px solid #2e3a78;border-radius:10px;padding:10px;margin-top:12px}
</style>
</head>
<body>
	<div class=\"card\">
		<h2>Private YouTube → MP3</h2>
		<p class=\"small\">Run your own backend. Only download content you’re allowed to.</p>
		<input id=\"url\" type=\"url\" placeholder=\"Paste YouTube URL…\" />
		<button id=\"btn\">Download MP3</button>
		<div class=\"notice small\">If this is deployed publicly, add rate limits and auth. Public YouTube‑to‑MP3 APIs are unstable; this is self‑hosted.</div>
		<footer class=\"small\">Backend: FastAPI + yt‑dlp + ffmpeg</footer>
	</div>
	<script>
	const btn = document.getElementById('btn');
	const input = document.getElementById('url');
	btn.addEventListener('click', async () => {
		const url = input.value.trim();
		if (!url) { alert('Please paste a YouTube URL.'); return; }
		btn.disabled = true; btn.textContent = 'Converting…';
		try {
			const resp = await fetch(`/api/download?url=${encodeURIComponent(url)}`);
			if (!resp.ok) {
				const text = await resp.text();
				throw new Error(text || `Request failed: ${resp.status}`);
			}
			const blob = await resp.blob();
			const disposition = resp.headers.get('Content-Disposition') || 'attachment; filename=\"audio.mp3\"';
			const match = disposition.match(/filename=\"?([^\";]+)\"?/i);
			const filename = match ? match[1] : 'audio.mp3';
			const link = document.createElement('a');
			link.href = URL.createObjectURL(blob);
			link.download = filename;
			document.body.appendChild(link);
			link.click();
			link.remove();
		} catch (e) {
			alert('Error: ' + (e && e.message ? e.message : e));
		} finally {
			btn.disabled = false; btn.textContent = 'Download MP3';
		}
	});
	</script>
</body>
</html>"""
	))