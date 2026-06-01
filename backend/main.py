"""
main.py — FastAPI backend for ScholarGlow Admin Dashboard.
Exposes a single SSE endpoint that streams pipeline progress.
"""

import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from pipeline import run_pipeline

app = FastAPI(title="ScholarGlow Admin API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class PipelineRequest(BaseModel):
    raw_text: str
    apply_link: str
    official_link: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/run")
async def run(req: PipelineRequest):
    """
    Streams Server-Sent Events (SSE) with pipeline progress.
    Each event is a JSON object:
      { step, status, data? }
    status values: "running" | "done" | "error" | "complete"
    """

    def event_stream():
        for event in run_pipeline(req.raw_text, req.apply_link, req.official_link):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
