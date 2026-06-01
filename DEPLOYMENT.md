# ScholarGlow Admin Dashboard — Deployment Guide

## Local Development (Ready Now)

Both servers are already running:
- **Backend** → http://localhost:8000
- **Frontend** → http://localhost:3000

---

## Deploying for Free Online

### Option A — Render (Recommended, easiest)

**Backend on Render:**
1. Push your code to a GitHub repo
2. Go to https://render.com → New → Web Service
3. Connect the repo, set root directory to `admin_server/backend`
4. Build command: `pip install -r requirements.txt`
5. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Add environment variable: `OPENAI_API_KEY=your_key_here`

**Frontend on Vercel:**
1. Go to https://vercel.com → New Project
2. Connect repo, set root to `admin_server/frontend`
3. Add environment variable: `NEXT_PUBLIC_API_URL=https://your-render-backend.onrender.com`
4. Deploy

> ⚠️ **Important**: The pipeline uses local file paths for images (poster_logo, watermark, country_flags). On Render, you need to include those assets in the repo and update the paths in `poster_T7.py` and `post_T2.py` to use relative paths.

### Option B — Railway (Backend + Frontend together)
1. Push to GitHub
2. New project on Railway → add two services (backend + frontend)
3. Set env vars per service

---

## Environment Variables

| Variable | Where | Value |
|---|---|---|
| `OPENAI_API_KEY` | Backend (Render/Railway) | Your OpenAI API key |
| `NEXT_PUBLIC_API_URL` | Frontend (Vercel/Railway) | Backend URL |

---

## Local Asset Paths (required for poster generation)

The following files must be present for posters to generate:
```
E:\Scholarship Website\poster\poster_logo_bg_chatgpt_cropped.png
E:\Scholarship Website\poster\watermark_landscape_final.png
E:\Scholarship Website\poster\country_flags\*.png
```
These paths are hardcoded in `poster_T7.py` and `post_T2.py`. When deploying, commit these assets and update paths to be relative (e.g., `os.path.join(os.path.dirname(__file__), "assets", "logo.png")`).
