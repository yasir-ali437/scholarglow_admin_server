"use client";

import { useState, useRef, useEffect } from "react";

// ── Types ────────────────────────────────────────────────────────────────────
interface ProgressEvent {
  step: string;
  status: "running" | "done" | "error" | "complete";
  data?: {
    wp_url: string;
    poster_b64: string;
    post_b64: string;
    caption: string;
    title: string;
  };
}

interface Results {
  wp_url: string;
  poster_b64: string;
  post_b64: string;
  caption: string;
  title: string;
}

// ── Config ───────────────────────────────────────────────────────────────────
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Step log item ─────────────────────────────────────────────────────────────
function StepItem({ event }: { event: ProgressEvent }) {
  const dotClass =
    event.status === "running"
      ? "dot-running"
      : event.status === "done"
      ? "dot-done"
      : event.status === "error"
      ? "dot-error"
      : "dot-complete";

  const textColor =
    event.status === "error"
      ? "#ef4444"
      : event.status === "complete"
      ? "#6378ff"
      : event.status === "done"
      ? "#e2e8f0"
      : "#f4b400";

  return (
    <div className="step-item">
      <span className={`step-dot ${dotClass}`} />
      <span style={{ color: textColor, fontSize: "0.88rem", lineHeight: 1.5 }}>
        {event.step}
      </span>
    </div>
  );
}

// ── Result card ───────────────────────────────────────────────────────────────
function ResultCard({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="glass-card glow-border p-5">
      <p
        style={{
          color: "#6378ff",
          fontSize: "0.75rem",
          fontWeight: 700,
          letterSpacing: "0.1em",
          textTransform: "uppercase",
          marginBottom: "0.75rem",
        }}
      >
        {label}
      </p>
      {children}
    </div>
  );
}

// ── Copy button ───────────────────────────────────────────────────────────────
function CopyBtn({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={() => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }}
      style={{
        marginTop: "0.6rem",
        padding: "0.4rem 1rem",
        borderRadius: "0.5rem",
        background: copied ? "#22c55e22" : "rgba(99,120,255,0.12)",
        border: `1px solid ${copied ? "#22c55e55" : "rgba(99,120,255,0.3)"}`,
        color: copied ? "#22c55e" : "#8892b0",
        fontSize: "0.78rem",
        cursor: "pointer",
        transition: "all 0.2s",
      }}
    >
      {copied ? "✓ Copied!" : "Copy"}
    </button>
  );
}

// ── Download button ───────────────────────────────────────────────────────────
function DownloadBtn({ b64, filename }: { b64: string; filename: string }) {
  return (
    <a
      href={`data:image/png;base64,${b64}`}
      download={filename}
      style={{
        display: "inline-block",
        marginTop: "0.6rem",
        padding: "0.4rem 1.1rem",
        borderRadius: "0.5rem",
        background: "rgba(244,180,0,0.1)",
        border: "1px solid rgba(244,180,0,0.3)",
        color: "#f4b400",
        fontSize: "0.78rem",
        textDecoration: "none",
      }}
    >
      ⬇ Download PNG
    </a>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────
export default function Dashboard() {
  const [rawText, setRawText]       = useState("");
  const [applyLink, setApplyLink]   = useState("");
  const [officialLink, setOfficialLink] = useState("");
  const [events, setEvents]         = useState<ProgressEvent[]>([]);
  const [running, setRunning]       = useState(false);
  const [results, setResults]       = useState<Results | null>(null);
  const logRef = useRef<HTMLDivElement>(null);

  // Auto-scroll log
  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [events]);

  const handleRun = async () => {
    if (!rawText.trim() || !applyLink.trim() || !officialLink.trim()) return;
    setEvents([]);
    setResults(null);
    setRunning(true);

    try {
      const res = await fetch(`${API_BASE}/api/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          raw_text: rawText,
          apply_link: applyLink,
          official_link: officialLink,
        }),
      });

      if (!res.ok || !res.body) {
        throw new Error(`Server error: ${res.status}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split("\n\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith("data:")) continue;
          const jsonStr = trimmed.replace(/^data:\s*/, "");
          try {
            const event: ProgressEvent = JSON.parse(jsonStr);
            setEvents((prev) => [...prev, event]);
            if (event.status === "complete" && event.data) {
              setResults(event.data);
            }
          } catch {
            // ignore parse errors
          }
        }
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      setEvents((prev) => [
        ...prev,
        { step: `❌ Connection error: ${message}`, status: "error" },
      ]);
    } finally {
      setRunning(false);
    }
  };

  const canRun = rawText.trim() && applyLink.trim() && officialLink.trim() && !running;

  return (
    <div
      style={{
        minHeight: "100vh",
        padding: "2.5rem 1.5rem",
        maxWidth: 1280,
        margin: "0 auto",
        position: "relative",
        zIndex: 1,
      }}
    >
      {/* ── Header ── */}
      <div style={{ marginBottom: "2.5rem", textAlign: "center" }}>
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "0.6rem",
            padding: "0.4rem 1.2rem",
            borderRadius: "999px",
            background: "rgba(99,120,255,0.1)",
            border: "1px solid rgba(99,120,255,0.25)",
            marginBottom: "1rem",
          }}
        >
          <span style={{ color: "#6378ff", fontSize: "0.78rem", fontWeight: 600, letterSpacing: "0.08em" }}>
            SCHOLARGLOW ADMIN
          </span>
        </div>
        <h1
          style={{
            fontSize: "clamp(1.8rem, 4vw, 2.8rem)",
            fontWeight: 800,
            background: "linear-gradient(135deg, #e2e8f0 0%, #6378ff 60%, #f4b400 100%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            backgroundClip: "text",
            marginBottom: "0.5rem",
            letterSpacing: "-0.02em",
          }}
        >
          Content Pipeline
        </h1>
        <p style={{ color: "#8892b0", fontSize: "1rem" }}>
          Paste raw scholarship data → auto-generate blog, posters &amp; captions
        </p>
      </div>

      {/* ── Two-column layout ── */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "minmax(0, 1fr) minmax(0, 1fr)",
          gap: "1.5rem",
          alignItems: "start",
        }}
      >
        {/* ── LEFT: Input + Log ── */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>

          <div className="glass-card glow-border p-6" style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
            <h2 style={{ color: "#e2e8f0", fontWeight: 700, fontSize: "1.05rem", margin: 0 }}>
              📋 Scholarship Input
            </h2>

            <div>
              <label htmlFor="rawText">Raw Scholarship Text</label>
              <textarea
                id="rawText"
                rows={14}
                placeholder="Paste the full scholarship description here — program details, eligibility, benefits, deadline, etc."
                value={rawText}
                onChange={(e) => setRawText(e.target.value)}
              />
            </div>

            <div>
              <label htmlFor="applyLink">Apply Now Link</label>
              <input
                id="applyLink"
                type="url"
                placeholder="https://apply.university.edu/scholarship"
                value={applyLink}
                onChange={(e) => setApplyLink(e.target.value)}
              />
            </div>

            <div>
              <label htmlFor="officialLink">Official Website Link</label>
              <input
                id="officialLink"
                type="url"
                placeholder="https://www.university.edu/scholarship"
                value={officialLink}
                onChange={(e) => setOfficialLink(e.target.value)}
              />
            </div>

            <button className="accent-btn" onClick={handleRun} disabled={!canRun}>
              {running ? (
                <span style={{ display: "flex", alignItems: "center", gap: "0.6rem", justifyContent: "center" }}>
                  <span className="step-dot dot-running" style={{ display: "inline-block" }} />
                  Running Pipeline…
                </span>
              ) : (
                "🚀 Run Pipeline"
              )}
            </button>
          </div>

          {/* Pipeline log */}
          {events.length > 0 && (
            <div className="glass-card glow-border p-5">
              <p
                style={{
                  color: "#6378ff",
                  fontSize: "0.75rem",
                  fontWeight: 700,
                  letterSpacing: "0.1em",
                  textTransform: "uppercase",
                  marginBottom: "0.75rem",
                }}
              >
                ⚡ Pipeline Log
              </p>
              <div
                ref={logRef}
                style={{ maxHeight: "280px", overflowY: "auto", paddingRight: "0.25rem" }}
              >
                {events.map((ev, i) => (
                  <StepItem key={i} event={ev} />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* ── RIGHT: Results ── */}
        <div style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>

          {/* Empty state */}
          {!results && !running && events.length === 0 && (
            <div
              className="glass-card"
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                minHeight: 340,
                color: "#8892b0",
                flexDirection: "column",
                gap: "1rem",
              }}
            >
              <span style={{ fontSize: "3rem" }}>🎓</span>
              <p style={{ fontSize: "0.95rem", margin: 0 }}>
                Results will appear here after running the pipeline
              </p>
            </div>
          )}

          {/* Spinner while running, before first result */}
          {running && !results && (
            <div
              className="glass-card"
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                minHeight: 340,
                flexDirection: "column",
                gap: "1rem",
              }}
            >
              <div
                style={{
                  width: 48,
                  height: 48,
                  borderRadius: "50%",
                  border: "3px solid rgba(99,120,255,0.2)",
                  borderTopColor: "#6378ff",
                  animation: "spin 0.9s linear infinite",
                }}
              />
              <p style={{ color: "#8892b0", fontSize: "0.9rem", margin: 0 }}>
                Pipeline running — this takes ~60–90 seconds
              </p>
            </div>
          )}

          {/* Results */}
          {results && (
            <>
              {/* WordPress post link */}
              <ResultCard label="🌐 WordPress Post">
                <a
                  href={results.wp_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    color: "#6378ff",
                    fontWeight: 600,
                    fontSize: "0.9rem",
                    wordBreak: "break-all",
                    textDecoration: "none",
                    display: "block",
                    marginBottom: "0.5rem",
                  }}
                >
                  {results.wp_url}
                </a>
                <a
                  href={results.wp_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    display: "inline-block",
                    padding: "0.4rem 1.1rem",
                    borderRadius: "0.5rem",
                    background: "rgba(99,120,255,0.12)",
                    border: "1px solid rgba(99,120,255,0.3)",
                    color: "#8892b0",
                    fontSize: "0.78rem",
                    textDecoration: "none",
                  }}
                >
                  Open Post ↗
                </a>
              </ResultCard>

              {/* Landscape poster */}
              <ResultCard label="🖼️ Landscape Poster (1200×630)">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  className="result-img"
                  src={`data:image/png;base64,${results.poster_b64}`}
                  alt="Landscape scholarship poster"
                />
                <DownloadBtn b64={results.poster_b64} filename="landscape_poster.png" />
              </ResultCard>

              {/* Instagram poster */}
              <ResultCard label="📱 Instagram Poster (1080×1350)">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  className="result-img"
                  src={`data:image/png;base64,${results.post_b64}`}
                  alt="Instagram scholarship poster"
                  style={{ maxHeight: 420, objectFit: "contain", width: "100%" }}
                />
                <DownloadBtn b64={results.post_b64} filename="instagram_poster.png" />
              </ResultCard>

              {/* Social media caption */}
              <ResultCard label="💬 Social Media Caption">
                <pre
                  style={{
                    color: "#c8d6f0",
                    fontSize: "0.82rem",
                    lineHeight: 1.7,
                    whiteSpace: "pre-wrap",
                    wordBreak: "break-word",
                    margin: 0,
                    fontFamily: "inherit",
                  }}
                >
                  {results.caption}
                </pre>
                <CopyBtn text={results.caption} />
              </ResultCard>
            </>
          )}
        </div>
      </div>

      {/* ── Footer ── */}
      <p
        style={{
          textAlign: "center",
          color: "#4a5568",
          fontSize: "0.75rem",
          marginTop: "2.5rem",
        }}
      >
        ScholarGlow Admin Dashboard · Powered by GPT-4.1 + FastAPI
      </p>
    </div>
  );
}
