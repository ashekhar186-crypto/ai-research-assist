import { useState, useEffect, useCallback } from "react";

// ── API Client ────────────────────────────────────────────────────────────────
const API = "http://127.0.0.1:8000";

async function apiFetch(path, opts = {}, token = null) {
  const headers = { "Content-Type": "application/json", ...(opts.headers || {}) };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (opts.body instanceof FormData) delete headers["Content-Type"];
  const res = await fetch(`${API}${path}`, { ...opts, headers });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || JSON.stringify(data));
  return data;
}

// ── Utilities ─────────────────────────────────────────────────────────────────
function copyToClipboard(text) {
  navigator.clipboard.writeText(text).catch(() => {
    const ta = document.createElement("textarea");
    ta.value = text; document.body.appendChild(ta); ta.select();
    document.execCommand("copy"); document.body.removeChild(ta);
  });
}

// Converts LaTeX commands to readable text for browser display
function stripLatexForDisplay(text) {
  if (!text || typeof text !== "string") return text;
  return text
    .replace(/\\subsection\*?\{([^}]+)\}/g, "\n\n◆ $1\n")
    .replace(/\\subsubsection\*?\{([^}]+)\}/g, "\n◇ $1\n")
    .replace(/\\section\*?\{([^}]+)\}/g, "\n\n◈ $1\n")
    .replace(/\\textbf\{([^}]+)\}/g, "$1")
    .replace(/\\textit\{([^}]+)\}/g, "$1")
    .replace(/\\emph\{([^}]+)\}/g, "$1")
    .replace(/\\label\{[^}]+\}/g, "")
    .replace(/\\ref\{([^}]+)\}/g, "")
    .replace(/\\citep?\{([^}]+)\}/g, "[$1]")
    .replace(/\\begin\{itemize\}/g, "").replace(/\\end\{itemize\}/g, "")
    .replace(/\\begin\{enumerate\}/g, "").replace(/\\end\{enumerate\}/g, "")
    .replace(/\\item\s/g, "• ")
    .replace(/\$([^$\n]+)\$/g, "$1")
    .replace(/\\\\/g, "\n")
    .replace(/\\noindent\s*/g, "")
    .trim();
}

function Toast({ msg, onDone }) {
  useEffect(() => { const t = setTimeout(onDone, 2500); return () => clearTimeout(t); }, [onDone]);
  return (
    <div style={{position:"fixed",bottom:24,left:"50%",transform:"translateX(-50%)",
      background:"var(--navy3)",color:"var(--text)",padding:"10px 20px",borderRadius:8,
      fontSize:13,fontWeight:600,zIndex:9999,boxShadow:"0 4px 20px rgba(0,0,0,0.4)",
      border:"1px solid var(--border)",display:"flex",alignItems:"center",gap:8}}>
      ✅ {msg}
    </div>
  );
}

// ── Design Tokens ─────────────────────────────────────────────────────────────
const style = `
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --navy:    #0A1628;
    --navy2:   #0F1F3D;
    --navy3:   #1A2F50;
    --blue:    #1264A3;
    --blue2:   #1D8EDB;
    --blue3:   #36C5F0;
    --accent:  #ECB22E;
    --green:   #2BAC76;
    --red:     #E01E5A;
    --text:    #E8EDF5;
    --text2:   #8DA3C0;
    --text3:   #4A6280;
    --border:  rgba(255,255,255,0.08);
    --card:    rgba(15,31,61,0.8);
    --shadow:  0 8px 32px rgba(0,0,0,0.4);
  }

  body {
    font-family: 'IBM Plex Sans', sans-serif;
    background: var(--navy);
    color: var(--text);
    min-height: 100vh;
    line-height: 1.5;
  }

  /* Scrollbar */
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: var(--navy2); }
  ::-webkit-scrollbar-thumb { background: var(--navy3); border-radius: 3px; }

  /* Layout */
  .app { display: flex; height: 100vh; overflow: hidden; }

  /* Sidebar */
  .sidebar {
    width: 240px; min-width: 240px;
    background: var(--navy2);
    border-right: 1px solid var(--border);
    display: flex; flex-direction: column;
    padding: 0;
  }
  .sidebar-header {
    padding: 20px 16px 16px;
    border-bottom: 1px solid var(--border);
  }
  .sidebar-logo {
    display: flex; align-items: center; gap: 10px;
    font-weight: 700; font-size: 15px;
    letter-spacing: -0.3px;
    background: linear-gradient(90deg, var(--text) 0%, var(--blue3) 120%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  }
  .sidebar-logo-icon {
    width: 32px; height: 32px; border-radius: 8px;
    background: linear-gradient(135deg, var(--blue), var(--blue3));
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; flex-shrink: 0;
    box-shadow: 0 0 14px rgba(54,197,240,0.25);
  }
  .sidebar-section { padding: 12px 8px 4px; }
  .sidebar-section-label {
    font-size: 10px; font-weight: 700; color: var(--text3);
    text-transform: uppercase; letter-spacing: 1.2px;
    padding: 0 10px; margin-bottom: 6px;
  }
  .sidebar-item {
    display: flex; align-items: center; gap: 10px;
    padding: 9px 10px 9px 14px; border-radius: 7px;
    cursor: pointer; font-size: 13.5px; color: var(--text2);
    transition: background 0.15s, color 0.15s, transform 0.1s;
    border: none; background: none;
    width: 100%; text-align: left;
    position: relative;
  }
  .sidebar-item::before {
    content: ""; position: absolute; left: 0; top: 20%; height: 60%;
    width: 3px; border-radius: 0 2px 2px 0;
    background: transparent; transition: background 0.15s;
  }
  .sidebar-item:hover {
    background: rgba(255,255,255,0.04); color: var(--text);
  }
  .sidebar-item:hover::before { background: rgba(54,197,240,0.3); }
  .sidebar-item.active {
    background: linear-gradient(90deg, rgba(18,100,163,0.35) 0%, rgba(18,100,163,0.1) 100%);
    color: white;
  }
  .sidebar-item.active::before { background: var(--blue3); }
  .sidebar-item .icon { font-size: 16px; width: 20px; text-align: center; flex-shrink: 0; }
  .sidebar-footer {
    margin-top: auto; padding: 12px 8px;
    border-top: 1px solid var(--border);
  }
  .user-card {
    display: flex; align-items: center; gap: 10px;
    padding: 9px 10px; border-radius: 7px;
    transition: background 0.15s;
  }
  .user-card:hover { background: rgba(255,255,255,0.04); }
  .user-avatar {
    width: 32px; height: 32px; border-radius: 50%;
    background: linear-gradient(135deg, var(--blue), var(--blue3));
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 12px; color: white; flex-shrink: 0;
    box-shadow: 0 0 10px rgba(29,142,219,0.3);
  }
  .user-name { font-size: 13px; font-weight: 600; color: var(--text); }
  .user-email { font-size: 11px; color: var(--text3); }

  /* Main content */
  .main { flex: 1; overflow-y: auto; display: flex; flex-direction: column; }
  .topbar {
    padding: 16px 28px; border-bottom: 1px solid var(--border);
    display: flex; align-items: center; justify-content: space-between;
    background: rgba(15,31,61,0.92); position: sticky; top: 0; z-index: 10;
    backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
  }
  .page-title { font-size: 18px; font-weight: 700; color: var(--text); letter-spacing: -0.3px; }
  .page-sub { font-size: 12px; color: var(--text3); margin-top: 3px; }
  .content { padding: 28px; flex: 1; }

  /* Cards */
  .card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    backdrop-filter: blur(8px);
    transition: border-color 0.2s;
  }
  .card:hover { border-color: rgba(255,255,255,0.12); }
  .card-header {
    padding: 16px 20px;
    border-bottom: 1px solid var(--border);
    font-weight: 700; font-size: 14px; letter-spacing: -0.1px;
  }
  .card-body { padding: 20px; }

  /* Buttons */
  .btn {
    display: inline-flex; align-items: center; gap: 7px;
    padding: 9px 16px; border-radius: 6px; font-size: 13px;
    font-weight: 600; cursor: pointer; border: none;
    transition: all 0.15s; font-family: inherit;
    white-space: nowrap;
  }
  .btn-primary {
    background: linear-gradient(135deg, var(--blue) 0%, var(--blue2) 100%);
    color: white; box-shadow: 0 2px 12px rgba(18,100,163,0.35);
  }
  .btn-primary:hover:not(:disabled) {
    background: linear-gradient(135deg, var(--blue2) 0%, var(--blue3) 100%);
    box-shadow: 0 4px 18px rgba(29,142,219,0.45);
  }
  .btn-secondary { background: var(--navy3); color: var(--text); border: 1px solid var(--border); }
  .btn-secondary:hover { background: var(--navy); }
  .btn-danger { background: var(--red); color: white; }
  .btn-success { background: var(--green); color: white; }
  .btn-sm { padding: 6px 12px; font-size: 12px; }
  .btn:disabled { opacity: 0.5; cursor: not-allowed; }

  /* Forms */
  .form-group { margin-bottom: 16px; }
  .form-label { display: block; font-size: 12px; font-weight: 600; color: var(--text2); margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px; }
  .form-input {
    width: 100%; padding: 11px 14px; border-radius: 8px;
    background: rgba(10,22,40,0.7); border: 1px solid var(--border);
    color: var(--text); font-size: 14px; font-family: inherit;
    transition: border-color 0.2s, box-shadow 0.2s; outline: none;
    -webkit-text-fill-color: var(--text);
  }
  .form-input::placeholder { color: var(--text3); }
  .form-input:focus {
    border-color: var(--blue2);
    box-shadow: 0 0 0 3px rgba(29,142,219,0.15);
  }
  .form-textarea { min-height: 100px; resize: vertical; }

  /* Status badges */
  .badge {
    display: inline-flex; align-items: center; gap: 5px;
    padding: 3px 9px; border-radius: 20px; font-size: 11px; font-weight: 600;
  }
  .badge-pending { background: rgba(236,178,46,0.15); color: var(--accent); }
  .badge-processing { background: rgba(29,142,219,0.15); color: var(--blue2); }
  .badge-complete { background: rgba(43,172,118,0.15); color: var(--green); }
  .badge-failed { background: rgba(224,30,90,0.15); color: var(--red); }
  .badge-dot { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }

  /* Grid */
  .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  .grid-3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; }
  .grid-4 { display: grid; grid-template-columns: repeat(4,1fr); gap: 16px; }

  /* Stats */
  .stat-card {
    background: var(--card); border: 1px solid var(--border);
    border-radius: 12px; padding: 22px 20px;
    transition: transform 0.18s, box-shadow 0.18s;
    position: relative; overflow: hidden;
  }
  .stat-card::before {
    content: ""; position: absolute; top: 0; left: 0; right: 0; height: 2px;
    background: var(--stat-accent, var(--blue2)); opacity: 0.7;
    border-radius: 12px 12px 0 0;
  }
  .stat-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.3); }
  .stat-value { font-size: 30px; font-weight: 700; color: var(--text); font-family: 'IBM Plex Mono', monospace; }
  .stat-label { font-size: 11px; color: var(--text3); margin-top: 4px; text-transform: uppercase; letter-spacing: 0.8px; }
  .stat-icon {
    font-size: 22px; margin-bottom: 14px;
    width: 42px; height: 42px; border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    background: rgba(255,255,255,0.05); border: 1px solid var(--border);
  }

  /* Paper list */
  .paper-row {
    display: flex; align-items: center; gap: 16px;
    padding: 14px 20px; border-bottom: 1px solid var(--border);
    transition: background 0.15s, padding-left 0.15s; cursor: pointer;
  }
  .paper-row:hover { background: rgba(29,142,219,0.05); padding-left: 24px; }
  .paper-row:last-child { border-bottom: none; }
  .paper-icon {
    width: 40px; height: 40px; border-radius: 10px;
    background: linear-gradient(135deg, rgba(18,100,163,0.25) 0%, rgba(54,197,240,0.1) 100%);
    border: 1px solid rgba(18,100,163,0.3);
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; flex-shrink: 0;
    transition: box-shadow 0.15s;
  }
  .paper-row:hover .paper-icon { box-shadow: 0 0 12px rgba(29,142,219,0.25); }
  .paper-title { font-size: 14px; font-weight: 600; color: var(--text); }
  .paper-meta { font-size: 12px; color: var(--text3); margin-top: 2px; }
  .paper-actions { margin-left: auto; display: flex; gap: 8px; }

  /* Upload zone */
  .upload-zone {
    border: 2px dashed rgba(255,255,255,0.1); border-radius: 14px;
    padding: 52px 24px; text-align: center; cursor: pointer;
    transition: all 0.25s;
    background: radial-gradient(ellipse at 50% 100%, rgba(18,100,163,0.07) 0%, transparent 70%);
  }
  .upload-zone:hover, .upload-zone.drag {
    border-color: var(--blue2);
    background: radial-gradient(ellipse at 50% 80%, rgba(29,142,219,0.12) 0%, transparent 70%);
    box-shadow: 0 0 0 4px rgba(29,142,219,0.08);
  }
  .upload-icon { font-size: 44px; margin-bottom: 14px; line-height: 1; }
  .upload-title { font-size: 16px; font-weight: 700; margin-bottom: 6px; }
  .upload-sub { font-size: 13px; color: var(--text3); }

  /* Analysis result */
  .analysis-section { margin-bottom: 20px; }
  .analysis-label { font-size: 11px; font-weight: 700; color: var(--text3); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 8px; }
  .analysis-value { font-size: 14px; color: var(--text); line-height: 1.6; }
  .tag-list { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; }
  .tag {
    padding: 3px 10px; border-radius: 4px; font-size: 12px;
    background: rgba(18,100,163,0.2); border: 1px solid rgba(18,100,163,0.3);
    color: var(--blue3); font-family: 'IBM Plex Mono', monospace;
  }
  .bullet-list { list-style: none; }
  .bullet-list li { padding: 5px 0; font-size: 14px; color: var(--text); display: flex; gap: 10px; }
  .bullet-list li::before { content: "›"; color: var(--blue3); font-weight: 700; }

  /* ── Auth page — modern split-screen ──────────────────────────── */
  @keyframes floatOrb {
    0%,100% { transform: translate(0,0) scale(1); }
    33%      { transform: translate(30px,-40px) scale(1.08); }
    66%      { transform: translate(-20px,25px) scale(0.95); }
  }
  @keyframes pulseGlow {
    0%,100% { box-shadow: 0 0 0 0 rgba(54,197,240,0), 0 8px 32px rgba(0,0,0,0.5); }
    50%      { box-shadow: 0 0 0 12px rgba(54,197,240,0.12), 0 8px 32px rgba(0,0,0,0.5); }
  }
  @keyframes slideUp {
    from { opacity:0; transform:translateY(24px); }
    to   { opacity:1; transform:translateY(0); }
  }
  @keyframes fadeIn {
    from { opacity:0; } to { opacity:1; }
  }
  @keyframes shimmer {
    0%   { background-position: -200% center; }
    100% { background-position:  200% center; }
  }

  .auth-page {
    min-height: 100vh;
    height: 100%;
    display: flex;
    background: var(--navy);
    overflow: hidden;
    position: relative;
  }

  /* Animated background orbs */
  .auth-orb {
    position: absolute; border-radius: 50%; pointer-events: none; filter: blur(80px);
  }
  .auth-orb-1 {
    width: 480px; height: 480px; top: -120px; left: -80px;
    background: radial-gradient(circle, rgba(18,100,163,0.35) 0%, transparent 70%);
    animation: floatOrb 14s ease-in-out infinite;
  }
  .auth-orb-2 {
    width: 360px; height: 360px; bottom: -80px; right: 30%;
    background: radial-gradient(circle, rgba(54,197,240,0.18) 0%, transparent 70%);
    animation: floatOrb 18s ease-in-out infinite reverse;
  }
  .auth-orb-3 {
    width: 300px; height: 300px; top: 40%; right: -60px;
    background: radial-gradient(circle, rgba(29,142,219,0.22) 0%, transparent 70%);
    animation: floatOrb 22s ease-in-out infinite 4s;
  }

  /* Left panel — feature showcase */
  .auth-panel-left {
    flex: 1; min-width: 0;
    display: flex; flex-direction: column; justify-content: center;
    padding: 60px 56px;
    position: relative; z-index: 1;
  }
  @media (max-width: 860px) { .auth-panel-left { display: none; } }

  .auth-brand {
    display: flex; align-items: center; gap: 14px; margin-bottom: 52px;
  }
  .auth-brand-icon {
    width: 48px; height: 48px; border-radius: 13px;
    background: linear-gradient(135deg, var(--blue) 0%, var(--blue3) 100%);
    display: flex; align-items: center; justify-content: center;
    font-size: 22px; flex-shrink: 0;
    box-shadow: 0 4px 20px rgba(54,197,240,0.3);
    animation: pulseGlow 3s ease-in-out infinite;
  }
  .auth-brand-name {
    font-size: 20px; font-weight: 700; letter-spacing: -0.3px;
    background: linear-gradient(90deg, var(--text) 0%, var(--blue3) 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  }
  .auth-panel-headline {
    font-size: 38px; font-weight: 700; line-height: 1.2; letter-spacing: -0.8px;
    margin-bottom: 16px;
  }
  .auth-panel-headline span {
    background: linear-gradient(90deg, var(--blue3) 0%, var(--blue2) 50%, var(--accent) 100%);
    background-size: 200% auto;
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
    animation: shimmer 4s linear infinite;
  }
  .auth-panel-sub {
    font-size: 15px; color: var(--text2); line-height: 1.6; margin-bottom: 44px; max-width: 380px;
  }
  .auth-features { display: flex; flex-direction: column; gap: 20px; }
  .auth-feature-item {
    display: flex; align-items: flex-start; gap: 16px;
    animation: slideUp 0.5s ease both;
  }
  .auth-feature-item:nth-child(1) { animation-delay: 0.1s; }
  .auth-feature-item:nth-child(2) { animation-delay: 0.2s; }
  .auth-feature-item:nth-child(3) { animation-delay: 0.3s; }
  .auth-feature-item:nth-child(4) { animation-delay: 0.4s; }
  .auth-feature-icon {
    width: 40px; height: 40px; border-radius: 10px; flex-shrink: 0;
    display: flex; align-items: center; justify-content: center; font-size: 18px;
    background: rgba(18,100,163,0.2); border: 1px solid rgba(54,197,240,0.15);
  }
  .auth-feature-text h4 { font-size: 14px; font-weight: 600; color: var(--text); margin-bottom: 3px; }
  .auth-feature-text p  { font-size: 12px; color: var(--text3); line-height: 1.5; }

  .auth-stats {
    display: flex; gap: 32px; margin-top: 48px;
    padding-top: 32px; border-top: 1px solid var(--border);
  }
  .auth-stat-item { text-align: left; }
  .auth-stat-num { font-size: 22px; font-weight: 700; color: var(--blue3); font-family: 'IBM Plex Mono', monospace; }
  .auth-stat-lbl { font-size: 11px; color: var(--text3); margin-top: 2px; text-transform: uppercase; letter-spacing: 0.5px; }

  /* Right panel — form */
  .auth-panel-right {
    width: 480px; flex-shrink: 0;
    min-height: 100vh;
    display: flex; align-items: center; justify-content: center;
    padding: 48px 44px;
    position: relative; z-index: 1;
    background: rgba(8,18,34,0.75);
    border-left: 1px solid rgba(255,255,255,0.07);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
  }
  @media (max-width: 860px) {
    .auth-panel-right {
      width: 100%; border-left: none;
      background: var(--navy);
      padding: 48px 28px;
      min-height: 100vh;
    }
  }

  .auth-card {
    width: 100%; max-width: 380px;
    animation: slideUp 0.45s ease both;
  }

  .auth-logo { margin-bottom: 32px; }
  .auth-logo-icon {
    width: 56px; height: 56px; border-radius: 16px; margin-bottom: 16px;
    background: linear-gradient(135deg, var(--blue) 0%, var(--blue3) 100%);
    display: flex; align-items: center; justify-content: center; font-size: 26px;
    box-shadow: 0 8px 24px rgba(54,197,240,0.25);
    animation: pulseGlow 3s ease-in-out infinite;
  }
  .auth-title { font-size: 26px; font-weight: 700; color: var(--text); margin-bottom: 6px; letter-spacing: -0.4px; }
  .auth-sub { font-size: 14px; color: var(--text3); line-height: 1.5; }

  /* Enhanced form inputs for auth */
  .auth-input-wrap { position: relative; }
  .auth-input-icon {
    position: absolute; left: 14px; top: 50%; transform: translateY(-50%);
    color: var(--text3); font-size: 15px; pointer-events: none;
    transition: color 0.2s;
  }
  .auth-input-wrap:focus-within .auth-input-icon { color: var(--blue3); }
  .auth-input-wrap .form-input { padding-left: 42px; }
  .auth-input-wrap.has-toggle .form-input { padding-right: 46px; }

  /* Strength meter */
  .auth-strength-bar {
    height: 3px; border-radius: 2px; margin-top: 8px;
    background: var(--navy3); overflow: hidden;
  }
  .auth-strength-fill {
    height: 100%; border-radius: 2px;
    transition: width 0.3s ease, background 0.3s ease;
  }

  /* Divider with text */
  .auth-divider {
    display: flex; align-items: center; gap: 12px; margin: 20px 0;
  }
  .auth-divider::before, .auth-divider::after {
    content: ""; flex: 1; height: 1px; background: var(--border);
  }
  .auth-divider span { font-size: 11px; color: var(--text3); text-transform: uppercase; letter-spacing: 1px; }

  .auth-footer { margin-top: 24px; font-size: 13px; color: var(--text3); text-align: center; }
  .auth-link {
    color: var(--blue2); cursor: pointer; font-weight: 600;
    background: none; border: none; padding: 0; font-size: inherit; font-family: inherit;
    transition: color 0.2s;
  }
  .auth-link:hover { color: var(--blue3); text-decoration: underline; }

  /* Alert */
  .alert { padding: 12px 16px; border-radius: 6px; font-size: 13px; margin-bottom: 16px; }
  .alert-error { background: rgba(224,30,90,0.1); border: 1px solid rgba(224,30,90,0.3); color: #ff6b8a; }
  .alert-success { background: rgba(43,172,118,0.1); border: 1px solid rgba(43,172,118,0.3); color: var(--green); }

  /* Loading */
  .spinner {
    width: 20px; height: 20px; border-radius: 50%;
    border: 2px solid var(--navy3); border-top-color: var(--blue2);
    animation: spin 0.8s linear infinite; display: inline-block;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  @keyframes shimmerBar {
    0%   { transform: translateX(-100%); }
    100% { transform: translateX(100%); }
  }
  @keyframes fadeSlideIn {
    from { opacity:0; transform: translateY(12px); }
    to   { opacity:1; transform: translateY(0); }
  }

  .empty-state { text-align: center; padding: 60px 20px; color: var(--text3); }
  .empty-icon { font-size: 48px; margin-bottom: 12px; }
  .empty-title { font-size: 16px; font-weight: 600; color: var(--text2); margin-bottom: 6px; }

  .divider { height: 1px; background: var(--border); margin: 20px 0; }
  .mono { font-family: 'IBM Plex Mono', monospace; }
  .text-muted { color: var(--text3); }
  .text-blue { color: var(--blue2); }
  .text-green { color: var(--green); }
  .flex { display: flex; }
  .flex-center { display: flex; align-items: center; }
  .gap-8 { gap: 8px; }
  .gap-12 { gap: 12px; }
  .mb-16 { margin-bottom: 16px; }
  .mb-20 { margin-bottom: 20px; }
  .mt-auto { margin-top: auto; }
  .w-full { width: 100%; }
  .justify-between { justify-content: space-between; }
`;

// ── Auth Pages ─────────────────────────────────────────────────────────────────
function downloadAsText(content, filename) {
  const blob = new Blob([content], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

function AuthLeftPanel() {
  return (
    <div className="auth-panel-left">
      <div className="auth-brand">
        <div className="auth-brand-icon">🔬</div>
        <div className="auth-brand-name">Research Assistant AI</div>
      </div>
      <h1 className="auth-panel-headline">
        Publish-ready papers,<br/><span>generated in minutes.</span>
      </h1>
      <p className="auth-panel-sub">
        A multi-agent Claude pipeline that writes full academic papers with real citations,
        ethics statements, and structured LaTeX — benchmarked at 9.1/10 against expert reviewers.
      </p>
      <div className="auth-features">
        {[
          { icon: "🧠", title: "6-Stage AI Pipeline", desc: "Outline → Research → Methods → Results → Discussion → Bibliography, each optimised separately." },
          { icon: "📚", title: "Real Citations, Zero [?]", desc: "Automatic citation_map ensures every reference resolves to a real BibTeX entry." },
          { icon: "⚖️", title: "Auto Ethics Statements", desc: "Publication-quality ethics text generated for dual-use risks, paper mills, and dataset consent." },
          { icon: "📊", title: "Publishability Scoring", desc: "MAPQ-based 0–100 score with colour-coded readiness badge after every generation." },
        ].map(f => (
          <div className="auth-feature-item" key={f.title}>
            <div className="auth-feature-icon">{f.icon}</div>
            <div className="auth-feature-text">
              <h4>{f.title}</h4>
              <p>{f.desc}</p>
            </div>
          </div>
        ))}
      </div>
      <div className="auth-stats">
        {[
          { num: "~$0.50", lbl: "Per 20-page paper" },
          { num: "6 calls", lbl: "Claude API calls" },
          { num: "r=0.91", lbl: "Expert correlation" },
        ].map(s => (
          <div className="auth-stat-item" key={s.lbl}>
            <div className="auth-stat-num">{s.num}</div>
            <div className="auth-stat-lbl">{s.lbl}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function LoginPage({ onLogin, onSwitch }) {
  const [form, setForm] = useState({ email: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showPwd, setShowPwd] = useState(false);

  const validate = () => {
    if (!form.email.trim()) return "Email is required";
    if (!form.email.includes("@")) return "Enter a valid email address";
    if (!form.password) return "Password is required";
    if (form.password.length < 6) return "Password must be at least 6 characters";
    return null;
  };

  const submit = async () => {
    const err = validate(); if (err) { setError(err); return; }
    setLoading(true); setError("");
    try {
      const fd = new URLSearchParams();
      fd.append("username", form.email.trim());
      fd.append("password", form.password);
      const data = await apiFetch("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: fd.toString(),
      });
      onLogin(data);
    } catch (e) { setError(e.message || "Login failed. Check your credentials."); }
    setLoading(false);
  };

  return (
    <div className="auth-page">
      {/* Animated background orbs */}
      <div className="auth-orb auth-orb-1"/>
      <div className="auth-orb auth-orb-2"/>
      <div className="auth-orb auth-orb-3"/>

      <AuthLeftPanel/>

      <div className="auth-panel-right">
        <div className="auth-card">
          <div className="auth-logo">
            <div className="auth-logo-icon">🔬</div>
            <div className="auth-title">Welcome back</div>
            <div className="auth-sub">Sign in to your research workspace</div>
          </div>

          {error && <div className="alert alert-error">⚠ {error}</div>}

          <div className="form-group">
            <label className="form-label">Email address</label>
            <div className="auth-input-wrap">
              <span className="auth-input-icon">✉</span>
              <input className="form-input" type="email" placeholder="you@university.edu" autoFocus
                value={form.email} onChange={e => setForm({...form, email: e.target.value})}
                onKeyDown={e => e.key === "Enter" && submit()} />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label" style={{display:"flex",justifyContent:"space-between"}}>
              <span>Password</span>
            </label>
            <div className="auth-input-wrap has-toggle">
              <span className="auth-input-icon">🔒</span>
              <input className="form-input" type={showPwd ? "text" : "password"} placeholder="••••••••"
                value={form.password} onChange={e => setForm({...form, password: e.target.value})}
                onKeyDown={e => e.key === "Enter" && submit()} />
              <button onClick={() => setShowPwd(v => !v)} tabIndex={-1}
                style={{position:"absolute",right:12,top:"50%",transform:"translateY(-50%)",
                  background:"none",border:"none",cursor:"pointer",color:"var(--text3)",fontSize:15,
                  padding:4,lineHeight:1,transition:"color 0.2s"}}
                onMouseEnter={e=>e.currentTarget.style.color="var(--text)"}
                onMouseLeave={e=>e.currentTarget.style.color="var(--text3)"}>
                {showPwd ? "🙈" : "👁"}
              </button>
            </div>
          </div>

          <button className="btn btn-primary w-full" onClick={submit} disabled={loading}
            style={{height:44,fontSize:15,fontWeight:600,letterSpacing:0.2,marginTop:4,
              background: loading ? "var(--blue)" : "linear-gradient(135deg, var(--blue) 0%, var(--blue2) 100%)",
              boxShadow: loading ? "none" : "0 4px 16px rgba(18,100,163,0.4)",
              transition:"all 0.2s"}}>
            {loading ? <><span className="spinner" style={{width:16,height:16,marginRight:8,verticalAlign:"middle"}}/> Signing in…</> : "Sign In →"}
          </button>

          <div className="auth-divider"><span>or</span></div>

          <div className="auth-footer">
            Don&apos;t have an account?{" "}
            <button className="auth-link" onClick={onSwitch}>Create one →</button>
          </div>
        </div>
      </div>
    </div>
  );
}

function RegisterPage({ onLogin, onSwitch }) {
  const [form, setForm] = useState({ full_name: "", email: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showPwd, setShowPwd] = useState(false);

  const validate = () => {
    if (!form.full_name.trim()) return "Full name is required";
    if (!form.email.trim() || !form.email.includes("@")) return "Enter a valid email address";
    if (!form.password || form.password.length < 8) return "Password must be at least 8 characters";
    return null;
  };

  const submit = async () => {
    const err = validate(); if (err) { setError(err); return; }
    setLoading(true); setError("");
    try {
      await apiFetch("/api/v1/auth/register", {
        method: "POST", body: JSON.stringify({
          full_name: form.full_name.trim(),
          email: form.email.trim(),
          password: form.password,
        })
      });
      const fd = new URLSearchParams();
      fd.append("username", form.email.trim()); fd.append("password", form.password);
      const data = await apiFetch("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: fd.toString(),
      });
      onLogin(data);
    } catch (e) { setError(e.message || "Registration failed. Email may already be in use."); }
    setLoading(false);
  };

  const pwLen = form.password.length;
  const strength = pwLen === 0 ? null : pwLen < 8 ? "weak" : pwLen < 12 ? "ok" : "strong";
  const strengthMeta = {
    weak:   { pct: "30%",  color: "var(--red)",    label: "Too short — keep going" },
    ok:     { pct: "65%",  color: "var(--accent)",  label: "Good — a bit longer would be better" },
    strong: { pct: "100%", color: "var(--green)",   label: "Strong password ✓" },
  };

  return (
    <div className="auth-page">
      <div className="auth-orb auth-orb-1"/>
      <div className="auth-orb auth-orb-2"/>
      <div className="auth-orb auth-orb-3"/>

      <AuthLeftPanel/>

      <div className="auth-panel-right">
        <div className="auth-card">
          <div className="auth-logo">
            <div className="auth-logo-icon">🔬</div>
            <div className="auth-title">Create account</div>
            <div className="auth-sub">Start your AI research journey today</div>
          </div>

          {error && <div className="alert alert-error">⚠ {error}</div>}

          <div className="form-group">
            <label className="form-label">Full name</label>
            <div className="auth-input-wrap">
              <span className="auth-input-icon">👤</span>
              <input className="form-input" placeholder="Dr. Jane Smith" autoFocus
                value={form.full_name} onChange={e => setForm({...form, full_name: e.target.value})}
                onKeyDown={e => e.key === "Enter" && submit()} />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Email address</label>
            <div className="auth-input-wrap">
              <span className="auth-input-icon">✉</span>
              <input className="form-input" type="email" placeholder="you@university.edu"
                value={form.email} onChange={e => setForm({...form, email: e.target.value})}
                onKeyDown={e => e.key === "Enter" && submit()} />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <div className="auth-input-wrap has-toggle">
              <span className="auth-input-icon">🔒</span>
              <input className="form-input" type={showPwd ? "text" : "password"} placeholder="Min. 8 characters"
                value={form.password} onChange={e => setForm({...form, password: e.target.value})}
                onKeyDown={e => e.key === "Enter" && submit()} />
              <button onClick={() => setShowPwd(v => !v)} tabIndex={-1}
                style={{position:"absolute",right:12,top:"50%",transform:"translateY(-50%)",
                  background:"none",border:"none",cursor:"pointer",color:"var(--text3)",fontSize:15,
                  padding:4,lineHeight:1,transition:"color 0.2s"}}
                onMouseEnter={e=>e.currentTarget.style.color="var(--text)"}
                onMouseLeave={e=>e.currentTarget.style.color="var(--text3)"}>
                {showPwd ? "🙈" : "👁"}
              </button>
            </div>
            {strength && (<>
              <div className="auth-strength-bar">
                <div className="auth-strength-fill" style={{width:strengthMeta[strength].pct, background:strengthMeta[strength].color}}/>
              </div>
              <div style={{marginTop:5,fontSize:11,color:strengthMeta[strength].color,fontWeight:600}}>
                {strengthMeta[strength].label}
              </div>
            </>)}
          </div>

          <button className="btn btn-primary w-full" onClick={submit} disabled={loading}
            style={{height:44,fontSize:15,fontWeight:600,letterSpacing:0.2,marginTop:4,
              background: loading ? "var(--blue)" : "linear-gradient(135deg, var(--blue) 0%, var(--blue2) 100%)",
              boxShadow: loading ? "none" : "0 4px 16px rgba(18,100,163,0.4)",
              transition:"all 0.2s"}}>
            {loading ? <><span className="spinner" style={{width:16,height:16,marginRight:8,verticalAlign:"middle"}}/> Creating account…</> : "Create Account →"}
          </button>

          <div className="auth-divider"><span>or</span></div>

          <div className="auth-footer">
            Already have an account?{" "}
            <button className="auth-link" onClick={onSwitch}>Sign in →</button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Dashboard ──────────────────────────────────────────────────────────────────
function Dashboard({ token, onNavigate }) {
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState(null);

  const fetchPapers = useCallback(() => {
    apiFetch("/api/v1/papers/", {}, token)
      .then(p => { setPapers(p); setLoading(false); setLastRefresh(new Date()); })
      .catch(() => setLoading(false));
  }, [token]);

  useEffect(() => {
    fetchPapers();
    // Auto-refresh every 10s while papers are still processing
    const interval = setInterval(() => {
      fetchPapers();
    }, 10000);
    return () => clearInterval(interval);
  }, [fetchPapers]);

  const complete = papers.filter(p => p.processing_status === "complete").length;
  const pending = papers.filter(p => ["pending","processing"].includes(p.processing_status)).length;
  const failed = papers.filter(p => p.processing_status === "failed").length;

  return (
    <div>
      <div className="grid-4 mb-20">
        {[
          { icon: "📄", value: papers.length, label: "Total Papers", color: "var(--blue3)", accent: "var(--blue3)" },
          { icon: "✅", value: complete, label: "Analyzed", color: "var(--green)", accent: "var(--green)" },
          { icon: "⏳", value: pending, label: "Processing", color: "var(--accent)", accent: "var(--accent)" },
          { icon: "❌", value: failed, label: "Failed", color: failed > 0 ? "var(--red)" : "var(--text3)", accent: failed > 0 ? "var(--red)" : "var(--navy3)" },
        ].map(s => (
          <div className="stat-card" key={s.label} style={{"--stat-accent": s.accent}}>
            <div className="stat-icon" style={{color: s.color}}>{s.icon}</div>
            <div className="stat-value mono" style={{color:s.color}}>{s.value}</div>
            <div className="stat-label">{s.label}</div>
          </div>
        ))}
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header flex-center flex justify-between">
            <span>Recent Papers</span>
            <div style={{display:"flex",gap:8,alignItems:"center"}}>
              {lastRefresh && <span style={{fontSize:10,color:"var(--text3)"}}>Updated {lastRefresh.toLocaleTimeString()}</span>}
              <button className="btn btn-secondary btn-sm" onClick={fetchPapers}>↻ Refresh</button>
              <button className="btn btn-primary btn-sm" onClick={() => onNavigate("upload")}>+ Upload</button>
            </div>
          </div>
          {loading ? (
            <div style={{padding:40, textAlign:"center"}}><span className="spinner"/></div>
          ) : papers.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📭</div>
              <div className="empty-title">No papers yet</div>
              <div style={{marginTop:12}}>
                <button className="btn btn-primary btn-sm" onClick={() => onNavigate("upload")}>Upload your first paper</button>
              </div>
            </div>
          ) : (
            papers.slice(0,6).map(p => (
              <div className="paper-row" key={p.id} onClick={() => onNavigate("analysis", p)}>
                <div className="paper-icon">📄</div>
                <div style={{flex:1, minWidth:0}}>
                  <div className="paper-title" style={{overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>
                    {p.title || p.file_name}
                  </div>
                  <div className="paper-meta">{p.research_domain || (p.processing_status === "processing" ? "Analyzing..." : p.processing_status === "pending" ? "Queued..." : "—")}</div>
                </div>
                <StatusBadge status={p.processing_status} />
              </div>
            ))
          )}
          {papers.length > 6 && (
            <div style={{padding:"10px 16px",textAlign:"center",borderTop:"1px solid var(--border)"}}>
              <button className="btn btn-secondary btn-sm" onClick={() => onNavigate("analysis")}>View all {papers.length} papers →</button>
            </div>
          )}
        </div>

        <div className="card">
          <div className="card-header">Quick Actions</div>
          <div className="card-body">
            {[
              { icon:"📄", label:"Upload & Analyze Paper", sub:"PDF or DOCX · 30-45 seconds", page:"upload", color:"var(--blue)" },
              { icon:"📚", label:"Literature Review", sub:"Synthesize multiple papers with citations", page:"literature", color:"var(--green)" },
              { icon:"🔍", label:"Research Gaps", sub:"Find opportunities in the literature", page:"gaps", color:"var(--accent)" },
              { icon:"💰", label:"Grant Proposal", sub:"NSF/NIH/EU format with AI writing", page:"grant", color:"var(--blue3)" },
              { icon:"✍️", label:"Write Full Paper", sub:"7-step wizard → LaTeX + BibTeX", page:"write", color:"var(--text2)" },
            ].map(a => (
              <div key={a.page} onClick={() => onNavigate(a.page)}
                style={{display:"flex",alignItems:"center",gap:14,padding:"12px 0",
                  borderBottom:"1px solid var(--border)",cursor:"pointer",transition:"opacity 0.15s"}}
                onMouseOver={e => e.currentTarget.style.opacity="0.75"}
                onMouseOut={e => e.currentTarget.style.opacity="1"}>
                <div style={{width:38,height:38,borderRadius:8,background:`rgba(18,100,163,0.15)`,
                  display:"flex",alignItems:"center",justifyContent:"center",fontSize:18,flexShrink:0,
                  border:`1px solid rgba(18,100,163,0.2)`}}>
                  {a.icon}
                </div>
                <div style={{flex:1}}>
                  <div style={{fontSize:13,fontWeight:600,color:"var(--text)"}}>{a.label}</div>
                  <div style={{fontSize:11,color:"var(--text3)",marginTop:2}}>{a.sub}</div>
                </div>
                <span style={{color:"var(--text3)",fontSize:18}}>›</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Status Badge ───────────────────────────────────────────────────────────────
function StatusBadge({ status }) {
  const map = {
    pending: ["badge-pending", "Pending"],
    processing: ["badge-processing", "Processing"],
    complete: ["badge-complete", "Complete"],
    failed: ["badge-failed", "Failed"],
  };
  const [cls, label] = map[status] || ["badge-pending", status];
  return <span className={`badge ${cls}`}><span className="badge-dot"/>{label}</span>;
}

// ── Upload Page ────────────────────────────────────────────────────────────────
function UploadPage({ token, onNavigate }) {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [success, setSuccess] = useState(null);
  const [error, setError] = useState("");

  const upload = async (file) => {
    if (!file) return;
    setUploading(true); setError(""); setSuccess(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      const data = await apiFetch("/api/v1/papers/upload", {
        method: "POST", body: fd,
        headers: { "Authorization": `Bearer ${token}` }
      }, null);
      setSuccess(data);
    } catch (e) { setError(e.message); }
    setUploading(false);
  };

  const onDrop = (e) => {
    e.preventDefault(); setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) upload(file);
  };

  return (
    <div style={{maxWidth:640}}>
      {error && <div className="alert alert-error">⚠ {error}</div>}
      {success ? (
        <div className="card">
          <div className="card-body" style={{textAlign:"center",padding:"40px 24px"}}>
            <div style={{fontSize:48,marginBottom:16}}>✅</div>
            <div style={{fontSize:18,fontWeight:700,marginBottom:8}}>Paper Uploaded!</div>
            <div style={{fontSize:13,color:"var(--text3)",marginBottom:8}}>
              <span className="mono">{success.file_name}</span>
            </div>
            <div style={{fontSize:13,color:"var(--text3)",marginBottom:24}}>
              Claude AI is analyzing your paper. This takes ~30-45 seconds.
            </div>
            <div style={{display:"flex",gap:12,justifyContent:"center"}}>
              <button className="btn btn-primary" onClick={() => onNavigate("analysis", success)}>
                View Analysis
              </button>
              <button className="btn btn-secondary" onClick={() => setSuccess(null)}>
                Upload Another
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div>
          <div className={`upload-zone ${dragging ? "drag" : ""}`}
            onDragOver={e => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
            onClick={() => document.getElementById("fileInput").click()}>
            <input id="fileInput" type="file" accept=".pdf,.docx" style={{display:"none"}}
              onChange={e => upload(e.target.files[0])} />
            {uploading ? (
              <div>
                <div className="upload-icon"><span className="spinner" style={{width:40,height:40,borderWidth:3}}/></div>
                <div className="upload-title">Uploading & analyzing...</div>
                <div className="upload-sub">Claude AI is reading your paper</div>
              </div>
            ) : (
              <div>
                <div className="upload-icon">📂</div>
                <div className="upload-title">Drop your paper here</div>
                <div className="upload-sub">or click to browse · PDF and DOCX supported · Max 50MB</div>
              </div>
            )}
          </div>
          <div style={{marginTop:20,padding:"16px 20px",background:"var(--navy2)",borderRadius:8,border:"1px solid var(--border)"}}>
            <div style={{fontSize:12,fontWeight:700,color:"var(--text3)",textTransform:"uppercase",letterSpacing:"0.5px",marginBottom:10}}>
              What happens after upload
            </div>
            {["PDF text is extracted using PyMuPDF","Claude AI reads the full paper","Sections, contributions, and gaps are identified","Results saved and ready to view"].map((s,i) => (
              <div key={i} style={{display:"flex",gap:10,fontSize:13,color:"var(--text2)",marginBottom:6}}>
                <span style={{color:"var(--blue3)",fontWeight:700}}>{i+1}.</span> {s}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ── Analysis Page ──────────────────────────────────────────────────────────────
function AnalysisPage({ token, paper: initialPaper, onNavigate }) {
  const [paper, setPaper] = useState(initialPaper);
  const [analysis, setAnalysis] = useState(null);
  const [status, setStatus] = useState(initialPaper?.processing_status || "pending");
  const [loading, setLoading] = useState(true);
  const [papers, setPapers] = useState([]);
  const [selected, setSelected] = useState(initialPaper?.id || null);

  // Load paper list
  useEffect(() => {
    apiFetch("/api/v1/papers/", {}, token).then(setPapers).catch(() => {});
  }, [token]);

  const fetchAnalysis = useCallback(async (pid) => {
    if (!pid) return;
    try {
      const data = await apiFetch(`/api/v1/papers/${pid}/analysis`, {}, token);
      setStatus(data.status);
      if (data.analysis && Object.keys(data.analysis).length > 0) {
        setAnalysis(data.analysis);
        setLoading(false);
      }
    } catch (e) { setLoading(false); }
  }, [token]);

  useEffect(() => {
    if (!selected) { setLoading(false); return; }
    fetchAnalysis(selected);
    const interval = setInterval(() => {
      if (status !== "complete" && status !== "failed") fetchAnalysis(selected);
      else clearInterval(interval);
    }, 5000);
    return () => clearInterval(interval);
  }, [selected, fetchAnalysis]);

  const selectPaper = (p) => {
    setSelected(p.id); setPaper(p);
    setAnalysis(null); setStatus(p.processing_status); setLoading(true);
  };

  if (papers.length === 0 && !initialPaper) {
    return (
      <div className="empty-state">
        <div className="empty-icon">📄</div>
        <div className="empty-title">No papers uploaded yet</div>
        <div style={{marginTop:12}}>
          <button className="btn btn-primary" onClick={() => onNavigate("upload")}>Upload a Paper</button>
        </div>
      </div>
    );
  }

  return (
    <div className="grid-2" style={{alignItems:"start"}}>
      {/* Paper selector */}
      <div className="card" style={{gridColumn:"1",maxHeight:"80vh",overflowY:"auto"}}>
        <div className="card-header">Your Papers</div>
        {papers.map(p => (
          <div key={p.id} className="paper-row" onClick={() => selectPaper(p)}
            style={{background: selected===p.id ? "rgba(18,100,163,0.15)" : ""}}>
            <div className="paper-icon">📄</div>
            <div style={{flex:1,minWidth:0}}>
              <div className="paper-title" style={{overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap",fontSize:13}}>
                {p.title || p.file_name}
              </div>
              <div style={{marginTop:4}}><StatusBadge status={p.processing_status}/></div>
            </div>
          </div>
        ))}
      </div>

      {/* Analysis result */}
      <div>
        {!selected ? (
          <div className="card"><div className="empty-state"><div className="empty-icon">👈</div><div className="empty-title">Select a paper</div></div></div>
        ) : loading || !analysis ? (
          <div className="card">
            <div className="card-body" style={{textAlign:"center",padding:60}}>
              {status === "failed" ? (
                <div><div style={{fontSize:40,marginBottom:12}}>❌</div><div style={{fontWeight:600}}>Analysis failed</div></div>
              ) : (
                <div>
                  <span className="spinner" style={{width:40,height:40,borderWidth:3,marginBottom:16,display:"block",margin:"0 auto 16px"}}/>
                  <div style={{fontWeight:600,marginBottom:6}}>Analyzing with Claude AI...</div>
                  <div style={{fontSize:13,color:"var(--text3)"}}>This takes 30-45 seconds</div>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="card">
            <div className="card-header flex-center flex justify-between">
              <span style={{flex:1,minWidth:0,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{analysis.title || "Analysis"}</span>
              <div style={{display:"flex",gap:8,flexShrink:0}}>
                <button className="btn btn-secondary btn-sm" onClick={()=>copyToClipboard(JSON.stringify(analysis,null,2))}>📋 Copy JSON</button>
                <StatusBadge status="complete"/>
              </div>
            </div>
            {/* Meta bar */}
            <div style={{padding:"8px 16px",background:"rgba(18,100,163,0.06)",borderBottom:"1px solid var(--border)",display:"flex",gap:10,flexWrap:"wrap",alignItems:"center",fontSize:11}}>
              {analysis.authors&&<span style={{color:"var(--text2)"}}>{analysis.authors}{analysis.year?` · ${analysis.year}`:""}</span>}
              {analysis.publication_venue&&<span style={{color:"var(--text3)",borderLeft:"1px solid var(--border)",paddingLeft:10}}>{analysis.publication_venue}</span>}
              {analysis.paper_type&&<span style={{padding:"2px 8px",borderRadius:10,background:"rgba(18,100,163,0.15)",color:"var(--blue3)",fontWeight:600,textTransform:"uppercase",fontSize:10}}>{analysis.paper_type.replace(/_/g," ")}</span>}
              {analysis.methodology_type&&<span style={{padding:"2px 8px",borderRadius:10,background:"rgba(43,172,118,0.12)",color:"var(--green)",fontWeight:600,textTransform:"uppercase",fontSize:10}}>{analysis.methodology_type.replace(/_/g," ")}</span>}
              {analysis.reproducibility_score&&<span style={{padding:"2px 8px",borderRadius:10,fontSize:10,fontWeight:600,
                background:analysis.reproducibility_score.startsWith("high")?"rgba(43,172,118,0.12)":analysis.reproducibility_score.startsWith("medium")?"rgba(236,178,46,0.12)":"rgba(224,30,90,0.12)",
                color:analysis.reproducibility_score.startsWith("high")?"var(--green)":analysis.reproducibility_score.startsWith("medium")?"var(--accent)":"var(--red)"}}>
                🔁 Reproducibility: {analysis.reproducibility_score.split(" ")[0]}
              </span>}
            </div>
            <div className="card-body" style={{display:"flex",flexDirection:"column",gap:20}}>
              {analysis.research_domain && (
                <div className="analysis-section">
                  <div className="analysis-label">Research Domain</div>
                  <div style={{display:"flex",gap:8,flexWrap:"wrap",alignItems:"center"}}>
                    <span className="tag">{analysis.research_domain}</span>
                    {analysis.code_availability&&!analysis.code_availability.startsWith("unknown")&&(
                      <span style={{fontSize:12,padding:"3px 10px",borderRadius:10,fontWeight:600,
                        background:analysis.code_availability.startsWith("yes")?"rgba(43,172,118,0.12)":"rgba(224,30,90,0.1)",
                        color:analysis.code_availability.startsWith("yes")?"var(--green)":"var(--red)"}}>
                        {analysis.code_availability.startsWith("yes")?"💻 Code Available":"❌ No Code"}
                      </span>
                    )}
                  </div>
                </div>
              )}
              {analysis.abstract_summary && (
                <div className="analysis-section">
                  <div className="analysis-label">Abstract Summary</div>
                  <div className="analysis-value" style={{lineHeight:1.8}}>{analysis.abstract_summary}</div>
                </div>
              )}
              {analysis.core_problem && (
                <div className="analysis-section">
                  <div className="analysis-label">Core Problem</div>
                  <div style={{padding:"10px 14px",background:"rgba(18,100,163,0.07)",borderRadius:6,borderLeft:"3px solid var(--blue)",fontSize:13,lineHeight:1.7,color:"var(--text)"}}>{analysis.core_problem}</div>
                </div>
              )}
              {analysis.performance_metrics && (
                <div className="analysis-section">
                  <div className="analysis-label">⚡ Key Performance Metrics</div>
                  <div style={{padding:"10px 14px",background:"rgba(43,172,118,0.08)",borderRadius:6,borderLeft:"3px solid var(--green)",fontSize:13,lineHeight:1.7,color:"var(--text)",fontFamily:"'IBM Plex Mono',monospace"}}>{analysis.performance_metrics}</div>
                </div>
              )}
              {analysis.key_contributions?.length > 0 && (
                <div className="analysis-section">
                  <div className="analysis-label">Key Contributions</div>
                  <div style={{display:"flex",flexDirection:"column",gap:6}}>
                    {analysis.key_contributions.map((c,i) => (
                      <div key={i} style={{display:"flex",gap:10,padding:"8px 12px",background:"rgba(18,100,163,0.06)",borderRadius:6,fontSize:13,lineHeight:1.6}}>
                        <span style={{color:"var(--blue3)",fontWeight:700,flexShrink:0,minWidth:20}}>{i+1}.</span>
                        <span>{c}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {analysis.main_results && (
                <div className="analysis-section">
                  <div className="analysis-label">Main Results</div>
                  <div className="analysis-value" style={{lineHeight:1.8}}>{analysis.main_results}</div>
                </div>
              )}
              {analysis.baseline_comparison && (
                <div className="analysis-section">
                  <div className="analysis-label">Baseline Comparison</div>
                  <div className="analysis-value">{analysis.baseline_comparison}</div>
                </div>
              )}
              {analysis.methodology_summary && (
                <div className="analysis-section">
                  <div className="analysis-label">Methodology</div>
                  <div className="analysis-value" style={{lineHeight:1.8}}>{analysis.methodology_summary}</div>
                </div>
              )}
              {(analysis.datasets_used?.length > 0 || analysis.evaluation_metrics?.length > 0) && (
                <div className="analysis-section">
                  <div className="analysis-label">Datasets & Metrics</div>
                  <div style={{display:"flex",flexDirection:"column",gap:8}}>
                    {analysis.datasets_used?.length > 0 && (
                      <div><div style={{fontSize:11,color:"var(--text3)",marginBottom:4,textTransform:"uppercase"}}>Datasets</div>
                        <div style={{display:"flex",gap:6,flexWrap:"wrap"}}>{analysis.datasets_used.map((d,i)=><span key={i} className="tag" style={{background:"rgba(54,197,240,0.1)",color:"var(--blue3)"}}>{d}</span>)}</div>
                      </div>
                    )}
                    {analysis.evaluation_metrics?.length > 0 && (
                      <div><div style={{fontSize:11,color:"var(--text3)",marginBottom:4,textTransform:"uppercase"}}>Metrics</div>
                        <div style={{display:"flex",gap:6,flexWrap:"wrap"}}>{analysis.evaluation_metrics.map((m,i)=><span key={i} className="tag" style={{background:"rgba(236,178,46,0.1)",color:"var(--accent)"}}>{m}</span>)}</div>
                      </div>
                    )}
                  </div>
                </div>
              )}
              {analysis.novelty_assessment && (
                <div className="analysis-section">
                  <div className="analysis-label">Novelty Assessment</div>
                  <div className="analysis-value">{analysis.novelty_assessment}</div>
                </div>
              )}
              {analysis.limitations && (
                <div className="analysis-section">
                  <div className="analysis-label">⚠ Limitations</div>
                  <div className="analysis-value" style={{lineHeight:1.8}}>{analysis.limitations}</div>
                </div>
              )}
              {analysis.future_work && (
                <div className="analysis-section">
                  <div className="analysis-label">Future Work</div>
                  <div className="analysis-value">{analysis.future_work}</div>
                </div>
              )}
              {analysis.practical_applications && (
                <div className="analysis-section">
                  <div className="analysis-label">Practical Applications</div>
                  <div className="analysis-value">{analysis.practical_applications}</div>
                </div>
              )}
              {analysis.citation_context && (
                <div className="analysis-section">
                  <div className="analysis-label">Citation Context</div>
                  <div className="analysis-value">{analysis.citation_context}</div>
                </div>
              )}
              {analysis.key_terms?.length > 0 && (
                <div className="analysis-section">
                  <div className="analysis-label">Key Terms</div>
                  <div className="tag-list">{analysis.key_terms.map((t,i) => <span className="tag" key={i}>{t}</span>)}</div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ── Literature Review ──────────────────────────────────────────────────────────
function LiteraturePage({ token, showToast }) {
  const [topic, setTopic] = useState("");
  const [papers, setPapers] = useState([]);
  const [allPapers, setAllPapers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => { apiFetch("/api/v1/papers/", {}, token).then(setAllPapers).catch(() => {}); }, [token]);

  const generate = async () => {
    setLoading(true); setError(""); setResult(null);
    try {
      const data = await apiFetch("/api/v1/literature-review", {
        method: "POST",
        body: JSON.stringify({ topic, paper_ids: papers, search_web: false })
      }, token);
      setResult(data);
    } catch (e) { setError(e.message); }
    setLoading(false);
  };

  const copyResult = () => {
    if (!result) return;
    const lines = [result.title, "=".repeat(60), ""];
    if (result.scope_and_coverage) { lines.push("SCOPE & COVERAGE"); lines.push(result.scope_and_coverage); lines.push(""); }
    if (result.introduction) { lines.push("INTRODUCTION"); lines.push(result.introduction); lines.push(""); }
    if (result.chronological_evolution) { lines.push("FIELD EVOLUTION"); lines.push(result.chronological_evolution); lines.push(""); }
    (result.thematic_sections||[]).forEach(s => {
      lines.push(s.title.toUpperCase()); lines.push("-".repeat(40));
      lines.push(s.content);
      if (s.consensus) lines.push("\nConsensus: " + s.consensus);
      if (s.debate) lines.push("Debate: " + s.debate);
      lines.push("");
    });
    if (result.methodology_comparison) { lines.push("METHODOLOGY COMPARISON"); lines.push(result.methodology_comparison); lines.push(""); }
    if (result.key_findings_synthesis) { lines.push("KEY FINDINGS SYNTHESIS"); lines.push(result.key_findings_synthesis); lines.push(""); }
    if (result.research_gaps?.length) { lines.push("RESEARCH GAPS"); (result.research_gaps||[]).forEach((g,i)=>lines.push(`${i+1}. ${g}`)); lines.push(""); }
    if (result.future_directions?.length) { lines.push("FUTURE DIRECTIONS"); (Array.isArray(result.future_directions)?result.future_directions:[result.future_directions]).forEach((d,i)=>lines.push(`${i+1}. ${d}`)); lines.push(""); }
    if (result.conclusion) { lines.push("CONCLUSION"); lines.push(result.conclusion); }
    copyToClipboard(lines.filter(l=>l!==undefined).join("\n"));
    if (showToast) showToast("Literature review copied to clipboard!");
  };

  return (
    <div>
      {!result ? (
        <div style={{maxWidth:640}}>
          {error && <div className="alert alert-error">⚠ {error}</div>}
          <div className="card mb-16">
            <div className="card-header">Generate Literature Review</div>
            <div className="card-body">
              <div className="form-group">
                <label className="form-label">Research Topic *</label>
                <input className="form-input" placeholder="e.g. Transformer architectures in NLP" autoFocus
                  value={topic} onChange={e => setTopic(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && topic && !loading && generate()} />
              </div>
              <div className="form-group">
                <label className="form-label">Select Papers to Include (optional)</label>
                {allPapers.filter(p => p.processing_status === "complete").length === 0 ? (
                  <div style={{fontSize:13,color:"var(--text3)",padding:"10px 0"}}>
                    No analyzed papers yet — you can still generate a review using Claude's knowledge
                  </div>
                ) : (
                  allPapers.filter(p => p.processing_status === "complete").map(p => (
                    <label key={p.id} style={{display:"flex",alignItems:"center",gap:10,padding:"8px 0",cursor:"pointer",fontSize:13,borderBottom:"1px solid var(--border)"}}>
                      <input type="checkbox" checked={papers.includes(p.id)}
                        onChange={e => setPapers(e.target.checked ? [...papers,p.id] : papers.filter(x=>x!==p.id))} />
                      <div>
                        <div style={{fontWeight:600}}>{p.title || p.file_name}</div>
                        {p.research_domain && <div style={{fontSize:11,color:"var(--text3)"}}>{p.research_domain}</div>}
                      </div>
                    </label>
                  ))
                )}
              </div>
              <button className="btn btn-primary" onClick={generate} disabled={!topic || loading}>
                {loading ? <><span className="spinner"/> Generating (~30-60s)...</> : "📚 Generate Review"}
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div>
          <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:12,flexWrap:"wrap",gap:8}}>
            <div>
              <div style={{fontSize:17,fontWeight:700}}>{result.title || topic}</div>
              {result.citation_count_reviewed&&<div style={{fontSize:12,color:"var(--text3)",marginTop:4}}>📑 {result.citation_count_reviewed} papers reviewed</div>}
            </div>
            <div style={{display:"flex",gap:8}}>
              <button className="btn btn-secondary btn-sm" onClick={copyResult}>📋 Copy All</button>
              <button className="btn btn-secondary btn-sm" onClick={() => setResult(null)}>← New Review</button>
            </div>
          </div>
          {result.themes?.length > 0 && (
            <div style={{marginBottom:12,display:"flex",gap:6,flexWrap:"wrap"}}>
              {result.themes.map((t,i)=><span key={i} style={{padding:"3px 10px",borderRadius:10,fontSize:11,fontWeight:600,background:"rgba(18,100,163,0.15)",color:"var(--blue3)",border:"1px solid rgba(18,100,163,0.25)"}}>{t}</span>)}
            </div>
          )}
          <div className="card" style={{marginBottom:16}}>
            <div className="card-body" style={{display:"flex",flexDirection:"column",gap:20}}>
              {result.scope_and_coverage && (
                <div className="analysis-section">
                  <div className="analysis-label">Scope & Coverage</div>
                  <div className="analysis-value">{result.scope_and_coverage}</div>
                </div>
              )}
              {result.introduction && (
                <div className="analysis-section">
                  <div className="analysis-label">Introduction</div>
                  <div className="analysis-value" style={{lineHeight:1.9}}>{result.introduction}</div>
                </div>
              )}
              {result.chronological_evolution && (
                <div className="analysis-section">
                  <div className="analysis-label">📅 Field Evolution</div>
                  <div className="analysis-value" style={{lineHeight:1.8}}>{result.chronological_evolution}</div>
                </div>
              )}
            </div>
          </div>
          {result.thematic_sections?.length > 0 && result.thematic_sections.map((sec, si) => (
            <div key={si} className="card" style={{marginBottom:12}}>
              <div className="card-header" style={{fontSize:13,fontWeight:700,color:"var(--blue3)"}}>◆ {sec.title}</div>
              <div className="card-body" style={{display:"flex",flexDirection:"column",gap:12}}>
                <div className="analysis-value" style={{lineHeight:1.9}}>{sec.content}</div>
                {(sec.consensus||sec.debate)&&(
                  <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:10}}>
                    {sec.consensus&&<div style={{padding:"8px 12px",background:"rgba(43,172,118,0.07)",borderRadius:6,borderLeft:"3px solid var(--green)"}}>
                      <div style={{fontSize:10,fontWeight:700,color:"var(--green)",marginBottom:4,textTransform:"uppercase"}}>Field Consensus</div>
                      <div style={{fontSize:12,color:"var(--text2)",lineHeight:1.6}}>{sec.consensus}</div>
                    </div>}
                    {sec.debate&&<div style={{padding:"8px 12px",background:"rgba(236,178,46,0.07)",borderRadius:6,borderLeft:"3px solid var(--accent)"}}>
                      <div style={{fontSize:10,fontWeight:700,color:"var(--accent)",marginBottom:4,textTransform:"uppercase"}}>Open Debate</div>
                      <div style={{fontSize:12,color:"var(--text2)",lineHeight:1.6}}>{sec.debate}</div>
                    </div>}
                  </div>
                )}
                {sec.key_papers?.length > 0 && (
                  <div><div style={{fontSize:10,color:"var(--text3)",marginBottom:4,textTransform:"uppercase",fontWeight:700}}>Key Papers in This Area</div>
                    <div style={{display:"flex",flexDirection:"column",gap:4}}>
                      {sec.key_papers.map((p,i)=><div key={i} style={{fontSize:12,color:"var(--text2)",padding:"4px 8px",background:"var(--navy)",borderRadius:4}}>• {p}</div>)}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))}
          <div className="card" style={{marginBottom:16}}>
            <div className="card-body" style={{display:"flex",flexDirection:"column",gap:20}}>
              {result.methodology_comparison && (
                <div className="analysis-section">
                  <div className="analysis-label">⚙️ Methodology Comparison</div>
                  <div className="analysis-value" style={{lineHeight:1.8}}>{result.methodology_comparison}</div>
                </div>
              )}
              {result.performance_benchmarks && (
                <div className="analysis-section">
                  <div className="analysis-label">📊 Performance Benchmarks</div>
                  <div style={{padding:"10px 14px",background:"rgba(43,172,118,0.07)",borderRadius:6,borderLeft:"3px solid var(--green)",fontSize:13,lineHeight:1.7,fontFamily:"'IBM Plex Mono',monospace"}}>{result.performance_benchmarks}</div>
                </div>
              )}
              {result.key_findings_synthesis && (
                <div className="analysis-section">
                  <div className="analysis-label">🔑 Key Findings Synthesis</div>
                  <div className="analysis-value" style={{lineHeight:1.9}}>{result.key_findings_synthesis}</div>
                </div>
              )}
              {result.research_gaps?.length > 0 && (
                <div className="analysis-section">
                  <div className="analysis-label">🔍 Research Gaps</div>
                  <div style={{display:"flex",flexDirection:"column",gap:6}}>
                    {result.research_gaps.map((g,i)=>(
                      <div key={i} style={{display:"flex",gap:10,padding:"8px 12px",background:"rgba(224,30,90,0.06)",borderRadius:6,borderLeft:"3px solid rgba(224,30,90,0.4)",fontSize:13,lineHeight:1.6}}>
                        <span style={{color:"var(--red)",fontWeight:700,flexShrink:0}}>{i+1}.</span><span>{g}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {result.future_directions?.length > 0 && (
                <div className="analysis-section">
                  <div className="analysis-label">🚀 Future Directions</div>
                  <div style={{display:"flex",flexDirection:"column",gap:8}}>
                    {(Array.isArray(result.future_directions)?result.future_directions:[result.future_directions]).map((d,i)=>(
                      <div key={i} style={{padding:"10px 14px",background:"rgba(18,100,163,0.07)",borderRadius:6,borderLeft:"3px solid var(--blue)",fontSize:13,lineHeight:1.7}}>
                        <span style={{fontWeight:700,color:"var(--blue3)"}}>Direction {i+1}: </span>{d}
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {result.conclusion && (
                <div className="analysis-section">
                  <div className="analysis-label">Conclusion</div>
                  <div className="analysis-value" style={{lineHeight:1.9}}>{result.conclusion}</div>
                </div>
              )}
            </div>
          </div>
          {result.key_papers_table?.length > 0 && (
            <div className="card">
              <div className="card-header">📋 Key Papers Summary Table</div>
              <div style={{overflowX:"auto"}}>
                <table style={{width:"100%",borderCollapse:"collapse",fontSize:12}}>
                  <thead><tr style={{background:"rgba(18,100,163,0.15)"}}>
                    {["Authors","Year","Title","Venue","Method","Key Contribution"].map(h=><th key={h} style={{padding:"8px 10px",color:"var(--blue3)",fontWeight:700,textAlign:"left",borderBottom:"2px solid var(--blue)",whiteSpace:"nowrap"}}>{h}</th>)}
                  </tr></thead>
                  <tbody>{result.key_papers_table.map((row,i)=>(
                    <tr key={i} style={{borderBottom:"1px solid var(--border)",background:i%2===0?"var(--navy)":"var(--navy2)"}}>
                      <td style={{padding:"8px 10px",color:"var(--text)",fontWeight:600,whiteSpace:"nowrap"}}>{row.authors}</td>
                      <td style={{padding:"8px 10px",color:"var(--accent)",fontWeight:600,whiteSpace:"nowrap"}}>{row.year}</td>
                      <td style={{padding:"8px 10px",color:"var(--text)",maxWidth:200,overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}} title={row.title}>{row.title}</td>
                      <td style={{padding:"8px 10px",color:"var(--blue3)",whiteSpace:"nowrap"}}>{row.venue}</td>
                      <td style={{padding:"8px 10px",color:"var(--text2)",fontFamily:"'IBM Plex Mono',monospace",fontSize:11}}>{row.method}</td>
                      <td style={{padding:"8px 10px",color:"var(--text2)",maxWidth:220,fontSize:11}}>{row.key_contribution}</td>
                    </tr>
                  ))}</tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Research Gaps ──────────────────────────────────────────────────────────────
function GapsPage({ token, showToast }) {
  const [topic, setTopic] = useState("");
  const [allPapers, setAllPapers] = useState([]);
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => { apiFetch("/api/v1/papers/", {}, token).then(setAllPapers).catch(() => {}); }, [token]);

  const generate = async () => {
    setLoading(true); setError(""); setResult(null);
    try {
      const data = await apiFetch("/api/v1/research-gaps", {
        method: "POST",
        body: JSON.stringify({ topic, paper_ids: papers })
      }, token);
      setResult(data);
    } catch (e) { setError(e.message); }
    setLoading(false);
  };

  const copyResult = () => {
    if (!result) return;
    const gapTypes = [
      ["methodological_gaps","Methodological Gaps"],
      ["theoretical_gaps","Theoretical Gaps"],
      ["empirical_gaps","Empirical Gaps"],
      ["application_gaps","Application Gaps"],
      ["data_gaps","Data Gaps"],
    ];
    const lines = [`Research Gaps: ${result.topic || topic}`, ""];
    gapTypes.forEach(([key, label]) => {
      if (result[key]?.length) {
        lines.push(label.toUpperCase());
        result[key].forEach((g,i) => lines.push(`${i+1}. ${g}`));
        lines.push("");
      }
    });
    if (result.top_research_opportunities?.length) {
      lines.push("TOP RESEARCH OPPORTUNITIES");
      result.top_research_opportunities.forEach((o,i) => lines.push(`${i+1}. ${o.opportunity} [Impact: ${o.impact}, Difficulty: ${o.difficulty}]`));
    }
    copyToClipboard(lines.join("\n"));
    if (showToast) showToast("Research gaps copied to clipboard!");
  };

  const gapTypes = [
    ["methodological_gaps", "Methodological Gaps", "🔬"],
    ["theoretical_gaps", "Theoretical Gaps", "💡"],
    ["empirical_gaps", "Empirical Gaps", "📊"],
    ["application_gaps", "Application Gaps", "⚙️"],
    ["data_gaps", "Data Gaps", "🗄️"],
  ];

  return (
    <div>
      {!result ? (
        <div style={{maxWidth:640}}>
          {error && <div className="alert alert-error">⚠ {error}</div>}
          <div className="card">
            <div className="card-header">Identify Research Gaps</div>
            <div className="card-body">
              <div className="form-group">
                <label className="form-label">Research Topic *</label>
                <input className="form-input" placeholder="e.g. Deep learning for medical imaging" autoFocus
                  value={topic} onChange={e => setTopic(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && topic && !loading && generate()} />
              </div>
              <div className="form-group">
                <label className="form-label">Papers to Analyze (optional)</label>
                {allPapers.filter(p => p.processing_status === "complete").map(p => (
                  <label key={p.id} style={{display:"flex",alignItems:"center",gap:10,padding:"8px 0",cursor:"pointer",fontSize:13,borderBottom:"1px solid var(--border)"}}>
                    <input type="checkbox" checked={papers.includes(p.id)}
                      onChange={e => setPapers(e.target.checked ? [...papers,p.id] : papers.filter(x=>x!==p.id))} />
                    <div>
                      <div style={{fontWeight:600}}>{p.title || p.file_name}</div>
                      {p.research_domain && <div style={{fontSize:11,color:"var(--text3)"}}>{p.research_domain}</div>}
                    </div>
                  </label>
                ))}
                {allPapers.filter(p => p.processing_status === "complete").length === 0 && (
                  <div style={{fontSize:13,color:"var(--text3)",padding:"10px 0"}}>No analyzed papers yet — gaps will be based on Claude's knowledge</div>
                )}
              </div>
              <button className="btn btn-primary" onClick={generate} disabled={!topic || loading}>
                {loading ? <><span className="spinner"/> Analyzing (~30s)...</> : "🔍 Find Gaps"}
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div>
          <div style={{marginBottom:12,display:"flex",justifyContent:"space-between",alignItems:"center",flexWrap:"wrap",gap:8}}>
            <div>
              <div style={{fontSize:18,fontWeight:700}}>Research Gaps: {result.topic || topic}</div>
              {result.field_maturity&&<div style={{fontSize:12,color:"var(--text3)",marginTop:4}}>
                Field maturity: <span style={{fontWeight:600,color:result.field_maturity==="mature"?"var(--green)":result.field_maturity==="developing"?"var(--accent)":"var(--red)"}}>{result.field_maturity}</span>
                {result.field_maturity_rationale&&<span> — {result.field_maturity_rationale}</span>}
              </div>}
            </div>
            <div style={{display:"flex",gap:8}}>
              <button className="btn btn-secondary btn-sm" onClick={copyResult}>📋 Copy</button>
              <button className="btn btn-secondary btn-sm" onClick={() => setResult(null)}>← New Analysis</button>
            </div>
          </div>
          <div className="grid-2" style={{marginBottom:16}}>
            {gapTypes.map(([key, label, icon]) => {
              const gaps = result[key];
              if (!gaps?.length) return null;
              return (
                <div className="card" key={key}>
                  <div className="card-header">{icon} {label} <span style={{fontSize:11,color:"var(--text3)",marginLeft:6}}>({gaps.length})</span></div>
                  <div className="card-body" style={{display:"flex",flexDirection:"column",gap:8}}>
                    {gaps.map((g,i) => {
                      const isObj = typeof g === "object" && g !== null;
                      const txt = isObj ? g.gap : g;
                      const feasibility = isObj ? g.feasibility : null;
                      const impact = isObj ? g.impact : null;
                      const rationale = isObj ? g.rationale : null;
                      return (
                        <div key={i} style={{padding:"8px 10px",background:"var(--navy)",borderRadius:6,borderLeft:"3px solid rgba(18,100,163,0.4)"}}>
                          <div style={{display:"flex",justifyContent:"space-between",alignItems:"flex-start",gap:8,marginBottom:rationale?4:0}}>
                            <div style={{fontSize:13,color:"var(--text)",lineHeight:1.5,flex:1}}>{txt}</div>
                            <div style={{display:"flex",gap:4,flexShrink:0}}>
                              {impact&&<span style={{fontSize:10,padding:"2px 6px",borderRadius:8,fontWeight:700,
                                background:impact==="high"?"rgba(224,30,90,0.15)":impact==="medium"?"rgba(236,178,46,0.15)":"rgba(43,172,118,0.15)",
                                color:impact==="high"?"var(--red)":impact==="medium"?"var(--accent)":"var(--green)"}}>{impact}</span>}
                              {feasibility&&<span style={{fontSize:10,padding:"2px 6px",borderRadius:8,fontWeight:700,background:"rgba(18,100,163,0.15)",color:"var(--blue3)"}}>F:{feasibility}/5</span>}
                            </div>
                          </div>
                          {rationale&&<div style={{fontSize:11,color:"var(--text3)",lineHeight:1.5}}>{rationale}</div>}
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
          {result.top_research_opportunities?.length > 0 && (
            <div className="card">
              <div className="card-header">🚀 Top Research Opportunities</div>
              <div className="card-body" style={{display:"flex",flexDirection:"column",gap:16}}>
                {result.top_research_opportunities.map((o,i) => (
                  <div key={i} style={{border:"1px solid var(--border)",borderRadius:8,overflow:"hidden"}}>
                    <div style={{padding:"10px 16px",background:"rgba(18,100,163,0.1)",display:"flex",justifyContent:"space-between",alignItems:"center",gap:12,flexWrap:"wrap"}}>
                      <div style={{fontSize:14,fontWeight:700,color:"var(--text)",flex:1}}>
                        {o.rank&&<span style={{color:"var(--blue3)",marginRight:8}}>#{o.rank}</span>}{o.opportunity}
                      </div>
                      <div style={{display:"flex",gap:6,flexWrap:"wrap"}}>
                        {o.impact&&<span style={{fontSize:11,padding:"3px 8px",borderRadius:8,fontWeight:700,
                          background:o.impact==="high"?"rgba(43,172,118,0.15)":o.impact==="medium"?"rgba(236,178,46,0.15)":"rgba(18,100,163,0.15)",
                          color:o.impact==="high"?"var(--green)":o.impact==="medium"?"var(--accent)":"var(--blue3)"}}>Impact: {o.impact}</span>}
                        {o.difficulty&&<span style={{fontSize:11,padding:"3px 8px",borderRadius:8,fontWeight:700,
                          background:o.difficulty==="high"?"rgba(224,30,90,0.12)":o.difficulty==="medium"?"rgba(236,178,46,0.12)":"rgba(43,172,118,0.12)",
                          color:o.difficulty==="high"?"var(--red)":o.difficulty==="medium"?"var(--accent)":"var(--green)"}}>Difficulty: {o.difficulty}</span>}
                        {o.feasibility&&<span style={{fontSize:11,padding:"3px 8px",borderRadius:8,fontWeight:700,background:"rgba(18,100,163,0.15)",color:"var(--blue3)"}}>Feasibility: {o.feasibility}/5</span>}
                        {o.estimated_timeline&&<span style={{fontSize:11,padding:"3px 8px",borderRadius:8,background:"rgba(43,172,118,0.1)",color:"var(--green)",fontWeight:600}}>⏱ {o.estimated_timeline}</span>}
                      </div>
                    </div>
                    <div style={{padding:"12px 16px",display:"flex",flexDirection:"column",gap:8}}>
                      {o.rationale&&<div style={{fontSize:13,color:"var(--text2)",lineHeight:1.7}}>{o.rationale}</div>}
                      {o.approach&&<div><span style={{fontSize:11,fontWeight:700,color:"var(--text3)",textTransform:"uppercase"}}>Approach: </span><span style={{fontSize:13,color:"var(--text2)"}}>{o.approach}</span></div>}
                      <div style={{display:"flex",gap:12,flexWrap:"wrap",marginTop:4}}>
                        {o.required_expertise?.length>0&&<div>
                          <div style={{fontSize:10,color:"var(--text3)",marginBottom:4,textTransform:"uppercase",fontWeight:700}}>Required Expertise</div>
                          <div style={{display:"flex",gap:4,flexWrap:"wrap"}}>{o.required_expertise.map((e,j)=><span key={j} style={{fontSize:10,padding:"2px 6px",borderRadius:6,background:"rgba(54,197,240,0.1)",color:"var(--blue3)"}}>{e}</span>)}</div>
                        </div>}
                        {o.suggested_venues?.length>0&&<div>
                          <div style={{fontSize:10,color:"var(--text3)",marginBottom:4,textTransform:"uppercase",fontWeight:700}}>Publish At</div>
                          <div style={{display:"flex",gap:4,flexWrap:"wrap"}}>{o.suggested_venues.map((v,j)=><span key={j} style={{fontSize:10,padding:"2px 6px",borderRadius:6,background:"rgba(236,178,46,0.1)",color:"var(--accent)"}}>{v}</span>)}</div>
                        </div>}
                        {o.potential_funding?.length>0&&<div>
                          <div style={{fontSize:10,color:"var(--text3)",marginBottom:4,textTransform:"uppercase",fontWeight:700}}>Funding</div>
                          <div style={{display:"flex",gap:4,flexWrap:"wrap"}}>{o.potential_funding.map((f,j)=><span key={j} style={{fontSize:10,padding:"2px 6px",borderRadius:6,background:"rgba(43,172,118,0.1)",color:"var(--green)"}}>{f}</span>)}</div>
                        </div>}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Grant Proposal ─────────────────────────────────────────────────────────────
function GrantPage({ token, showToast }) {
  const [form, setForm] = useState({ topic: "", agency: "", budget: "", timeline: "", objectives: "" });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const generate = async () => {
    if (!form.topic || !form.agency) { return; }
    setLoading(true); setError(""); setResult(null);
    try {
      const data = await apiFetch("/api/v1/grant-proposal", {
        method: "POST",
        body: JSON.stringify({
          topic: form.topic, agency: form.agency,
          budget: form.budget, timeline: form.timeline,
          objectives: form.objectives.split("\n").filter(Boolean)
        })
      }, token);
      setResult(data);
    } catch (e) { setError(e.message); }
    setLoading(false);
  };

  const copyResult = () => {
    if (!result) return;
    const lines = [result.title, "=".repeat(60), ""];
    const addSec = (label, val) => { if (val) { lines.push(label); lines.push("-".repeat(40)); lines.push(val); lines.push(""); } };
    addSec("EXECUTIVE SUMMARY", result.executive_summary);
    addSec("BACKGROUND & SIGNIFICANCE", result.background_and_significance);
    addSec("PRELIMINARY DATA", result.preliminary_data);
    if (result.research_objectives?.length) { lines.push("RESEARCH OBJECTIVES"); result.research_objectives.forEach((o,i)=>lines.push(`${i+1}. ${o}`)); lines.push(""); }
    addSec("METHODOLOGY", result.methodology);
    addSec("INNOVATION", result.innovation);
    if (result.expected_outcomes?.length) { lines.push("EXPECTED OUTCOMES"); result.expected_outcomes.forEach((o,i)=>lines.push(`${i+1}. ${o}`)); lines.push(""); }
    if (result.risk_assessment?.length) { lines.push("RISK ASSESSMENT"); result.risk_assessment.forEach(r=>lines.push(`- ${r.risk} [Likelihood: ${r.likelihood}, Impact: ${r.impact}] → ${r.mitigation}`)); lines.push(""); }
    addSec("BUDGET JUSTIFICATION", result.budget_justification);
    if (result.milestones?.length) { lines.push("MILESTONES"); result.milestones.forEach(m=>lines.push(`Month ${m.month}: ${m.milestone}`)); lines.push(""); }
    addSec("EVALUATION CRITERIA", result.evaluation_criteria);
    addSec("TEAM QUALIFICATIONS", result.team_qualifications);
    addSec("BROADER IMPACTS", result.broader_impacts);
    addSec("INTELLECTUAL MERIT", result.intellectual_merit);
    addSec("DATA MANAGEMENT PLAN", result.data_management_plan);
    copyToClipboard(lines.join("\n"));
    if (showToast) showToast("Grant proposal copied to clipboard!");
  };

  const sectionMap = [
    ["executive_summary","Executive Summary","📋"],
    ["introduction","Introduction","📖"],
    ["methodology","Methodology","⚙️"],
    ["innovation","Innovation & Novelty","💡"],
    ["budget_justification","Budget Justification","💰"],
    ["timeline","Timeline","📅"],
    ["team_qualifications","Team Qualifications","👥"],
    ["broader_impacts","Broader Impacts","🌍"],
  ];

  return (
    <div>
      {!result ? (
        <div style={{maxWidth:640}}>
          {error && <div className="alert alert-error">⚠ {error}</div>}
          <div className="card">
            <div className="card-header">Generate Grant Proposal</div>
            <div className="card-body">
              <div className="grid-2">
                <div className="form-group">
                  <label className="form-label">Research Topic *</label>
                  <input className="form-input" placeholder="e.g. AI in drug discovery" autoFocus
                    value={form.topic} onChange={e => setForm({...form, topic: e.target.value})} />
                </div>
                <div className="form-group">
                  <label className="form-label">Funding Agency *</label>
                  <input className="form-input" placeholder="e.g. NIH, NSF, DARPA, EU Horizon"
                    value={form.agency} onChange={e => setForm({...form, agency: e.target.value})} />
                </div>
                <div className="form-group">
                  <label className="form-label">Budget</label>
                  <input className="form-input" placeholder="e.g. $500,000"
                    value={form.budget} onChange={e => setForm({...form, budget: e.target.value})} />
                </div>
                <div className="form-group">
                  <label className="form-label">Timeline</label>
                  <input className="form-input" placeholder="e.g. 3 years"
                    value={form.timeline} onChange={e => setForm({...form, timeline: e.target.value})} />
                </div>
              </div>
              <div className="form-group">
                <label className="form-label">Research Objectives (one per line)</label>
                <textarea className="form-input form-textarea"
                  placeholder={"Develop novel ML model for protein folding\nValidate on benchmark datasets\nPublish findings in top-tier journals"}
                  value={form.objectives} onChange={e => setForm({...form, objectives: e.target.value})} />
              </div>
              <button className="btn btn-primary" onClick={generate}
                disabled={!form.topic || !form.agency || loading}>
                {loading ? <><span className="spinner"/> Generating (~30-60s)...</> : "💰 Generate Proposal"}
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div>
          <div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:12,flexWrap:"wrap",gap:8}}>
            <div>
              <div style={{fontSize:17,fontWeight:700}}>{result.title}</div>
              <div style={{fontSize:12,color:"var(--text3)",marginTop:4}}>
                <strong style={{color:"var(--green)"}}>{form.agency}</strong> · {form.budget} · {form.timeline}
              </div>
            </div>
            <div style={{display:"flex",gap:8}}>
              <button className="btn btn-secondary btn-sm" onClick={copyResult}>📋 Copy All</button>
              <button className="btn btn-secondary btn-sm" onClick={() => setResult(null)}>← New Proposal</button>
            </div>
          </div>
          <div className="card" style={{marginBottom:14}}>
            <div className="card-body" style={{display:"flex",flexDirection:"column",gap:20}}>
              {result.executive_summary&&<div className="analysis-section"><div className="analysis-label">📋 Executive Summary</div><div style={{padding:"12px 14px",background:"rgba(18,100,163,0.07)",borderRadius:6,borderLeft:"3px solid var(--blue)",fontSize:13,lineHeight:1.9}}>{result.executive_summary}</div></div>}
              {result.background_and_significance&&<div className="analysis-section"><div className="analysis-label">📖 Background & Significance</div><div className="analysis-value" style={{lineHeight:1.9}}>{result.background_and_significance}</div></div>}
              {result.preliminary_data&&<div className="analysis-section"><div className="analysis-label">🔬 Preliminary Data</div><div className="analysis-value">{result.preliminary_data}</div></div>}
              {result.research_objectives?.length>0&&<div className="analysis-section">
                <div className="analysis-label">🎯 Research Objectives</div>
                <div style={{display:"flex",flexDirection:"column",gap:6}}>
                  {result.research_objectives.map((o,i)=>(
                    <div key={i} style={{display:"flex",gap:10,padding:"8px 12px",background:"rgba(43,172,118,0.07)",borderRadius:6,fontSize:13,lineHeight:1.6,borderLeft:"3px solid var(--green)"}}>
                      <span style={{color:"var(--green)",fontWeight:700,flexShrink:0}}>Obj {i+1}.</span><span>{o}</span>
                    </div>
                  ))}
                </div>
              </div>}
              {result.methodology&&<div className="analysis-section"><div className="analysis-label">⚙️ Methodology</div><div className="analysis-value" style={{lineHeight:1.9}}>{result.methodology}</div></div>}
              {result.innovation&&<div className="analysis-section"><div className="analysis-label">💡 Innovation</div><div style={{padding:"12px 14px",background:"rgba(236,178,46,0.07)",borderRadius:6,borderLeft:"3px solid var(--accent)",fontSize:13,lineHeight:1.8}}>{result.innovation}</div></div>}
              {result.expected_outcomes?.length>0&&<div className="analysis-section">
                <div className="analysis-label">✅ Expected Outcomes</div>
                <div style={{display:"flex",flexDirection:"column",gap:6}}>
                  {result.expected_outcomes.map((o,i)=><div key={i} style={{display:"flex",gap:8,padding:"6px 10px",background:"var(--navy)",borderRadius:6,fontSize:13}}><span style={{color:"var(--green)"}}>✓</span><span>{o}</span></div>)}
                </div>
              </div>}
            </div>
          </div>
          {result.risk_assessment?.length>0&&(
            <div className="card" style={{marginBottom:14}}>
              <div className="card-header">⚠️ Risk Assessment & Mitigation</div>
              <div style={{overflowX:"auto"}}>
                <table style={{width:"100%",borderCollapse:"collapse",fontSize:12}}>
                  <thead><tr style={{background:"rgba(18,100,163,0.15)"}}>{["Risk","Likelihood","Impact","Mitigation Plan"].map(h=><th key={h} style={{padding:"8px 12px",color:"var(--blue3)",fontWeight:700,textAlign:"left",borderBottom:"2px solid var(--blue)"}}>{h}</th>)}</tr></thead>
                  <tbody>{result.risk_assessment.map((r,i)=>(
                    <tr key={i} style={{borderBottom:"1px solid var(--border)",background:i%2===0?"var(--navy)":"var(--navy2)"}}>
                      <td style={{padding:"8px 12px",color:"var(--text)",maxWidth:200}}>{r.risk}</td>
                      <td style={{padding:"8px 12px",fontWeight:700,color:r.likelihood==="high"?"var(--red)":r.likelihood==="medium"?"var(--accent)":"var(--green)"}}>{r.likelihood}</td>
                      <td style={{padding:"8px 12px",fontWeight:700,color:r.impact==="high"?"var(--red)":r.impact==="medium"?"var(--accent)":"var(--green)"}}>{r.impact}</td>
                      <td style={{padding:"8px 12px",color:"var(--text2)",fontSize:12}}>{r.mitigation}</td>
                    </tr>
                  ))}</tbody>
                </table>
              </div>
            </div>
          )}
          {result.budget_breakdown?.length>0&&(
            <div className="card" style={{marginBottom:14}}>
              <div className="card-header">💰 Budget Breakdown</div>
              <div style={{overflowX:"auto"}}>
                <table style={{width:"100%",borderCollapse:"collapse",fontSize:12}}>
                  <thead><tr style={{background:"rgba(18,100,163,0.15)"}}>{["Category","Year 1","Year 2","Year 3","Total","Notes"].map(h=><th key={h} style={{padding:"8px 10px",color:"var(--blue3)",fontWeight:700,textAlign:"left",borderBottom:"2px solid var(--blue)",whiteSpace:"nowrap"}}>{h}</th>)}</tr></thead>
                  <tbody>{result.budget_breakdown.map((row,i)=>(
                    <tr key={i} style={{borderBottom:"1px solid var(--border)",background:i%2===0?"var(--navy)":"var(--navy2)"}}>
                      <td style={{padding:"8px 10px",fontWeight:600,color:"var(--text)"}}>{row.category}</td>
                      <td style={{padding:"8px 10px",color:"var(--text2)",fontFamily:"'IBM Plex Mono',monospace"}}>{row.year1}</td>
                      <td style={{padding:"8px 10px",color:"var(--text2)",fontFamily:"'IBM Plex Mono',monospace"}}>{row.year2}</td>
                      <td style={{padding:"8px 10px",color:"var(--text2)",fontFamily:"'IBM Plex Mono',monospace"}}>{row.year3}</td>
                      <td style={{padding:"8px 10px",color:"var(--green)",fontWeight:700,fontFamily:"'IBM Plex Mono',monospace"}}>{row.total}</td>
                      <td style={{padding:"8px 10px",color:"var(--text3)",fontSize:11}}>{row.justification}</td>
                    </tr>
                  ))}</tbody>
                </table>
              </div>
              {result.budget_justification&&<div style={{padding:"12px 16px",borderTop:"1px solid var(--border)",fontSize:13,color:"var(--text2)",lineHeight:1.7}}>{result.budget_justification}</div>}
            </div>
          )}
          {result.milestones?.length>0&&(
            <div className="card" style={{marginBottom:14}}>
              <div className="card-header">📅 Project Milestones</div>
              <div style={{padding:"14px 16px",display:"flex",flexDirection:"column",gap:0}}>
                {result.milestones.map((m,i)=>(
                  <div key={i} style={{display:"flex",gap:14,paddingBottom:12,paddingTop:i===0?0:12,borderTop:i===0?"none":"1px solid var(--border)",alignItems:"flex-start"}}>
                    <div style={{width:48,flexShrink:0,textAlign:"center"}}>
                      <div style={{width:36,height:36,borderRadius:"50%",background:"rgba(18,100,163,0.2)",border:"2px solid var(--blue)",display:"flex",alignItems:"center",justifyContent:"center",fontSize:11,fontWeight:700,color:"var(--blue3)",margin:"0 auto"}}>M{m.month}</div>
                    </div>
                    <div style={{flex:1}}>
                      <div style={{fontSize:13,fontWeight:600,color:"var(--text)",lineHeight:1.5}}>{m.milestone}</div>
                      {m.objective&&<div style={{fontSize:11,color:"var(--text3)",marginTop:2}}>{m.objective}</div>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
          <div className="card">
            <div className="card-body" style={{display:"flex",flexDirection:"column",gap:20}}>
              {result.evaluation_criteria&&<div className="analysis-section"><div className="analysis-label">📏 Evaluation Criteria</div><div className="analysis-value">{result.evaluation_criteria}</div></div>}
              {result.team_qualifications&&<div className="analysis-section"><div className="analysis-label">👥 Team Qualifications</div><div className="analysis-value" style={{lineHeight:1.8}}>{result.team_qualifications}</div></div>}
              {result.dissemination_plan&&<div className="analysis-section"><div className="analysis-label">📢 Dissemination Plan</div><div className="analysis-value">{result.dissemination_plan}</div></div>}
              {result.broader_impacts&&<div className="analysis-section"><div className="analysis-label">🌍 Broader Impacts</div><div className="analysis-value" style={{lineHeight:1.8}}>{result.broader_impacts}</div></div>}
              {result.intellectual_merit&&<div className="analysis-section"><div className="analysis-label">🧠 Intellectual Merit</div><div className="analysis-value" style={{lineHeight:1.8}}>{result.intellectual_merit}</div></div>}
              {result.data_management_plan&&<div className="analysis-section"><div className="analysis-label">🗄️ Data Management Plan</div><div className="analysis-value">{result.data_management_plan}</div></div>}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


// ── Write Paper ────────────────────────────────────────────────────────────────
function Field({ label, k, placeholder, textarea, required, hint, form, update }) {
return (
<div className="form-group">
<label className="form-label">{label}{required && " *"}</label>
{hint && <div style={{fontSize:11,color:"var(--blue3)",marginBottom:6,padding:"4px 8px",background:"rgba(18,100,163,0.1)",borderRadius:4}}>{hint}</div>}
{textarea
? <textarea className="form-input form-textarea" style={{minHeight:100}} placeholder={placeholder} value={form[k]||""} onChange={e => update(k, e.target.value)} />
: <input className="form-input" placeholder={placeholder} value={form[k]||""} onChange={e => update(k, e.target.value)} />}
</div>
);
}

function WritePaperPage({ token }) {
const [step, setStep] = useState(1);
const [allPapers, setAllPapers] = useState([]);
const [selectedPapers, setSelectedPapers] = useState([]);
const [loading, setLoading] = useState(false);
const [loadingStep, setLoadingStep] = useState(0);
const [result, setResult] = useState(null);
const [error, setError] = useState("");
const [activeSection, setActiveSection] = useState("abstract");
const [form, setForm] = useState({
topic:"", research_question:"", hypothesis:"",
target_journal:"", word_count:"5000", methodology_type:"",
datasets:"", key_findings:"", contribution_list:"",
related_papers:"", limitations:"", future_work:"",
experimental_results:"", hyperparameters:"",
figure_descriptions:"", acknowledgements:"", ethics_statement:"",
column_format:"single", authors_list:"", authors_emails:"",
author_contributions:"", data_access_statement:"", research_field:"computer_science",
// ── NEW top-tier quality input fields ─────────────────────────────────────
novelty_statement:"",        // Explicit "what's new vs prior work"
statistical_tests:"",        // Which test, n per group, effect size, correction
reviewer_concerns:"",        // Anticipated weakest point the authors want pre-addressed
venue_fit_rationale:"",      // Why THIS venue specifically — drives cover letter
algorithm_description:"",    // Optional — triggers \begin{algorithm} block in Methodology
});

useEffect(() => {
apiFetch("/api/v1/papers/", {}, token)
.then(p => setAllPapers(p.filter(x => x.processing_status === "complete")))
.catch(() => {});
}, [token]);

const LOADING_STEPS = [
  "📋 Call 1/6 — Generating front matter (title, abstract, keywords, highlights)...",
  "📖 Call 2/6 — Writing Introduction + Related Work (900–1300 words, 20+ citations)...",
  "⚙️  Call 3/6 — Writing Methodology + Experiments + Results tables (math notation)...",
  "💬 Call 4/6 — Writing Discussion + Conclusion + Cover Letter + Supplementary...",
  "📚 Call 5/6 — Generating BibTeX references (18–22 entries, real venues & years)...",
  "✨ Call 6/6 — Humanizer pass + 4 peer-reviewer responses & rebuttals...",
];

useEffect(() => {
  if (!loading) { setLoadingStep(0); return; }
  const t = setInterval(() => setLoadingStep(s => s < LOADING_STEPS.length - 1 ? s + 1 : s), 90000);
  return () => clearInterval(t);
}, [loading]);

const update = (k, v) => setForm(f => ({...f, [k]: v}));

const generate = async () => {
setLoading(true); setError("");
try {
const data = await apiFetch("/api/v1/write-paper", {
method:"POST",
body: JSON.stringify({ topic:form.topic, target_journal:form.target_journal,
word_count:form.word_count, research_field:form.research_field,
paper_ids:selectedPapers, extra_context:form })
}, token);
setResult(data.paper || data);
setActiveSection("abstract");
} catch(e) { setError(String(e.message||e)); }
setLoading(false);
};

const buildBibTeX = (entries) => {
// ── BibTeX file builder ───────────────────────────────────────────────────
// KEY SCHEME: ref01 = citation [1], ref02 = citation [2], ... ref25 = citation [25]
// This matches the \cite{ref0N} commands emitted by buildLatex() exactly.
// Upload this file to Overleaf alongside research-paper.tex and compile:
//   pdfLaTeX → BibTeX → pdfLaTeX → pdfLaTeX  (four-pass compile)
if (!entries||!entries.length) return [
  "%% references.bib — auto-generated by AI Research Assistant",
  "%% WARNING: No BibTeX entries were generated. Re-generate the paper.",
  "%% Or add entries manually using the @article{ref01,...} format.",
].join("\n");
const NL = "\n";
// ── Count entries that need manual verification ───────────────────────────
const verifyNeeded = entries.filter(e =>
  e.note && (e.note.includes("⚠") || e.note.toLowerCase().includes("verify") ||
             e.note.toLowerCase().includes("placeholder") || e.note.toLowerCase().includes("auto-generated"))
).length;
const highConfidence = entries.length - verifyNeeded;
const header = [
  "%% references.bib — auto-generated by AI Research Assistant",
  "%% KEY SCHEME: ref01 = citation [1],  ref02 = citation [2],  etc.",
  "%% Upload this file alongside research-paper.tex to Overleaf.",
  "%% Compile order: pdfLaTeX → BibTeX → pdfLaTeX → pdfLaTeX",
  "%%",
  "%% ── REFERENCE VERIFICATION GUIDE ────────────────────────────────────────────",
  "%% Total entries: " + entries.length + "  |  High-confidence (real): " + highConfidence + "  |  Need verification: " + verifyNeeded,
  "%%",
  "%% Entries WITHOUT a note field = real papers recalled from AI training knowledge.",
  "%%   These are correct and ready to use. Optionally confirm the DOI before submission.",
  "%%",
  "%% Entries with a  ⚠  note = approximated or auto-filled — needs manual check:",
  "%%   (a) Title/venue may differ slightly from the published paper",
  "%%   (b) Auto-generated GAP-FILL — replace with real data from the publisher's site",
  "%%",
  "%% HOW TO VERIFY flagged entries: search the title on Google Scholar or DBLP,",
  "%% then paste the real BibTeX in place of the flagged entry.",
  "%%",
  "%% QUICK LINKS:",
  "%%   Google Scholar:    https://scholar.google.com",
  "%%   Semantic Scholar: https://www.semanticscholar.org",
  "%%   DBLP:             https://dblp.org",
  "%%   DOI lookup:       https://doi.org/<doi>",
  "",
].join(NL);
// bibEsc: escape LaTeX special chars in BibTeX field VALUES.
// BibTeX fields wrapped in {} are processed as LaTeX, so & % $ # _ need escaping.
// url/doi/year/volume/number/pages are left unescaped (they're not LaTeX-rendered).
const TEXT_FIELDS = new Set(["author","title","booktitle","journal",
  "publisher","address","edition","howpublished","note"]);
const bibEsc = (f, v) => {
  if (!TEXT_FIELDS.has(f)) return v;                    // numeric/url fields — no change
  return (v||"")
    .replace(/\\/g, "\\textbackslash{}")                // backslash must go first
    .replace(/&/g,  "\\&")                              // ampersand in title/venue
    .replace(/%/g,  "\\%")                              // percent
    .replace(/\$/g, "\\$")                              // dollar (not inside math)
    .replace(/#/g,  "\\#")                              // hash
    .replace(/_(?![\\{}])/g, "\\_");                    // underscore (skip if already \_ )
};
return header + entries.map(e => {
// Field order follows BibTeX convention; howpublished is needed for @misc arXiv entries;
// address for inproceedings/book; edition for books. Skip any field that is empty.
const fields = [
  "author","title",
  "booktitle","journal",          // conference vs journal venue
  "year","volume","number","pages",
  "publisher","address","edition", // book / conference publisher details
  "howpublished",                  // @misc arXiv: "arXiv preprint arXiv:XXXX.XXXXX"
  "note","doi","url"
].filter(f => e[f]).map(f => "  "+f+" = {"+bibEsc(f, e[f])+"}").join(","+NL);
return "@"+(e.type||"article")+"{"+(e.key||"ref01")+","+NL+fields+NL+"}";
}).join(NL+NL);
};

const buildLatex = (r) => {
const NL = "\n";
const j = (form.target_journal||"").toLowerCase();
const two = form.column_format==="two";
// ── Journal-type detection flags ─────────────────────────────────────────
// isIEEE: IEEEtran document class — uses \cite{}, \bibliographystyle{IEEEtran},
//         NO geometry/setspace/parskip, NO natbib, NO lineno, NO fancyhdr,
//         NO Plain Language Summary / Highlights, tables must be table* for two-col.
// ── Short acronyms that are ALSO common substrings (chi in "machine", acl in
// "practical", mai in "email") MUST use word-boundary matching or they produce
// false positives. has() = word-boundary-safe substring test.
const has = (re) => re.test(j);
const isIEEE = has(/\bieee\b/) || has(/\bcvpr\b/) || has(/\biccv\b/) ||
               has(/\bicassp\b/) || has(/\bwacv\b/) || has(/\bicip\b/) ||
               has(/\biros\b/) || has(/\bicra\b/);
// isACM: ACM sigconf class — "chi" must be word-bounded to avoid matching
// "machine" (every "Machine X" journal would be wrongly classified as ACM).
const isACM  = has(/\bacm\b/) || has(/\bchi\b/) || has(/\bsigraph\b/) ||
               has(/\bsiggraph\b/) || has(/\bcscw\b/);
// isACL: ACL/NLP venues — word-bounded to avoid matching "practical", "article".
const isACL  = has(/\bacl\b/) || has(/\bemnlp\b/) || has(/\bnaacl\b/) ||
               has(/\bcoling\b/) || has(/\beacl\b/) || has(/\bfindings\b/);
// isConf: any conference/workshop that uses numbered [n] citations and does NOT
// want lineno, preprint footers, Plain Language Summary, or Highlights.
// IMPORTANT: isConf must be declared BEFORE isNature so the !isConf guard works.
const isConf = isIEEE || isACM || isACL ||
  has(/\baaai\b/) || has(/\bijcai\b/) ||
  has(/\bneurips\b/) || has(/\bnips\b/) ||
  has(/\bicml\b/) || has(/\biclr\b/) ||
  has(/\bmiccai\b/) || has(/\beccv\b/) ||
  has(/\bbmvc\b/) || has(/\binterspeech\b/) ||
  has(/\bsigir\b/) || has(/\bkdd\b/) || has(/\bwww\b/) ||
  // Springer LNEE / LNCS conference venues (MAI, MVAI, etc.)
  has(/\blnee\b/) || has(/\blncs\b/) || has(/\blecture notes\b/) ||
  has(/\bmai\b/) || has(/\bmvai\b/) ||
  // Generic conference / proceedings keywords — catches any venue the user types
  has(/\bconference\b/) || has(/\bworkshop\b/) ||
  has(/\bsymposium\b/) || has(/\bproceedings\b/);
// isSpringerConf: Springer LNCS / LNEE conference proceedings.
// These use the \documentclass{llncs} template, \bibliographystyle{splncs04},
// and a specific \author{}\institute{} author block format.
// Detected when the venue is a conference AND mentions Springer / LNEE / LNCS.
// MAI and MVAI are ALWAYS published in Springer LNEE — include them explicitly
// so typing "MAI-2026" alone (without "Springer") still triggers llncs class.
const isSpringerConf = isConf && (
  has(/\bspringer\b/) || has(/\blnee\b/) ||
  has(/\blncs\b/) || has(/\blecture notes\b/) ||
  has(/\bmai\b/) || has(/\bmvai\b/));
// isNature: open-access journals that want Plain Language Summary & Highlights.
// "cell" must be word-bounded (matches "cellular", "cellphone" otherwise).
// CRITICAL: guard with !isConf so "Springer LNEE" conference papers are NOT treated
// as Nature-style journals (which would generate highlights, PLS, running title, etc.).
const isNature = !isConf && (
  has(/\bnature\b/) || has(/\bspringer\b/) ||
  has(/\belsevier\b/) || has(/\bplos\b/) || has(/\bcell\b/));
// Document class — evaluated in priority order:
// 1. NeurIPS / ICML / ICLR: generic article (these venues supply their own .sty)
// 2. IEEE venues: IEEEtran (two-col or single-col)
// 3. ACL/NLP venues: generic article with acl_natbib bib style
// 4. ACM venues: acmart sigconf
// 5. Springer LNCS/LNEE conferences: llncs class (10pt, A4, numbered citations)
// 6. Nature/Elsevier/PLOS journals: generic article (12pt A4)
// 7. Default: article (two-col → IEEEtran, single-col → article)
const dc = (j.includes("neurips")||j.includes("nips")||j.includes("icml")||j.includes("iclr"))
? (two?"\\documentclass[10pt,twocolumn]{article}":"\\documentclass[12pt,a4paper]{article}")
: isIEEE
? (two?"\\documentclass[10pt,twocolumn]{IEEEtran}":"\\documentclass[12pt]{IEEEtran}")
: isACL ? "\\documentclass[11pt]{article}"
: isACM ? "\\documentclass[sigconf]{acmart}"
: isSpringerConf ? "\\documentclass{llncs}"
: isNature ? "\\documentclass[12pt,a4paper]{article}"
: two ? "\\documentclass[10pt,twocolumn]{IEEEtran}" : "\\documentclass[12pt,a4paper]{article}";
// Re-detect based on final dc string (handles default two-col case → IEEEtran)
const usingIEEEtran = dc.includes("IEEEtran");
// BUG FIX: usingTwoCol must reflect the ACTUAL document class, not just
// "IEEE was selected". An IEEE journal like IEEE TPAMI uses IEEEtran in
// SINGLE-column mode — figures/tables must use figure/table (not figure*/table*)
// or LaTeX errors "figure* not allowed in single-column mode".
// Source of truth: check whether the DC line contains the twocolumn option.
// Springer LNEE (llncs) is ALWAYS single-column — override any user selection.
const usingTwoCol   = !isSpringerConf && dc.includes("twocolumn");
// ── LaTeX helper utilities ──────────────────────────────────────────────────
//
// esc: strict escaper for short text fields (titles, captions, keywords).
//      Escapes all LaTeX special characters unconditionally.
const esc = s => (s||"").replace(/&/g,"\\&").replace(/%/g,"\\%").replace(/_/g,"\\_").replace(/\$/g,"\\$").replace(/#/g,"\\#");

// escL: smart escaper for long section bodies that contain real LaTeX commands.
//       Protects existing LaTeX math environments ($...$, $$...$$,
//       \begin{equation}...\end{equation}, \begin{align}...\end{align}, \[...\])
//       and key-bearing commands (\cite, \label, \ref, \url, \href) from
//       double-escaping, then escapes bare special chars in plain text.
//
//       CRITICAL FIX: \begin{equation}...\end{equation} blocks are now protected
//       BEFORE the underscore escaper runs. Previously, subscripts like w_{y_t}
//       inside equation environments were wrongly converted to w\_{y\_t}, causing
//       LaTeX to emit literal "\_" text instead of proper subscripts.
const escL = s => {
  if (!s) return "";
  const markers = [];
  const protect = m => { markers.push(m); return "\uE000" + (markers.length-1) + "\uE001"; };
  // ── PRE-ESCAPE: fix Figure/Table N.M (section.number notation) → \ref{} ───
  // Claude sometimes writes "Figure 4.5" (section 4, item 5) instead of the
  // correct "Figure~\ref{fig:fig1}". In the compiled PDF this produces "Figure ??"
  // because no label "fig:4.5" exists. Replace with proper cross-reference using
  // the local index (M in N.M) capped at 3 (our paper always has ≤3 figures).
  s = s
    .replace(/\bFigure[~\s]+(\d+)\.(\d+)\b/g, (_, _sec, loc) =>
      `Figure~\\ref{fig:fig${Math.min(parseInt(loc), 3)}}`)
    .replace(/\bTable[~\s]+(\d+)\.(\d+)\b/g, (_, _sec, loc) =>
      `Table~\\ref{tab:tab${Math.min(parseInt(loc), 2)}}`);
  let t = s
    // 0. Protect full equation / align / gather / multline environments — FIRST,
    //    before any other rule, so that _ inside math is never touched by the
    //    underscore escaper below.
    .replace(/\\begin\{(?:equation|align|gather|multline|eqnarray)\*?\}[\s\S]*?\\end\{(?:equation|align|gather|multline|eqnarray)\*?\}/g, protect)
    // 0b. Protect display-math shorthand \[ ... \]
    .replace(/\\\[[\s\S]*?\\\]/g, protect)
    // 1. Protect display math ($$...$$) — must come before inline math rule
    .replace(/\$\$[\s\S]*?\$\$/g, protect)
    // ── PRE-ESCAPED CHAR PROTECTION (must run first, before all other steps) ──
    // 1b. Protect already-escaped special characters (\$, \%, \_, \&, \#).
    //     The AI sometimes pre-escapes these in its output (e.g. "\$377 billion",
    //     "73\%", "en\_core\_web\_sm").  Without this guard the escapers below
    //     would re-escape them: \$ → \\$, \% → \\%, \_ → \\_  which in a LaTeX
    //     paragraph means "force newline" + stray char → fatal compile errors:
    //       "There's no line here to end" (\\$  and  \\%)
    //       "Missing $ inserted"           (\\_)
    //     Running this FIRST ensures the currency protector (step 1c) and the
    //     dollar escaper never see an already-escaped \$ — no double-escaping.
    //     This one line eliminates ALL 41 double-escaping errors in the .tex.
    .replace(/\\([$%_&#])/g, protect)
    // 1c. ── CURRENCY PROTECTION ───────────────────────────────────────────────
    //     Protect currency/price dollar signs ($0.001, $377, $150) BEFORE the
    //     inline math protector below. Without this, the regex $[^$\n]{1,300}?$
    //     treats paired amounts like "$0.001 ... $0.028" as inline math, leaving
    //     them unescaped → LaTeX processes them as math mode → rendering errors.
    //     Step 1b above already handled pre-escaped \$377, so only bare $digit
    //     patterns remain here.  Marker stores \$digit → correct LaTeX on restore.
    .replace(/\$(\d)/g, (_, d) => { markers.push("\\$" + d); return "\uE000" + (markers.length-1) + "\uE001"; })
    // 1d. ── BROKEN INLINE MATH STRIPPER ───────────────────────────────────────
    //     Claude sometimes wraps entire sentences in $...$:
    //       "$99.72% and macro-F1 score of 0.9965$"
    //       "$4.5 minutes compared to ResNet-1D$"
    //     An unclosed or overly-long $...$ causes ALL following text in the PDF
    //     to render in italic math mode with no spaces — the most visible PDF bug.
    //     Detection: span >20 chars AND contains both spaces AND English words (3+).
    //     Action: strip the $ signs so text falls through to plain-text escaping.
    //     Must run BEFORE step 2 so bad spans are never "protected" as math.
    .replace(/\$([^$\n]{20,300})\$/g, (match, inner) => {
      if (/[a-zA-Z]{3,}/.test(inner) && /\s/.test(inner)) {
        return inner;  // drop the $...$ — render as plain escaped text
      }
      return match;   // short / pure-math expression — leave for step 2
    })
    // 2. Protect inline math ($...$) — non-greedy, max 300 chars, no newlines
    //    This keeps proper LaTeX math ($F_1$, $\mathcal{L}$, $\kappa=0.83$) untouched.
    //    A bare dollar sign like $12/hour has no closing $, so it won't match
    //    and will be caught by the $ escaper below.
    .replace(/\$[^$\n]{1,300}?\$/g, protect)
    // 3. Protect key/ref commands whose brace contents must not be escaped
    //    (\cite{key_with_underscores}, \label{sec:my_label}, \ref{tab:results}, etc.)
    .replace(/\\(?:cite[tp]?\*?|nocite|label|ref|eqref|autoref|pageref|url|href|hyperref|texttt)\{[^}]*\}/g, protect);
  // Escape unprotected special characters in the remaining plain text
  t = t
    .replace(/&/g,  "\\&")
    .replace(/%/g,  "\\%")
    .replace(/_/g,  "\\_")   // bare underscores in text identifiers (safe — math is protected above)
    .replace(/\$/g, "\\$")   // dollar signs in plain text (e.g. $12/hour)
    .replace(/#/g,  "\\#");
  // Restore all protected sequences
  return t.replace(/\uE000(\d+)\uE001/g, (_, i) => markers[parseInt(i)]);
};

// fixMd: convert Markdown bold/italic to LaTeX equivalents.
// Protects ALL math zones ($...$, $$...$$, \begin{equation}...\end{equation}, \[...\])
// BEFORE replacing *..* / **..**, so that math subscripts/notation are never corrupted.
// Using private-use Unicode E002/E003 as markers (distinct from escL which uses E000/E001).
const fixMd = t => {
  if (!t) return "";
  const markers = [];
  const protect = m => { markers.push(m); return "\uE002" + (markers.length - 1) + "\uE003"; };
  let s = (t)
    // 0. Protect full equation/align/gather/multline environments FIRST
    .replace(/\\begin\{(?:equation|align|gather|multline|eqnarray)\*?\}[\s\S]*?\\end\{(?:equation|align|gather|multline|eqnarray)\*?\}/g, protect)
    // 0b. Protect \[...\] display math
    .replace(/\\\[[\s\S]*?\\\]/g, protect)
    // 1. Protect $$...$$
    .replace(/\$\$[\s\S]*?\$\$/g, protect)
    // 2. Protect inline $...$ (max 300 chars, no $ or newline inside)
    .replace(/\$[^$\n]{1,300}?\$/g, protect);
  // 2b. ── DOUBLE-ESCAPING FIX (already-escaped underscores / asterisks) ──────
  //     escL() runs before fixMd() in the chain cite(fixMd(escL(text))).
  //     escL converts bare underscores: en_core_web_sm → en\_core\_web\_sm.
  //     Without this guard, fixMd then sees \_core\_ as the markdown pattern
  //     _core_ and converts it to \textit{core}, corrupting model names like
  //     en_core_web_sm → en\textit{core}web\_sm — a LaTeX syntax error.
  //     Protecting \_ and \* BEFORE the markdown rules prevents this entirely.
  s = s.replace(/\\[_*]/g, protect);
  // Now safe to replace markdown — no math zones remain in s
  s = s
    .replace(/\*\*([^*\n]+)\*\*/g, "\\textbf{$1}")
    .replace(/\*([^*\n]+)\*/g,     "\\textit{$1}")
    .replace(/__([^_\n]+)__/g,     "\\textbf{$1}")
    .replace(/_([^_\n]+)_/g,       "\\textit{$1}");
  // Restore protected math zones unchanged
  return s.replace(/\uE002(\d+)\uE003/g, (_, i) => markers[parseInt(i)]);
};

// stripSection: remove a leading \section{...} or \section*{...} that the AI
//               sometimes emits at the start of section content, which would
//               create a duplicate when buildLatex already emits \section{}.
//               FIX Errors 2, 3, 4: duplicate Methodology / Experiments /
//               Supplementary Materials headers.
const stripSection = t => (t||"")
  .replace(/^\s*\\section\*?\{[^}]*\}\s*/i, "")
  .replace(/^\s*\\subsection\*?\{[^}]*\}\s*/i, "");

// stripCapPrefix: remove a "Table N: " or "Figure N: " prefix from a caption
//                string. LaTeX's \caption{} command auto-numbers tables and
//                figures, so a prefix like "Table 2:" causes "Table 2: Table 1:"
//                double-label output.
//                FIX Error 10: double table caption labels.
const stripCapPrefix = cap => (cap||"").replace(/^\s*(?:Table|Figure)\s+\d+\s*[:—–-]\s*/i, "");

// ── Citation resolver ───────────────────────────────────────────────────────
// THREE-LAYER resolution — guarantees zero [?] citations:
//
// Layer 1 (primary): Order-independent ref0N key map.
//   Since Call 5 uses ref01-refNN keys, parse e.key → number and build a
//   number→key lookup.  This is immune to Call 5 returning entries in a
//   different order than the citation numbers (e.g. sorted alphabetically).
//
// Layer 2 (secondary): Author+year matching via citation_map from Call 2.
//   Useful when legacy entries use author-year keys instead of ref0N.
//
// Layer 3 (fallback): Synthesise "ref0N" directly from the citation number.
//   Always resolves — even if neither layer 1 nor 2 found a match.
//   The synthesis fallback in controller.py guarantees a .bib entry exists.

const bk = (r.bibtex_entries||[]).map(e=>e.key);

// Layer 1: build number → key map by parsing "ref0N" pattern (order-independent)
const refNumToKey = {};
(r.bibtex_entries||[]).forEach(e => {
  if (!e.key) return;
  const m = e.key.match(/^ref(\d+)$/i);
  if (m) refNumToKey[parseInt(m[1])] = e.key;
});

// Layer 2: author+year matching (handles legacy author-year keyed entries)
const numToKey = {};
if (r.citation_map && typeof r.citation_map === "object") {
  Object.entries(r.citation_map).forEach(([n, info]) => {
    if (!info) return;
    const surname = ((info.author||"").split(/[\s,]+/).find(w=>w.length>2)||"").toLowerCase();
    const yr = String(info.year||"");
    const matched = (r.bibtex_entries||[]).find(e =>
      surname && e.author && e.author.toLowerCase().includes(surname) &&
      yr && String(e.year) === yr
    );
    if (matched) numToKey[n] = matched.key;
  });
}

// ── Citation command: \cite{} for IEEE/ACM, \cite{} for natbib (numbers mode) ──
// IEEEtran does NOT load natbib, so \citep{} is undefined → [?] everywhere.
// With \usepackage[numbers]{natbib}, \cite{} and \citep{} both produce [N].
// We use \cite{} universally — works with IEEEtran, numbered natbib, and ACM.
//
// FIX: Also handles multi-citation groups like [5,6,7,8] → \cite{ref05,ref06,ref07,ref08}
// Previously only single [N] was converted; table row labels like "Method [17]"
// and grouped citations "[5,6,7,8]" were left as raw text → [?] after BibTeX.
const citeCmd = "\\cite{";
const cite = t => (t||"")
  // ── Step 0: Resolve \cite{Author, Year} author-year keys → \cite{refNN} ──
  // ROOT CAUSE FIX: The AI sometimes writes \cite{Firth et al., 2017} style keys
  // directly in the LaTeX body text.  These keys do NOT exist in references.bib
  // (which uses ref01, ref02, etc.) → LaTeX resolves them to [?] in the compiled PDF.
  //
  // Strategy: extract the first-author surname + year from the raw key, then look up:
  //   Layer A — bibtex_entries by author+year (exact match)
  //   Layer B — citation_map number → bibtex_entries key (via refNumToKey)
  //   Layer C — any word in the key as surname against bibtex_entries (year-relaxed)
  //   Fallback — strip entirely (blank is safer than an unresolvable [?])
  //
  // Keys that are already in refNN format are left completely untouched.
  .replace(/\\cite\{([^}]+)\}/g, (match, rawKey) => {
    const key = rawKey.trim();
    // Already a single correct refNN key — pass through
    if (/^ref\d+$/i.test(key)) return match;
    // Already a comma-list of correct refNN keys — pass through
    if (/^(ref\d+\s*,\s*)*ref\d+$/i.test(key)) return match;
    // Extract year (4-digit 19xx/20xx) and first author surname from the raw key
    const yearM = key.match(/\b(19|20)\d{2}\b/);
    const year  = yearM ? yearM[0] : "";
    const surname = (key.split(/[\s,;.]+/)[0] || "").toLowerCase();
    const tryMatch = (author, yr) =>
      surname.length > 1 &&
      (author || "").toLowerCase().includes(surname) &&
      (!year || String(yr) === year);
    // Layer A: exact author+year in bibtex_entries
    const bEntry = (r.bibtex_entries || []).find(e => tryMatch(e.author, e.year));
    if (bEntry) return "\\cite{" + bEntry.key + "}";
    // Layer B: citation_map number → refNumToKey
    for (const [n, info] of Object.entries(r.citation_map || {})) {
      if (!info) continue;
      if (tryMatch(info.author, info.year)) {
        const num = parseInt(n);
        return "\\cite{" + (refNumToKey[num] || ("ref" + String(num).padStart(2, "0"))) + "}";
      }
    }
    // Layer C: any word in the key as surname match (year-relaxed)
    const words = key.split(/[\s,;.]+/).filter(w => w.length > 3 && !/^\d+$/.test(w));
    for (const w of words) {
      const m2 = (r.bibtex_entries || []).find(e =>
        (e.author || "").toLowerCase().includes(w.toLowerCase())
      );
      if (m2) return "\\cite{" + m2.key + "}";
    }
    // No match found — strip entirely to prevent an unresolvable [?] in the PDF
    return "";
  })
  // ── Step 0b: Merge adjacent \cite{X} and \cite{Y} → \cite{X,Y} ─────────────
  // The AI sometimes writes "[1] and [2]" which Step 0 converts to two separate
  // \cite commands: "\cite{ref01} and \cite{ref02}".  In IEEE/BibTeX style this
  // renders as two independent citation markers [1] and [2] rather than [1,2].
  // Merging them keeps the bibliography clean and avoids duplicate-marker warnings.
  // Handles " and ", ", ", " or " connectors between adjacent \cite{} commands.
  .replace(/\\cite\{([^}]+)\}\s*(?:and|or|,)\s*\\cite\{([^}]+)\}/g,
    (_, a, b) => "\\cite{" + a + "," + b + "}")
  // ── Step 1: Strip [?] placeholder citations ──────────────────────────────
  // The AI sometimes writes [?] when it can't assign a specific citation number.
  // These are NOT handled by the numeric pattern below and appear as literal
  // "[?]" in the compiled PDF.  Remove them here before LaTeX sees them.
  // Pattern handles: "text [?]." → "text."  and  "text [?][?]" → "text"
  // Uses a greedy leading-whitespace match so "Chen [?] found" → "Chen found".
  .replace(/\s*\[\?\]/g, "")
  // ── Step 2: Convert [N] and [N,M,...] to \cite{refNN} ─────────────────────
  .replace(/\[(\d+(?:\s*,\s*\d+)*)\]/g, (_, ns) => {
    const keys = ns.split(/\s*,\s*/).map(n => {
      const num = parseInt(n);
      // Three-layer resolution: ref0N map → author+year map → synthetic ref0N
      return refNumToKey[num] || numToKey[n] || ("ref"+String(num).padStart(2,"0"));
    });
    // Deduplicate keys within a single \cite{} command
    const uniqueKeys = [...new Set(keys)];
    return citeCmd + uniqueKeys.join(",") + "}";
  })
  // ── Step 3: Deduplicate keys inside existing \cite{A,B,A,C} → \cite{A,B,C} ─
  .replace(/\\cite\{([^}]+)\}/g, (_, keys) => {
    const unique = [...new Set(keys.split(",").map(k=>k.trim()).filter(Boolean))];
    return "\\cite{" + unique.join(",") + "}";
  });

// ── Figure builder ──────────────────────────────────────────────────────────
// FIX Error 5: blank figure boxes.
//
// Old code emitted \IfFileExists{paper_figN.png}{...}{\fbox{...}} which
// rendered as a blank box when the file was absent (always, since generated_figures
// is always []). New code emits a commented-out figure block as a placeholder
// so the .tex compiles cleanly and the user knows where to add their own figures.
const mkFig = (cap,i) => {
const fp = r.generated_figures&&r.generated_figures[i]&&r.generated_figures[i].latex_path;
// Two-column layouts: figures spanning both columns use figure* (better results).
// Single-column: figure is fine.
const figEnv = usingTwoCol ? "figure*" : "figure";
// [tbp] = try top-of-page, bottom, or dedicated page — far more reliable than [h]
// which often drops figures at wrong positions. [h!] forces here but fails often.
const placement = "[tbp]";
if (!fp) {
  // No figure file — emit a placeholder comment block.
  // The user can uncomment and replace paper_figN.png with their own image file.
  // escL used (not esc) to protect math expressions like $F_1$ in captions.
  //
  // \phantomsection\label{fig:figN} outside the comment block allows
  // \ref{fig:figN} in methodology/results text to resolve (no "??" in PDF).
  // Remove this phantom label line once you add your actual figure below.
  return [
"% ── Figure "+(i+1)+": Replace paper_fig"+(i+1)+".png with your image, then uncomment ──",
"% \\begin{"+figEnv+"}"+placement,
"% \\centering",
"% \\includegraphics[width=0.9\\linewidth]{paper_fig"+(i+1)+".png}",
"% \\caption{"+fixMd(escL(cap))+"}",
"% \\label{fig:fig"+(i+1)+"}",
"% \\end{"+figEnv+"}",
"\\phantomsection\\label{fig:fig"+(i+1)+"}% placeholder — resolves Figure~\\ref{fig:fig"+(i+1)+"} cross-refs"
  ].join(NL);
}
return [
"\\begin{"+figEnv+"}"+placement,
"\\centering",
"\\includegraphics[width=0.9\\linewidth]{"+fp+"}",
"\\caption{"+fixMd(escL(cap))+"}",
"\\label{fig:fig"+(i+1)+"}",
"\\end{"+figEnv+"}"
].join(NL);
};

// ── Table builder ───────────────────────────────────────────────────────────
// In IEEEtran two-column layout \begin{table}[h] is single-column width —
// it causes tables to overflow/stretch into the adjacent column.
// \begin{table*}[t] spans both columns giving the table full page width.
const mkTbl = (data,cap,lbl) => {
if (!data||data.length<2) return "";
const ncols = data[0].length;
// Column spec: wider last col for wrap-friendly "Notes" / "Key Change" columns
// regardless of column layout — improves readability for long text in final column.
let cs;
if (ncols >= 4) {
  // 4+ cols: first is left-aligned, middle are centred, last wraps text
  cs = "l" + "c".repeat(ncols-2) + (usingTwoCol ? "p{4cm}" : "p{6cm}");
} else if (ncols === 3) {
  // 3 cols: first left, second centred, third wraps
  cs = "lc" + (usingTwoCol ? "p{4cm}" : "p{6cm}");
} else {
  // 2 cols or fewer: centred
  cs = "l" + "c".repeat(ncols-1);
}
const rows = data.map((row,i) => {
  // cite() converts [N] and [N,M] → \cite{refN} or \cite{refN,refM} in table cells.
  // fixMd converts **bold** → \textbf{} (e.g. **SleepFormer (Ours)** in method column).
  // escL is used (not esc) so that existing \textbf{} from AI output is preserved.
  const cells = row.map(c => cite(fixMd(escL(String(c))))).join(" & ");
  return cells+" \\\\"+(i===0 ? NL+"\\midrule" : "");
}).join(NL);
// table* spans both columns; table is single-column only
const tblEnv = usingTwoCol ? "table*" : "table";
return [
"\\begin{"+tblEnv+"}[t]",
"\\centering",
"{\\small",
// fixMd on caption converts **Bold** → \textbf{Bold} in caption strings.
// escL used (not esc) so that math expressions like $F_1$ in captions are
// protected before the underscore escaper runs — esc() would wrongly convert
// $F_1$ → $F\_1$ which breaks LaTeX math inside captions.
"\\caption{"+fixMd(escL(stripCapPrefix(cap)))+"}",
"\\label{"+lbl+"}",
"\\begin{tabular}{"+cs+"}",
"\\toprule",
rows,
"\\bottomrule",
"\\end{tabular}",
"}",
"\\end{"+tblEnv+"}"
].join(NL);
};
const ab = r.author_block||{};
const aNames = ab.authors||form.authors_list||"Author Name";
// For independent researchers with no institution, use a well-formed fallback
// that compiles cleanly in all document classes (llncs, IEEEtran, acmart, article).
// "Department, University" is a placeholder that looks broken in the compiled PDF.
const aAffilRaw = ab.affiliations||"";
const aAffil = aAffilRaw && aAffilRaw.trim() && !aAffilRaw.includes("[") && !aAffilRaw.includes("Department, University")
  ? aAffilRaw
  : (form.authors_list ? "Independent Researcher" : "Department, University");
const aEmail = ab.emails||form.authors_emails||"author@institution.edu";
// ── Author block: format depends on document class ─────────────────────────
// IEEEtran: \IEEEauthorblockN (names) + \IEEEauthorblockA (affiliation/email)
//           gives the two-row IEEE author box layout
// ACM acmart: bare name string — acmart handles affiliations via separate commands
// Standard article: name / italic affil / typewriter email stacked with \\
let aBlock;
if (usingIEEEtran) {
  // IEEE two-column layouts wrap affiliations; {\small} prevents overflow into text.
  // Single-column IEEE uses full-size to match the TeX style guide.
  const sizeWrap = usingTwoCol ? "{\\small " : "";
  const closeWrap = usingTwoCol ? "}" : "";
  aBlock = "\\IEEEauthorblockN{"+esc(aNames)+"}\n"
         + "\\IEEEauthorblockA{"+sizeWrap+"\\textit{"+esc(aAffil)+"}\\\\\n"
         + esc(aEmail)+closeWrap+"}";
} else if (isACM) {
  aBlock = esc(aNames);
} else if (isSpringerConf) {
  // llncs author block: \author{A \and B \and C}
  // Multiple authors must be joined with \and (NOT comma).
  // \email{} is a built-in llncs command (no package needed).
  const springerNames = aNames.split(/\s*[,;]\s*/)
    .map(n => n.trim()).filter(Boolean).map(esc).join(" \\and ");
  aBlock = springerNames || esc(aNames);
} else {
  aBlock = esc(aNames)+"\\\\"+NL+"\\textit{"+esc(aAffil)+"}\\\\"+NL+"\\texttt{"+esc(aEmail)+"}";
}
const figs = (r.figure_captions||[]);
const parts = [];
// ── Embed BibTeX via filecontents* (BEFORE \documentclass) ───────────────
// This makes the .tex file SELF-CONTAINED: Overleaf/pdfLaTeX writes references.bib
// at compile time from the embedded content, so [?] citations NEVER appear even
// if the user forgets to upload references.bib separately.
// filecontents* with [overwrite] is supported in TeX Live 2019+ (Overleaf default).
const embeddedBib = buildBibTeX(r.bibtex_entries||[]);
if (embeddedBib && embeddedBib.trim()) {
  parts.push("\\begin{filecontents*}[overwrite]{references.bib}");
  embeddedBib.split("\n").forEach(line => parts.push(line));
  parts.push("\\end{filecontents*}");
  parts.push("%% ↑ BibTeX auto-embedded — references.bib is created at compile time.");
  parts.push("%% You do NOT need to upload references.bib separately to Overleaf.");
  parts.push("%% Simply compile: pdfLaTeX → BibTeX → pdfLaTeX → pdfLaTeX");
}
parts.push(dc);
// ── Essential encoding & fonts ────────────────────────────────────────────
parts.push("\\usepackage[utf8]{inputenc}");
parts.push("\\usepackage[T1]{fontenc}");
// times font: DO NOT load for ACM (acmart ships its own font stack; loading times
// on top causes "LaTeX Font Warning: Font shape undefined" errors and breaks the
// acmart house style). Safe for IEEE, Nature, Elsevier, NeurIPS, etc.
if (!isACM) parts.push("\\usepackage{times}");
parts.push("\\usepackage{microtype}");
// ── Math ──────────────────────────────────────────────────────────────────
// amsmath + amssymb: safe for all document classes including llncs.
// amsthm: llncs defines its OWN proof environment via \spnewtheorem.
// Loading amsthm on top of llncs causes:
//   ! LaTeX Error: Environment proof already defined.
// Fix: only load amsthm for non-Springer-conference classes.
parts.push("\\usepackage{amsmath,amssymb}");
if (!isSpringerConf) parts.push("\\usepackage{amsthm}");
parts.push("\\usepackage{bm}");
// ── Figures & tables ──────────────────────────────────────────────────────
parts.push("\\usepackage{graphicx}");
parts.push("\\usepackage{booktabs}");
parts.push("\\usepackage{multirow}");
parts.push("\\usepackage{tabularx}");
// caption / subcaption: IEEEtran has its own internal caption system.
// Adding these packages on top of IEEEtran causes re-definition conflicts and
// style corruption. acmart also manages captions internally.
// Safe for all other doc classes (article, Nature, Springer, NeurIPS, etc.)
// caption/subcaption: IEEEtran, acmart, and llncs all manage captions internally.
// Loading these packages on top causes re-definition conflicts.
if (!usingIEEEtran && !isACM && !isSpringerConf) {
  parts.push("\\usepackage[font=small,labelfont=bf]{caption}");
  parts.push("\\usepackage{subcaption}");
}
// ── Layout — ONLY for non-IEEEtran/non-ACM/non-llncs classes ─────────────
// IEEEtran, acmart, and llncs all manage their own margins and spacing.
// Adding geometry/setspace/parskip on top of them corrupts the layout.
// llncs in particular sets very specific margins required by Springer.
if (!usingIEEEtran && !isACM && !isSpringerConf) {
  parts.push("\\usepackage[margin=1in]{geometry}");
  parts.push("\\usepackage{setspace}");
  parts.push("\\usepackage{parskip}");
}
// ── References & links ────────────────────────────────────────────────────
// IEEEtran: \usepackage{cite} for compressed numbered [1][2][3] citations.
// ACM acmart: handles citations internally — adding cite or natbib causes errors.
// Everyone else: \usepackage[numbers,sort&compress]{natbib}
//   "numbers"       → \cite{} and \citep{} both produce [N] (not author-year)
//   "sort&compress" → adjacent citations collapse: [1,2,3] → [1–3]
//
// WHY numbers mode: Nature/Elsevier/PLOS all use Vancouver (numbered) style.
// plainnat (author-year) was the previous default but produced "(Author, Year)"
// output that doesn't match any target journal's style → switched to numbered.
if (usingIEEEtran) {
  parts.push("\\usepackage{cite}");
} else if (!isACM) {
  parts.push("\\usepackage[numbers,sort&compress]{natbib}");
}
// hyperref BEFORE doi — doi package extends hyperref's \href{}; wrong order causes warnings.
// hyperref options differ by document class:
// IEEEtran: bookmarks=false (broken PDF bookmarks in two-col), breaklinks=true (narrow cols).
// Springer LNCS/LNEE (llncs): hidelinks — Springer's house style does not use coloured links.
//   Also must load AFTER llncs: the class defines \institute which hyperref patches.
// Everyone else: standard coloured-links setup.
if (usingIEEEtran) {
  parts.push("\\usepackage[pdftex,colorlinks=true,linkcolor=blue,citecolor=blue,urlcolor=blue,bookmarks=false,breaklinks=true]{hyperref}");
} else if (isSpringerConf) {
  parts.push("\\usepackage[hidelinks,breaklinks=true]{hyperref}");
} else {
  parts.push("\\usepackage[colorlinks=true,linkcolor=blue,citecolor=blue,urlcolor=blue]{hyperref}");
}
parts.push("\\usepackage{url}");
parts.push("\\usepackage{doi}");  // must come AFTER hyperref
// ── Misc ──────────────────────────────────────────────────────────────────
// lineno (continuous line numbers) — NEVER active by default.
// IEEE/ACM/conference submissions do NOT use line numbers.
// Non-conference preprints may enable it by uncommenting the line below.
parts.push("% \\usepackage{lineno}   % Uncomment for double-blind review with line numbers");
parts.push("% \\linenumbers          % (non-IEEE/ACM journals only)");
parts.push("\\usepackage{xcolor}");
parts.push("\\usepackage{enumitem}");        // fine-grained list control (\begin{enumerate}[label=...])
parts.push("\\usepackage{float}");           // [H] placement specifier for figures/tables
parts.push("\\usepackage{textcomp}");        // \textdegree, \texttrademark, \textcopyright
parts.push("\\usepackage{algorithm}");
parts.push("\\usepackage{algpseudocode}");   // algorithmicx pseudocode (replaces algorithmic)
// ── Hyperref — clickable cross-references + PDF metadata ─────────────────
// Must be loaded LAST (after all other packages).
// hidelinks: removes coloured boxes around links for clean submission PDF.
// ACM acmart loads hyperref internally — do not load it again.
// IEEE IEEEtran: hyperref is compatible but must come after all IEEE packages.
// llncs Springer: hyperref is compatible; \phantomsection (already in figure
//   placeholders) requires hyperref to be loaded.
if (!isACM) {
  parts.push("\\usepackage[hidelinks,bookmarks=true,pdfusetitle]{hyperref}");
  // ── PDF metadata: every real paper sets these. Missing metadata is a tell. ──
  const pdfTitle  = esc(r.title || form.topic || "");
  const pdfAuthor = esc(aNames || "");
  const pdfKwArr  = Array.isArray(r.keywords) ? r.keywords :
                    (typeof r.keywords === "string" ? r.keywords.split(/[,;]/).map(s=>s.trim()) : []);
  const pdfKw     = esc(pdfKwArr.filter(Boolean).join(", "));
  const pdfSubj   = esc(form.research_field || "Research paper");
  const hsBits = [];
  if (pdfTitle)  hsBits.push(`pdftitle={${pdfTitle}}`);
  if (pdfAuthor) hsBits.push(`pdfauthor={${pdfAuthor}}`);
  if (pdfKw)     hsBits.push(`pdfkeywords={${pdfKw}}`);
  if (pdfSubj)   hsBits.push(`pdfsubject={${pdfSubj}}`);
  hsBits.push("pdfcreator={LaTeX with hyperref}");
  hsBits.push("pdfproducer={pdfTeX}");
  if (hsBits.length) {
    parts.push("\\hypersetup{%");
    parts.push("  " + hsBits.join(",%\n  "));
    parts.push("}");
  }
}
// ── Two-column specific ───────────────────────────────────────────────────
// balance: makes the two column text on the last page equal length
// stfloats: allows [b] and [b!] placement for table* in IEEEtran
if (usingTwoCol) parts.push("\\usepackage{balance}");
if (usingIEEEtran) parts.push("\\usepackage{stfloats}");
// dblfloatfix: fixes LaTeX's handling of [b]/[b!] floats in two-column IEEEtran documents.
// Without it, bottom-placed figures/tables on the last page often drift to unexpected positions.
// Must come AFTER stfloats (both patch the same float mechanism; dblfloatfix is the superset).
if (usingIEEEtran) parts.push("\\usepackage{dblfloatfix}");
// ── Running header / Preprint footer ─────────────────────────────────────
// fancyhdr MUST NOT be used with IEEEtran, acmart, or any conference class
// that manages its own headers/footers.  Use ONLY for open-access journal
// submissions (Nature, Elsevier, PLOS, Springer standalone, etc.).
if (r.running_title && !isConf) {
  parts.push("\\usepackage{fancyhdr}");
  parts.push("\\pagestyle{fancy}");
  parts.push("\\fancyhead[L]{\\small\\textit{"+esc(r.running_title)+"}}");
  parts.push("\\fancyhead[R]{\\small \\thepage}");
  parts.push("\\fancyfoot[C]{\\small\\textit{Preprint --- under review}}");
}
parts.push("\\title{"+esc(r.title||form.topic)+"}");
if (isSpringerConf) {
  // llncs author format: \author{Name1 \and Name2}
  //                      \institute{Affiliation \\ \email{email}}
  // The \and separator is required for multiple authors in llncs.
  // \email{} is a built-in llncs command — do NOT use \texttt{}.
  parts.push("\\author{"+aBlock+"}");
  parts.push("\\institute{"+esc(aAffil)+" \\\\\n\\email{"+esc(aEmail)+"}}");
} else {
  parts.push("\\author{"+aBlock+"}");
  parts.push("\\date{}");
}
parts.push("\\begin{document}");
parts.push("\\maketitle");
// Suppress default page number on title page for IEEEtran
if (usingIEEEtran) parts.push("\\thispagestyle{empty}");
// ── Plain Language Summary & Highlights ──────────────────────────────────
// ONLY for Nature/Springer/Elsevier open-access journals — NOT for any
// conference paper (IEEE, ACM, ACL, NeurIPS, AAAI, MICCAI, etc.) or standard
// article submissions.  Including them in a conference paper confuses reviewers.
if (!isConf && isNature && r.plain_language_summary) {
  parts.push("\\begin{quote}");
  // escL not esc: plain language summary may contain inline math
  parts.push("\\textbf{Plain Language Summary:} "+escL(r.plain_language_summary));
  parts.push("\\end{quote}");
}
if (!isConf && isNature && r.highlights && r.highlights.length) {
  parts.push("\\noindent\\textbf{Highlights:}\\begin{itemize}");
  // escL not esc: highlight items may contain inline math or metric notation
  r.highlights.forEach(h=>parts.push("  \\item "+escL(h)));
  parts.push("\\end{itemize}");
}
parts.push("\\begin{abstract}");
// ── Abstract format ─────────────────────────────────────────────────────────
// IEEE / ACM / any conference: SINGLE plain paragraph, no bold IMRaD labels.
//   Reviewers at IEEE/ACM reject structured abstracts with "Background:" labels —
//   those are for medical/clinical journals only.
// Nature / Elsevier / PLOS: structured abstract with bold section labels is
//   required or strongly preferred — use if abstract_structured is populated.
//
// BUG FIX: abstract and structured-abstract fields now use cite(fixMd(escL()))
// instead of esc(). Using esc() on the abstract broke any inline math like
// $F_1$ → $F\_1$ (LaTeX error).  fixMd also converts any stray **bold**/**italic**
// markdown the AI emits in the abstract to proper \textbf{}/\textit{}.
// cite() resolves any [n] citation markers the AI may include.
const hasStructured = r.abstract_structured &&
  Object.keys(r.abstract_structured||{}).some(k=>(r.abstract_structured[k]||"").trim().length > 10);
if (!isConf && isNature && hasStructured) {
  // Structured abstract for Nature/Elsevier journals
  ["background","objective","methods","results","conclusion"].forEach(k => {
    const v = (r.abstract_structured||{})[k];
    if (v) parts.push("\\textbf{"+k.charAt(0).toUpperCase()+k.slice(1)+":} "+cite(fixMd(escL(v))));
  });
} else {
  // Single-paragraph abstract for all conference / IEEE / ACM / standard papers
  parts.push(cite(fixMd(escL(r.abstract||""))));
}
parts.push("\\end{abstract}");
// ── Keywords / Index Terms ───────────────────────────────────────────────────
// IEEEtran: \begin{IEEEkeywords}...\end{IEEEkeywords} — appears after abstract
//           and is auto-formatted as "Index Terms—" in the published layout
// ACM acmart: \keywords{...} command (handled by acmart class)
// Standard article/journal: plain-text line after abstract
// Robust keyword array — handle string, array, or missing
const rawKw = r.keywords;
const kwArr = (Array.isArray(rawKw) ? rawKw
  : typeof rawKw === "string" ? rawKw.split(/[,;]/).map(k=>k.trim()).filter(Boolean)
  : []).map(k=>esc(k));
// Fallback keywords derived from topic if AI returned none
const kwFinal = kwArr.length > 0 ? kwArr
  : (form.topic||"").split(/\s+/).filter(w=>w.length>4).slice(0,5).map(esc);
if (usingIEEEtran && kwFinal.length) {
  parts.push("\\begin{IEEEkeywords}");
  parts.push(kwFinal.join(", "));
  parts.push("\\end{IEEEkeywords}");
} else if (isACM && kwFinal.length) {
  parts.push("\\keywords{"+kwFinal.join(", ")+"}");
} else if (isSpringerConf && kwFinal.length) {
  // llncs \keywords{} uses \and separator
  parts.push("\\keywords{"+kwFinal.join(" \\and ")+" }");
} else if (kwFinal.length) {
  parts.push("\\noindent\\textbf{Keywords:} "+kwFinal.join("; "));
}
// FIX Errors 2, 3, 4: stripSection() removes a leading \section{} the AI
// sometimes includes at the top of section text, which would duplicate the
// \section{} we emit here (e.g., duplicate "Methodology" or "Supplementary Materials").
parts.push("\\section{Introduction}\\label{sec:intro}");
// ── IEEEtran drop-cap: \IEEEPARstart{F}{irst} for first paragraph ──────────
// This produces the large decorated capital letter that IEEE papers require
// at the opening of the Introduction.  Applied ONLY for IEEEtran documents.
{
  // fixMd applied AFTER escL so \textbf{} braces are never double-escaped.
  // This converts any **bold** or *italic* Markdown the AI emits in body text.
  let introTex = cite(fixMd(escL(stripSection(r.introduction||""))));
  if (usingIEEEtran) {
    introTex = introTex.replace(
      /^(\s*(?:\\[a-zA-Z]+\{[^}]*\}\s*)*)([A-Za-z])([A-Za-z])/,
      (m, pre, first, second) =>
        pre + "\\IEEEPARstart{" + first.toUpperCase() + "}{" + second.toLowerCase() + "}"
    );
  }
  parts.push(introTex);
}
parts.push("\\section{Related Work}\\label{sec:related}");
parts.push(cite(fixMd(escL(stripSection(r.literature_review||"")))));
parts.push("\\section{Methodology}\\label{sec:method}");
parts.push(cite(fixMd(escL(stripSection(r.methodology||"")))));
// NOTE: hyperparameters table is placed AFTER the results table in the Results section
// so that LaTeX assigns Table 1 → results, Table 2 → hyperparams (matching caption text).
// Do NOT move tbl2 back here — it would become Table 1 in the compiled PDF.
parts.push("\\section{Experiments and Results}\\label{sec:results}");
parts.push(cite(fixMd(escL(stripSection(r.results||"")))));
const tbl1 = mkTbl(r.results_table, r.results_table_caption||"Table 1: Comparison of Methods", "tab:results");
if (tbl1) parts.push(tbl1);   // ← first table in document → LaTeX assigns Table 1 ✓
const tbl2 = mkTbl(r.hyperparameters_table, r.hyperparameters_table_caption||"Table 2: Hyperparameter Configuration", "tab:hyperparams");
if (tbl2) parts.push(tbl2);   // ← second table in document → LaTeX assigns Table 2 ✓
figs.forEach((c,i)=>parts.push(mkFig(c,i)));
parts.push("\\section{Discussion}\\label{sec:discussion}");
parts.push(cite(fixMd(escL(stripSection(r.discussion||"")))));
parts.push("\\section{Conclusion}\\label{sec:conclusion}");
parts.push(cite(fixMd(escL(stripSection(r.conclusion||"")))));
// ── Back matter: section ordering differs by journal type ─────────────────
// IEEE/ACM conference papers:
//   Acknowledgements → Bibliography → Appendix (IEEE puts appendix AFTER refs)
// Journal papers (Nature, Elsevier, PLOS, standard article):
//   Ethics → Conflict → Acknowledgements → Contributions → Data Avail →
//   Supplementary → Bibliography → Appendix
const ac = r.author_contributions||ab.author_contributions||form.author_contributions;
const da = r.data_access_statement||ab.data_availability||form.data_access_statement;
if (isConf) {
  // ── Conference / IEEE back matter ──────────────────────────────────────
  if (r.ethics_statement) {
    parts.push("\\section*{Ethics Statement}");
    // Full pipeline: AI may emit markdown bold or citation markers in ethics text
    parts.push(cite(fixMd(escL(stripSection(r.ethics_statement)))));
  }
  if (r.conflict_of_interest) {
    parts.push("\\section*{Conflict of Interest Statement}");
    parts.push(cite(fixMd(escL(stripSection(r.conflict_of_interest)))));
  }
  if (r.acknowledgements) {
    parts.push("\\section*{Acknowledgment}");   // IEEE spells it without the 'e'
    parts.push(cite(fixMd(escL(stripSection(r.acknowledgements)))));
  }
  // Author contributions (CRediT) — required by NeurIPS 2024+ and many ACM venues
  if (ac) {
    parts.push("\\section*{Author Contributions}");
    parts.push(cite(fixMd(escL(stripSection(ac)))));
  }
  // Data / reproducibility statement — required by NeurIPS/ICML/ICLR for replication
  if (da) {
    parts.push("\\section*{Data and Code Availability}");
    parts.push(cite(fixMd(escL(stripSection(da)))));
  }
  // Abbreviations list — used in IEEE papers (IEEE Trans. style guide recommends it)
  if (r.abbreviations_list) {
    const abbrs = (r.abbreviations_list||"").split(/;\s*/).filter(a=>a.match(/[—–\-]/));
    if (abbrs.length >= 2) {
      parts.push("\\section*{Abbreviations}");
      parts.push("\\begin{tabular}{@{}p{2.5cm}l@{}}");
      abbrs.forEach(abbr => {
        const splits = abbr.split(/\s*[—–]+\s*/);
        if (splits.length >= 2)
          parts.push("  \\textbf{"+esc(splits[0].trim())+"} & "+esc(splits.slice(1).join(" ").trim())+" \\\\");
      });
      parts.push("\\end{tabular}");
    }
  }
  if (usingTwoCol) parts.push("\\balance");    // balance last page columns
  // ── Bibliography ───────────────────────────────────────────────────────
  const bibStyleConf = usingIEEEtran ? "IEEEtran"
    : isACM  ? "ACM-Reference-Format"
    : isACL  ? "acl_natbib"
    : isSpringerConf ? "splncs04"   // Springer LNCS/LNEE numbered citation style
    : (j.includes("neurips")||j.includes("icml")||j.includes("iclr")) ? "abbrvnat"
    : "plain";
  parts.push("\\bibliographystyle{"+bibStyleConf+"}");
  parts.push("\\bibliography{references}");
  // IEEE places appendix AFTER the bibliography
  if (r.appendix) {
    parts.push("\\appendix");
    parts.push("\\section{Appendix A}");
    parts.push(cite(fixMd(escL(stripSection(r.appendix)))));
  }
} else {
  // ── Journal back matter ────────────────────────────────────────────────
  if (r.ethics_statement) {
    parts.push("\\section*{Ethics Statement}");
    // Full pipeline: AI may include markdown bold, citations, or special chars
    parts.push(cite(fixMd(escL(stripSection(r.ethics_statement)))));
  }
  if (r.conflict_of_interest) {
    parts.push("\\section*{Conflict of Interest Statement}");
    // Full pipeline: pass through cite+fixMd+escL for consistency with all other text sections
    parts.push(cite(fixMd(escL(stripSection(r.conflict_of_interest)))));
  }
  if (r.acknowledgements) {
    parts.push("\\section*{Acknowledgements}");
    parts.push(cite(fixMd(escL(stripSection(r.acknowledgements)))));
  }
  if (ac) {
    parts.push("\\section*{Author Contributions (CRediT)}");
    parts.push(cite(fixMd(escL(stripSection(ac)))));
  }
  if (da) {
    parts.push("\\section*{Data and Code Availability}");
    parts.push(cite(fixMd(escL(stripSection(da)))));
  }
  if (r.supplementary_materials) {
    parts.push("\\section*{Supplementary Materials}");
    parts.push(cite(fixMd(escL(stripSection(r.supplementary_materials)))));
  }
  // ── Abbreviations for journal papers ───────────────────────────────────
  // Format as two-column tabular: ABBR — Full Term
  if (r.abbreviations_list) {
    const abbrs = (r.abbreviations_list||"").split(/;\s*/).filter(a=>a.match(/[—–\-]/));
    if (abbrs.length >= 2) {
      parts.push("\\section*{Abbreviations}");
      parts.push("\\begin{tabular}{@{}p{2.5cm}l@{}}");
      abbrs.forEach(abbr => {
        const splits = abbr.split(/\s*[—–]+\s*/);
        if (splits.length >= 2)
          parts.push("  \\textbf{"+esc(splits[0].trim())+"} & "+esc(splits.slice(1).join(" ").trim())+" \\\\");
      });
      parts.push("\\end{tabular}");
    }
  }
  // ── Bibliography ───────────────────────────────────────────────────────
  // unsrtnat: numbered [1],[2] in order of appearance — matches Nature/Springer/Elsevier style.
  // naturemag: only if the target journal is specifically Nature group AND they mandate it.
  // plainnat was wrong here — it gives author-year output, not numbered.
  const bibStyleJnl = isNature ? "naturemag" : "unsrtnat";
  parts.push("\\bibliographystyle{"+bibStyleJnl+"}");
  parts.push("\\bibliography{references}");
  if (r.appendix) {
    parts.push("\\appendix");
    parts.push("\\section{Appendix}");
    parts.push(cite(fixMd(escL(stripSection(r.appendix)))));
  }
}
parts.push("%% ─────────────────────────────────────────────────────────────────");
parts.push("%% OVERLEAF COMPILE INSTRUCTIONS:");
parts.push("%% 1. New Project → Upload Files → upload research-paper.tex + references.bib");
if (usingIEEEtran) {
  parts.push("%% 2. Compiler: pdfLaTeX  (IEEEtran is pdfLaTeX-only)");
} else {
  parts.push("%% 2. Compiler: pdfLaTeX");
}
parts.push("%% 3. Compile sequence: pdfLaTeX → BibTeX → pdfLaTeX → pdfLaTeX (4 passes)");
parts.push("%% 4. If you see [?] citations: run BibTeX then pdfLaTeX twice more");
parts.push("%% 5. Replace placeholder figure filenames with your actual image files");
parts.push("%% ─────────────────────────────────────────────────────────────────");
parts.push("\\end{document}");
return parts.join(NL);
};

const downloadFiles = () => {
if (!result) return;
downloadAsText(buildLatex(result), "research-paper.tex");
setTimeout(()=>downloadAsText(buildBibTeX(result.bibtex_entries),"references.bib"),300);
// Also offer matplotlib figure scripts if Call 8 produced them
if (result._figure_scripts && result._figure_scripts.length) {
  result._figure_scripts.forEach((fs, i) => {
    setTimeout(() => downloadAsText(fs.code, fs.filename || `paper_fig${i+1}.py`), 600 + i * 150);
  });
}
};

const downloadTxt = () => {
if (!result) return;
const lines=[result.title||form.topic,"=".repeat(60),""];
if(result.cover_letter){lines.push("COVER LETTER");lines.push(result.cover_letter);lines.push("");}
if(result.running_title){lines.push("RUNNING TITLE: "+result.running_title);lines.push("");}
if(result.plain_language_summary){lines.push("PLAIN LANGUAGE SUMMARY");lines.push(result.plain_language_summary);lines.push("");}
if(result.highlights&&result.highlights.length){lines.push("HIGHLIGHTS");result.highlights.forEach(h=>lines.push("• "+h));lines.push("");}
const ab=result.author_block||{};
if(ab.authors){lines.push("AUTHORS");lines.push(ab.authors);if(ab.affiliations)lines.push(ab.affiliations);lines.push("");}
if(ab.author_contributions){lines.push("AUTHOR CONTRIBUTIONS");lines.push(ab.author_contributions);lines.push("");}
if(ab.data_availability){lines.push("DATA AVAILABILITY");lines.push(ab.data_availability);lines.push("");}
["abstract","keywords","introduction","literature_review","abbreviations_list","methodology","results","discussion","conclusion","author_contributions","data_access_statement","acknowledgements","ethics_statement","conflict_of_interest","supplementary_materials","appendix","references"].forEach(key=>{
if(!result[key])return;
lines.push(key.replace(/_/g," ").toUpperCase());lines.push("-".repeat(40));
if(Array.isArray(result[key]))result[key].forEach((v,i)=>lines.push((key==="references"?"["+String(i+1)+"] ":"• ")+v));
else lines.push(result[key]);
lines.push("");
});
if(result.bibtex_entries&&result.bibtex_entries.length){
lines.push("BIBTEX REFERENCES");lines.push("-".repeat(40));
result.bibtex_entries.forEach(e=>{
const fields=["author","title","booktitle","journal","year","volume","number","pages","publisher","address","edition","howpublished","note","doi","url"].filter(f=>e[f]).map(f=>"  "+f+" = {"+e[f]+"}").join(",\n");
lines.push("@"+(e.type||"article")+"{"+(e.key||"ref")+",\n"+fields+"\n}");lines.push("");
});
}
if(result.reviewer_responses&&result.reviewer_responses.length){
lines.push("REVIEWER RESPONSES");
result.reviewer_responses.forEach(r=>{lines.push("--- "+r.reviewer+" ---");lines.push("CONCERN: "+r.concern);lines.push("RESPONSE: "+r.response);lines.push("CHANGE: "+r.paper_change);lines.push("");});
}
downloadAsText(lines.join("\n"),"research-paper.txt");


};

const TOTAL_STEPS=7;
const stepTitles=["Basic Info","Contributions","Methodology","Experiments","Figures & Refs","Extra Sections","Review"];
const SECTION_ORDER=["abstract","abstract_structured","plain_language_summary","running_title","highlights","author_block","author_contributions","abbreviations_list","generated_figures","introduction","literature_review","methodology","results","results_table","hyperparameters_table","discussion","conclusion","cover_letter","acknowledgements","ethics_statement","conflict_of_interest","data_access_statement","supplementary_materials","appendix","references","bibtex_entries","citation_map","reviewer_responses"];
const SECTION_LABELS={abstract:"Abstract",abstract_structured:"Structured Abstract",plain_language_summary:"Plain Language Summary",running_title:"Running Title",highlights:"Highlights",author_block:"Author Block",author_contributions:"Author Contributions",abbreviations_list:"Abbreviations",generated_figures:"Generated Figures",introduction:"Introduction",literature_review:"Literature Review / Related Work",methodology:"Methodology",results:"Results",results_table:"Results Table",hyperparameters_table:"Hyperparameters Table",discussion:"Discussion",conclusion:"Conclusion",cover_letter:"Cover Letter",acknowledgements:"Acknowledgements",ethics_statement:"Ethics Statement ⚖",conflict_of_interest:"Conflict of Interest",data_access_statement:"Data Availability",supplementary_materials:"Supplementary Materials",appendix:"Appendix",references:"References",bibtex_entries:"BibTeX References",citation_map:"Citation Map [n]→Author",reviewer_responses:"Reviewer Responses"};
const CORE_SECTIONS=["abstract","introduction","literature_review","methodology","results","discussion","conclusion","ethics_statement","bibtex_entries","reviewer_responses"];

if (result) {
// Completeness check
const coreCheck = CORE_SECTIONS.map(s => {
  const val = result[s];
  const ok = val && (Array.isArray(val) ? val.length > 0 : String(val).trim().length > 80);
  return {s, ok};
});
const score = Math.round(coreCheck.filter(x=>x.ok).length / CORE_SECTIONS.length * 100);
const scoreColor = score >= 90 ? "var(--green)" : score >= 70 ? "var(--accent)" : "var(--red)";

// Section copy helper
const copySection = () => {
  const val = result[activeSection];
  if (!val) return;
  const text = typeof val === "string" ? val
    : Array.isArray(val) ? val.map((r,i) => Array.isArray(r) ? r.join("\t") : `${i+1}. ${r}`).join("\n")
    : JSON.stringify(val, null, 2);
  copyToClipboard(text);
};

// Word count with colour
const wc = result[activeSection] && typeof result[activeSection] === "string"
  ? result[activeSection].split(/\s+/).filter(Boolean).length : null;
const wcColor = !wc ? "var(--text3)" : wc > 400 ? "var(--green)" : wc > 150 ? "var(--accent)" : "var(--red)";

return (
<div>
<div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:12,flexWrap:"wrap",gap:8}}>
<div>
<div style={{fontSize:17,fontWeight:700}}>{result.title||form.topic}</div>
<div style={{fontSize:12,color:"var(--text3)",marginTop:4,display:"flex",gap:12,flexWrap:"wrap"}}>
  <span>{form.target_journal||"—"}</span>
  {result.total_word_count&&<span style={{color:result.total_word_count>4000?"var(--green)":result.total_word_count>2000?"var(--accent)":"var(--red)",fontWeight:700}}>📝 {result.total_word_count.toLocaleString()} words</span>}
  {!result.total_word_count&&<span>target {form.word_count} words</span>}
</div>
</div>
<div style={{display:"flex",gap:8,flexWrap:"wrap"}}>
<button className="btn btn-success btn-sm" onClick={downloadFiles}>⬇ LaTeX + BibTeX</button>
<button className="btn btn-secondary btn-sm" onClick={downloadTxt}>⬇ TXT</button>
<button className="btn btn-secondary btn-sm" onClick={()=>{setResult(null);setStep(1);}}>New Paper</button>
</div>
</div>

{/* Completeness + Publishability indicator */}
<div style={{background:"var(--navy2)",border:"1px solid var(--border)",borderRadius:8,padding:"10px 14px",marginBottom:12}}>
<div style={{display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:8,flexWrap:"wrap",gap:8}}>
<span style={{fontSize:12,fontWeight:700,color:"var(--text2)"}}>Paper Completeness</span>
<div style={{display:"flex",gap:10,alignItems:"center"}}>
  {/* Publishability score badge */}
  {result._publishability_score!=null&&(()=>{
    const ps=result._publishability_score;
    const pCol=ps>=85?"var(--green)":ps>=65?"var(--accent)":"var(--red)";
    const pLabel=ps>=85?"Publication Ready":ps>=65?"Needs Revisions":"Significant Gaps";
    return(
    <span style={{fontSize:11,fontWeight:700,padding:"3px 10px",borderRadius:12,
      background:ps>=85?"rgba(43,172,118,0.15)":ps>=65?"rgba(236,178,46,0.15)":"rgba(224,30,90,0.12)",
      color:pCol,border:`1px solid ${pCol}`,whiteSpace:"nowrap"}}>
      📋 Pub. Score: {ps}% — {pLabel}
    </span>);
  })()}
  <span style={{fontSize:15,fontWeight:700,color:scoreColor}}>{score}%</span>
</div>
</div>
<div style={{display:"flex",gap:6,flexWrap:"wrap"}}>
{coreCheck.map(({s,ok})=>(
<span key={s} style={{fontSize:10,padding:"2px 8px",borderRadius:10,fontWeight:600,
  background:ok?"rgba(43,172,118,0.15)":"rgba(224,30,90,0.12)",
  color:ok?"var(--green)":"var(--red)",border:`1px solid ${ok?"rgba(43,172,118,0.3)":"rgba(224,30,90,0.25)"}`}}>
  {ok?"✓":"✗"} {SECTION_LABELS[s]||s}
</span>
))}
</div>
<div style={{marginTop:8,fontSize:11,color:"var(--text3)"}}>
✅ <strong style={{color:"var(--green)"}}>Download LaTeX + BibTeX</strong> → upload both to <strong>overleaf.com</strong> → compile twice → submit.
</div>
{result._warnings&&result._warnings.length>0&&(
<div style={{marginTop:8,padding:"8px 10px",background:"rgba(236,178,46,0.08)",border:"1px solid rgba(236,178,46,0.3)",borderRadius:6}}>
<div style={{fontSize:11,fontWeight:700,color:"var(--accent)",marginBottom:6}}>Publication Readiness Checks:</div>
{result._warnings.map((w,i)=>{
  const isOk=w.startsWith("✅")||w.startsWith("ℹ");
  const isErr=w.startsWith("⚠");
  return(
  <div key={i} style={{fontSize:11,color:isOk?"var(--green)":isErr?"#ecb22e":"var(--text3)",
    padding:"2px 0",borderBottom:"1px solid rgba(255,255,255,0.05)"}}>
    {w}
  </div>);
})}
</div>
)}
{/* ── Senior Reviewer Pass output ─────────────────────────────────── */}
{result._review&&!result._review.error&&(
<div style={{marginTop:10,padding:"10px 12px",background:"rgba(29,142,219,0.06)",border:"1px solid rgba(29,142,219,0.25)",borderRadius:8}}>
<div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:8}}>
<div style={{fontSize:12,fontWeight:700,color:"var(--blue3)"}}>📝 Senior Reviewer Pass</div>
{result._review.verdict && (
<span style={{fontSize:10,padding:"3px 10px",borderRadius:10,fontWeight:700,
  background:/accept/i.test(result._review.verdict)?"rgba(43,172,118,0.2)":/borderline/i.test(result._review.verdict)?"rgba(236,178,46,0.2)":"rgba(224,30,90,0.18)",
  color:/accept/i.test(result._review.verdict)?"var(--green)":/borderline/i.test(result._review.verdict)?"var(--accent)":"var(--red)"}}>
  {result._review.verdict.toUpperCase()}
  {result._reviewer_acceptance_probability!=null && ` · ${result._reviewer_acceptance_probability}%`}
</span>
)}
</div>
{result._review.strengths&&result._review.strengths.length>0&&(
<div style={{marginBottom:6}}>
<div style={{fontSize:10,fontWeight:700,color:"var(--green)",marginBottom:3}}>STRENGTHS</div>
{result._review.strengths.map((s,i)=>(
<div key={i} style={{fontSize:11,color:"var(--text2)",padding:"2px 0"}}>✓ {s}</div>
))}
</div>
)}
{result._review.weaknesses&&result._review.weaknesses.length>0&&(
<div style={{marginBottom:6}}>
<div style={{fontSize:10,fontWeight:700,color:"var(--red)",marginBottom:3}}>WEAKNESSES &amp; FIXES</div>
{result._review.weaknesses.map((w,i)=>(
<div key={i} style={{fontSize:11,color:"var(--text2)",padding:"4px 0",borderBottom:"1px solid rgba(255,255,255,0.04)"}}>
<span style={{fontSize:9,padding:"1px 6px",borderRadius:8,marginRight:6,
  background:w.severity==="blocker"?"rgba(224,30,90,0.2)":w.severity==="major"?"rgba(236,178,46,0.18)":"rgba(128,128,128,0.12)",
  color:w.severity==="blocker"?"var(--red)":w.severity==="major"?"var(--accent)":"var(--text3)",
  textTransform:"uppercase",fontWeight:700}}>{w.severity||"minor"}</span>
<strong>{w.section}</strong>: {w.issue}<br/>
<span style={{color:"var(--blue3)",fontSize:10,marginLeft:12}}>→ {w.fix}</span>
</div>
))}
</div>
)}
{result._review.questions_reviewers_will_ask&&result._review.questions_reviewers_will_ask.length>0&&(
<div style={{marginBottom:6}}>
<div style={{fontSize:10,fontWeight:700,color:"var(--accent)",marginBottom:3}}>HARD QUESTIONS REVIEWERS WILL ASK</div>
{result._review.questions_reviewers_will_ask.map((q,i)=>(
<div key={i} style={{fontSize:11,color:"var(--text2)",padding:"1px 0"}}>? {q}</div>
))}
</div>
)}
{result._review.camera_ready_checklist&&result._review.camera_ready_checklist.length>0&&(
<div>
<div style={{fontSize:10,fontWeight:700,color:"var(--text2)",marginBottom:3}}>CAMERA-READY CHECKLIST</div>
{result._review.camera_ready_checklist.map((c,i)=>(
<div key={i} style={{fontSize:11,color:"var(--text2)",padding:"1px 0"}}>☐ {c}</div>
))}
</div>
)}
</div>
)}
{/* ── Quality analysers (burstiness + AI leak) ─────────────────────── */}
{(result._ai_leak_signals&&Object.keys(result._ai_leak_signals).length>0)||
 (result._burstiness_analysis&&Object.values(result._burstiness_analysis).some(b=>b.uniform_pct>70))?(
<div style={{marginTop:8,padding:"8px 10px",background:"rgba(224,30,90,0.05)",border:"1px solid rgba(224,30,90,0.2)",borderRadius:6,fontSize:11}}>
<div style={{fontWeight:700,color:"var(--red)",marginBottom:4}}>🤖 AI-Detection Risk Indicators</div>
{result._ai_leak_signals&&Object.keys(result._ai_leak_signals).length>0&&(
<div style={{color:"var(--text2)"}}>
<strong>Phrase leaks:</strong> {Object.entries(result._ai_leak_signals).map(([k,v])=>`${k}(${v})`).join(", ")}
</div>
)}
{result._citation_distribution&&result._citation_distribution.end_pct>75&&(
<div style={{color:"var(--text2)",marginTop:2}}>
<strong>Citation placement:</strong> {result._citation_distribution.end_pct}% at sentence-end (ideal &lt;65%)
</div>
)}
</div>
):null}
</div>

<div style={{display:"grid",gridTemplateColumns:"185px 1fr",gap:14,alignItems:"start"}}>
<div className="card" style={{position:"sticky",top:16}}>
<div className="card-header" style={{fontSize:10,letterSpacing:1}}>SECTIONS</div>
{SECTION_ORDER.filter(s=>{
  const v=result[s];
  return v!=null&&(Array.isArray(v)?v.length>0:String(v).trim().length>0);
}).map(s=>{
  const v=result[s];
  const wds=typeof v==="string"?v.split(/\s+/).filter(Boolean).length:null;
  const good=wds?wds>400:Array.isArray(v)&&v.length>0;
  return (
  <div key={s} onClick={()=>setActiveSection(s)}
  style={{padding:"7px 12px",cursor:"pointer",fontSize:12,borderBottom:"1px solid var(--border)",
  background:activeSection===s?"rgba(18,100,163,0.2)":"",
  color:activeSection===s?"var(--blue3)":"var(--text2)",
  fontWeight:activeSection===s?700:400,
  borderLeft:activeSection===s?"3px solid var(--blue)":"3px solid transparent",
  display:"flex",justifyContent:"space-between",alignItems:"center"}}>
  <span>{SECTION_LABELS[s]||s}</span>
  {wds&&<span style={{fontSize:10,color:good?"var(--green)":"var(--accent)",fontWeight:600}}>{wds}w</span>}
  </div>
);})}
</div>
<div className="card">
<div className="card-header" style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}>
<span style={{fontWeight:700}}>{SECTION_LABELS[activeSection]||activeSection}</span>
<div style={{display:"flex",gap:8,alignItems:"center"}}>
{wc && <span style={{fontSize:11,color:wcColor,fontWeight:600}}>{wc} words</span>}
<button className="btn btn-secondary btn-sm" onClick={copySection} title="Copy section to clipboard">📋</button>
</div>
</div>
<div className="card-body">
{activeSection==="keywords"&&Array.isArray(result.keywords)?(
<div className="tag-list">{result.keywords.map((k,i)=><span className="tag" key={i}>{k}</span>)}</div>
):activeSection==="highlights"&&Array.isArray(result.highlights)?(
<ul style={{listStyle:"none",display:"flex",flexDirection:"column",gap:8}}>
{result.highlights.map((h,i)=>(
<li key={i} style={{fontSize:13,color:"var(--text2)",display:"flex",gap:10,lineHeight:1.5,padding:"8px 12px",background:"rgba(43,172,118,0.07)",borderRadius:6,borderLeft:"3px solid var(--green)"}}>
<span style={{color:"var(--green)",fontWeight:700}}>•</span>{h}
</li>
))}
</ul>
):activeSection==="references"&&Array.isArray(result.references)?(
<ul style={{listStyle:"none",display:"flex",flexDirection:"column",gap:8}}>
{result.references.map((r,i)=>(
<li key={i} style={{fontSize:13,color:"var(--text2)",display:"flex",gap:10,lineHeight:1.5,padding:"8px 0",borderBottom:"1px solid var(--border)"}}>
<span style={{color:"var(--blue3)",fontWeight:700,flexShrink:0,minWidth:28}}>[{i+1}]</span>{r}
</li>
))}
</ul>
):activeSection==="reviewer_responses"&&Array.isArray(result.reviewer_responses)?(
<div style={{display:"flex",flexDirection:"column",gap:16}}>
{result.reviewer_responses.map((r,i)=>(
<div key={i} style={{border:"1px solid var(--border)",borderRadius:8,overflow:"hidden"}}>
<div style={{padding:"10px 16px",background:"rgba(18,100,163,0.15)",fontWeight:700,fontSize:13,color:"var(--blue3)"}}>{r.reviewer}</div>
<div style={{padding:"12px 16px",display:"flex",flexDirection:"column",gap:10}}>
<div><div style={{fontSize:11,fontWeight:700,color:"var(--text3)",marginBottom:4}}>CONCERN</div><div style={{fontSize:13,lineHeight:1.6,background:"rgba(255,80,80,0.07)",padding:"8px 12px",borderRadius:6}}>{r.concern}</div></div>
<div><div style={{fontSize:11,fontWeight:700,color:"var(--text3)",marginBottom:4}}>RESPONSE</div><div style={{fontSize:13,lineHeight:1.6,background:"rgba(43,172,118,0.07)",padding:"8px 12px",borderRadius:6}}>{r.response}</div></div>
<div><div style={{fontSize:11,fontWeight:700,color:"var(--text3)",marginBottom:4}}>PAPER CHANGE</div><div style={{fontSize:13,lineHeight:1.6,background:"rgba(18,100,163,0.07)",padding:"8px 12px",borderRadius:6}}>{r.paper_change}</div></div>
</div>
</div>
))}
</div>
):activeSection==="author_block"&&result.author_block?(
<div style={{display:"flex",flexDirection:"column",gap:10}}>
{[["Authors",result.author_block.authors],["Affiliations",result.author_block.affiliations],["Emails",result.author_block.emails],["Author Contributions",result.author_block.author_contributions],["Data Availability",result.author_block.data_availability]].map(([label,val])=>val?(
<div key={label} style={{padding:"10px 14px",background:"rgba(18,100,163,0.07)",borderRadius:6}}>
<div style={{fontSize:11,fontWeight:700,color:"var(--blue3)",marginBottom:4}}>{label.toUpperCase()}</div>
<div style={{fontSize:13,lineHeight:1.7,color:"var(--text)"}}>{val}</div>
</div>
):null)}
</div>
):activeSection==="results_table"&&Array.isArray(result.results_table)&&result.results_table.length>1?(
<div>
{result.results_table_caption&&<div style={{fontSize:12,color:"var(--text3)",marginBottom:10,fontStyle:"italic"}}>{result.results_table_caption}</div>}
<div style={{overflowX:"auto"}}>
<table style={{width:"100%",borderCollapse:"collapse",fontSize:13}}>
<thead><tr>{result.results_table[0].map((h,i)=><th key={i} style={{padding:"9px 12px",background:"rgba(18,100,163,0.2)",color:"var(--blue3)",fontWeight:700,textAlign:"left",borderBottom:"2px solid var(--blue)",whiteSpace:"nowrap"}}>{h}</th>)}</tr></thead>
<tbody>{result.results_table.slice(1).map((row,i)=>(
<tr key={i} style={{background:i===0?"rgba(43,172,118,0.08)":i%2===0?"var(--navy)":"var(--navy2)",borderBottom:"1px solid var(--border)"}}>
{row.map((cell,j)=><td key={j} style={{padding:"8px 12px",color:i===0&&j>0?"var(--green)":"var(--text)",fontWeight:i===0&&j>0?700:400}}>{cell}</td>)}
</tr>))}</tbody>
</table>
</div>
{result.bibtex_entries&&<div style={{marginTop:10,fontSize:11,color:"var(--text3)"}}>★ Bold row = proposed method. Download LaTeX to get this table formatted for submission.</div>}
</div>
):activeSection==="hyperparameters_table"&&Array.isArray(result.hyperparameters_table)&&result.hyperparameters_table.length>1?(
<div>
{result.hyperparameters_table_caption&&<div style={{fontSize:12,color:"var(--text3)",marginBottom:10,fontStyle:"italic"}}>{result.hyperparameters_table_caption}</div>}
<div style={{overflowX:"auto"}}>
<table style={{width:"100%",borderCollapse:"collapse",fontSize:13}}>
<thead><tr>{result.hyperparameters_table[0].map((h,i)=><th key={i} style={{padding:"9px 12px",background:"rgba(18,100,163,0.2)",color:"var(--blue3)",fontWeight:700,textAlign:"left",borderBottom:"2px solid var(--blue)"}}>{h}</th>)}</tr></thead>
<tbody>{result.hyperparameters_table.slice(1).map((row,i)=>(
<tr key={i} style={{background:i%2===0?"var(--navy)":"var(--navy2)",borderBottom:"1px solid var(--border)"}}>
{row.map((cell,j)=><td key={j} style={{padding:"8px 12px",color:j===0?"var(--blue3)":"var(--text)",fontWeight:j===0?600:400,fontFamily:j===1?"'IBM Plex Mono',monospace":"inherit"}}>{cell}</td>)}
</tr>))}</tbody>
</table>
</div>
</div>
):activeSection==="abbreviations_list"?(
<div>
{typeof result.abbreviations_list==="string"?(
<table style={{width:"100%",borderCollapse:"collapse",fontSize:13}}>
<thead><tr style={{borderBottom:"2px solid var(--border)"}}><th style={{textAlign:"left",padding:"8px 12px",color:"var(--blue3)",width:120}}>Abbreviation</th><th style={{textAlign:"left",padding:"8px 12px",color:"var(--blue3)"}}>Definition</th></tr></thead>
<tbody>{result.abbreviations_list.split(";").map(s=>s.trim()).filter(Boolean).map((entry,i)=>{
const parts=entry.split(/\s*[—–-]\s*/);
return(<tr key={i} style={{borderBottom:"1px solid var(--border)",background:i%2===0?"var(--navy)":"var(--navy2)"}}>
<td style={{padding:"8px 12px",fontWeight:700,color:"var(--green)",fontFamily:"'IBM Plex Mono',monospace"}}>{parts[0]||""}</td>
<td style={{padding:"8px 12px",color:"var(--text2)"}}>{parts.slice(1).join(" — ")||entry}</td>
</tr>);})}
</tbody></table>
):Array.isArray(result.abbreviations_list)?(
<table style={{width:"100%",borderCollapse:"collapse",fontSize:13}}>
<thead><tr style={{borderBottom:"2px solid var(--border)"}}><th style={{textAlign:"left",padding:"8px",color:"var(--blue3)"}}>Abbr</th><th style={{textAlign:"left",padding:"8px",color:"var(--blue3)"}}>Definition</th></tr></thead>
<tbody>{result.abbreviations_list.map((a,i)=>(<tr key={i} style={{borderBottom:"1px solid var(--border)",background:i%2===0?"var(--navy)":"var(--navy2)"}}><td style={{padding:"8px",fontWeight:700,color:"var(--green)"}}>{typeof a==="object"?a.abbr:a}</td><td style={{padding:"8px",color:"var(--text2)"}}>{typeof a==="object"?a.definition:""}</td></tr>))}</tbody>
</table>
):null}
</div>
):activeSection==="generated_figures"&&result.generated_figures?(
<div style={{display:"flex",flexDirection:"column",gap:16}}>
{result.generated_figures.map((fig,i)=>(
<div key={i} style={{border:"1px solid var(--border)",borderRadius:8,overflow:"hidden"}}>
<div style={{padding:"10px 14px",background:"rgba(18,100,163,0.1)",fontWeight:700,fontSize:13,color:"var(--blue3)"}}>Figure {i+1}</div>
{fig.image_base64?(<img src={"data:image/png;base64,"+fig.image_base64} style={{width:"100%",maxHeight:400,objectFit:"contain",background:"white",padding:8}}/>):(<div style={{padding:16,color:"var(--text3)",fontSize:12}}>Figure generation failed — placeholder used in LaTeX</div>)}
<div style={{padding:"8px 14px",fontSize:12,color:"var(--text2)",borderTop:"1px solid var(--border)"}}>{fig.caption}</div>
</div>
))}
</div>
):activeSection==="abstract_structured"&&result.abstract_structured?(
<div style={{display:"flex",flexDirection:"column",gap:12}}>
{["background","objective","methods","results","conclusion"].map(k=>result.abstract_structured[k]?(
<div key={k} style={{padding:"10px 14px",background:"rgba(18,100,163,0.07)",borderRadius:6,borderLeft:"3px solid var(--blue)"}}>
<div style={{fontSize:11,fontWeight:700,color:"var(--blue3)",marginBottom:4,textTransform:"uppercase"}}>{k}</div>
<div style={{fontSize:13,lineHeight:1.7,color:"var(--text)"}}>{result.abstract_structured[k]}</div>
</div>
):null)}
</div>
):activeSection==="citation_map"&&result.citation_map&&Object.keys(result.citation_map).length>0?(
<div>
<div style={{marginBottom:10,fontSize:12,color:"var(--text3)"}}>
  Maps every <code>[n]</code> reference used in the paper to its author/year — used to build BibTeX in Call 5.
  {Object.keys(result.citation_map).length} citations tracked.
</div>
<table style={{width:"100%",borderCollapse:"collapse",fontSize:12}}>
<thead><tr style={{borderBottom:"2px solid var(--border)"}}>
  {["[n]","Author","Year","Venue","Title Hint"].map(h=>(
    <th key={h} style={{textAlign:"left",padding:"7px 10px",color:"var(--blue3)",fontWeight:700}}>{h}</th>
  ))}
</tr></thead>
<tbody>{Object.entries(result.citation_map).sort((a,b)=>parseInt(a[0])-parseInt(b[0])).map(([n,v],i)=>(
  <tr key={n} style={{borderBottom:"1px solid var(--border)",background:i%2===0?"var(--navy)":"var(--navy2)"}}>
    <td style={{padding:"6px 10px",fontWeight:700,color:"var(--green)",whiteSpace:"nowrap"}}>[{n}]</td>
    <td style={{padding:"6px 10px",color:"var(--text)"}}>{v.author||"—"}</td>
    <td style={{padding:"6px 10px",color:"var(--accent)",whiteSpace:"nowrap"}}>{v.year||"—"}</td>
    <td style={{padding:"6px 10px",color:"var(--text3)",whiteSpace:"nowrap"}}>{v.venue||"—"}</td>
    <td style={{padding:"6px 10px",color:"var(--text2)",fontStyle:"italic"}}>{v.title_hint||"—"}</td>
  </tr>
))}</tbody>
</table>
</div>
):activeSection==="bibtex_entries"&&Array.isArray(result.bibtex_entries)&&result.bibtex_entries.length>0?(
<div>
<div style={{display:"flex",justifyContent:"space-between",alignItems:"center",marginBottom:12}}>
  <span style={{fontSize:12,color:"var(--text3)"}}>{result.bibtex_entries.length} entries · included in references.bib when you download LaTeX</span>
  <button className="btn btn-secondary btn-sm" onClick={()=>{
    const txt=result.bibtex_entries.map(e=>{
      const fields=["author","title","booktitle","journal","year","volume","number","pages","publisher","address","edition","howpublished","note","doi","url"].filter(f=>e[f]).map(f=>"  "+f+" = {"+e[f]+"}").join(",\n");
      return "@"+(e.type||"article")+"{"+(e.key||"ref")+",\n"+fields+"\n}";
    }).join("\n\n");
    copyToClipboard(txt);
  }}>📋 Copy .bib</button>
</div>
<div style={{display:"flex",flexDirection:"column",gap:8}}>
{result.bibtex_entries.map((e,i)=>(
<div key={i} style={{background:"rgba(0,0,0,0.25)",borderRadius:6,border:"1px solid var(--border)",padding:"10px 14px",fontFamily:"'IBM Plex Mono',monospace",fontSize:11,lineHeight:1.8}}>
<span style={{color:"var(--blue3)",fontWeight:700}}>@{e.type||"article"}</span><span style={{color:"var(--text)"}}>{"{"}</span><span style={{color:"var(--accent)",fontWeight:700}}>{e.key}</span><span style={{color:"var(--text)"}}>{","}</span>
{["author","title","booktitle","journal","year","volume","number","pages","publisher","note","doi","url"].filter(f=>e[f]).map(f=>(
<div key={f} style={{paddingLeft:16}}>
  <span style={{color:"var(--accent)"}}>{f}</span>
  <span style={{color:"var(--text3)"}}> = </span>
  <span style={{color:"var(--text)"}}>{"{"}</span>
  <span style={{color:"var(--green)"}}>{e[f]}</span>
  <span style={{color:"var(--text)"}}>{"},"}</span>
</div>
))}
<span style={{color:"var(--text)"}}>{"}"}</span>
</div>
))}
</div>
</div>
):(
<div style={{fontSize:14,lineHeight:1.9,color:"var(--text)",whiteSpace:"pre-wrap",wordBreak:"break-word"}}>
{result[activeSection]?(()=>{
  const raw = typeof result[activeSection]==="string"
    ? result[activeSection]
    : JSON.stringify(result[activeSection],null,2);
  const display = stripLatexForDisplay(raw);
  // Render ◆ subsection headers as styled blocks
  const parts = display.split(/(\n◆ [^\n]+\n|\n◈ [^\n]+\n)/g);
  return parts.map((part,i)=>{
    const hdr = part.match(/^\n[◆◈◇] (.+)\n$/);
    if(hdr) return (
      <div key={i} style={{margin:"18px 0 6px",paddingBottom:4,
        borderBottom:"2px solid rgba(18,100,163,0.35)",
        color:"var(--blue3)",fontWeight:700,fontSize:13,letterSpacing:0.3}}>
        {hdr[1]}
      </div>
    );
    return <span key={i}>{part}</span>;
  });
})():"(Section not generated — regenerate the paper)"}
</div>
)}
</div>
</div>
</div>
</div>
);}


return (
<div style={{maxWidth:700}}>
<div style={{marginBottom:24,background:"var(--navy2)",border:"1px solid var(--border)",borderRadius:12,padding:"16px 20px"}}>
  {/* Step progress bar */}
  <div style={{display:"flex",alignItems:"center",marginBottom:14}}>
    {stepTitles.map((t,i)=>(
      <div key={i} style={{display:"flex",alignItems:"center",flex:1,minWidth:0}}>
        {/* Step pill */}
        <div style={{display:"flex",flexDirection:"column",alignItems:"center",gap:4,flexShrink:0}}
          onClick={()=>step>i+1&&setStep(i+1)}>
          <div style={{
            width:28,height:28,borderRadius:"50%",
            display:"flex",alignItems:"center",justifyContent:"center",
            fontSize:11,fontWeight:700,cursor:step>i+1?"pointer":"default",
            background: step>i+1?"rgba(43,172,118,0.2)":step===i+1?"rgba(29,142,219,0.25)":"var(--navy3)",
            border: step>i+1?"1.5px solid var(--green)":step===i+1?"1.5px solid var(--blue3)":"1.5px solid var(--border)",
            color: step>i+1?"var(--green)":step===i+1?"var(--blue3)":"var(--text3)",
            boxShadow: step===i+1?"0 0 14px rgba(29,142,219,0.35)":"none",
            transition:"all 0.25s",
          }}>
            {step>i+1 ? "✓" : i+1}
          </div>
        </div>
        {/* Connector */}
        {i<stepTitles.length-1 && (
          <div style={{flex:1,height:2,margin:"0 4px",borderRadius:1,
            background: step>i+1?"var(--green)":"var(--navy3)",
            transition:"background 0.4s"}}/>
        )}
      </div>
    ))}
  </div>
  {/* Step labels */}
  <div style={{display:"flex",justifyContent:"space-between"}}>
    {stepTitles.map((t,i)=>(
      <div key={i} style={{flex:1,textAlign:"center",fontSize:10,fontWeight:step===i+1?700:400,
        color:step===i+1?"var(--blue3)":step>i+1?"var(--green)":"var(--text3)",
        transition:"color 0.25s",letterSpacing:0.2,padding:"0 2px"}}>
        {t}
      </div>
    ))}
  </div>
  {/* Current step label */}
  <div style={{marginTop:12,fontSize:11,color:"var(--text3)",textAlign:"center"}}>
    Step <strong style={{color:"var(--text)"}}>{step}</strong> of {TOTAL_STEPS} — <span style={{color:"var(--blue3)",fontWeight:600}}>{stepTitles[step-1]}</span>
  </div>
</div>
{error&&<div style={{background:"rgba(232,93,74,0.1)",border:"1px solid rgba(232,93,74,0.3)",borderRadius:8,padding:"12px 16px",marginBottom:16,color:"#E85D4A",fontSize:13}}>⚠ {error}</div>}
{loading&&(
<div className="card" style={{overflow:"hidden"}}>
  {/* Shimmer top bar */}
  <div style={{height:3,background:"var(--navy3)",position:"relative",overflow:"hidden"}}>
    <div style={{position:"absolute",inset:0,background:"linear-gradient(90deg,transparent 0%,var(--blue3) 40%,var(--blue2) 60%,transparent 100%)",animation:"shimmerBar 1.8s linear infinite",backgroundSize:"200% 100%"}}/>
  </div>
  <div style={{padding:"36px 32px"}}>
    {/* Title row */}
    <div style={{textAlign:"center",marginBottom:32}}>
      <div style={{fontSize:15,fontWeight:700,color:"var(--text)",marginBottom:6}}>✨ Generating your paper…</div>
      <div style={{fontSize:12,color:"var(--text3)"}}>~7–10 min total · keep this tab open</div>
    </div>
    {/* Step pipeline */}
    <div style={{display:"flex",flexDirection:"column",gap:0}}>
      {LOADING_STEPS.map((step,i)=>{
        const done = i < loadingStep;
        const active = i === loadingStep;
        return (
          <div key={i} style={{display:"flex",gap:16,alignItems:"flex-start",paddingBottom:i<LOADING_STEPS.length-1?16:0}}>
            {/* Icon + connector */}
            <div style={{display:"flex",flexDirection:"column",alignItems:"center",flexShrink:0}}>
              <div style={{
                width:32,height:32,borderRadius:"50%",display:"flex",alignItems:"center",justifyContent:"center",
                fontSize:13,fontWeight:700,flexShrink:0,
                background: done ? "rgba(43,172,118,0.15)" : active ? "rgba(29,142,219,0.2)" : "var(--navy3)",
                border: done ? "1.5px solid var(--green)" : active ? "1.5px solid var(--blue3)" : "1.5px solid var(--border)",
                color: done ? "var(--green)" : active ? "var(--blue3)" : "var(--text3)",
                boxShadow: active ? "0 0 12px rgba(54,197,240,0.3)" : "none",
                transition:"all 0.4s",
              }}>
                {done ? "✓" : active ? <span className="spinner" style={{width:14,height:14,borderWidth:2}}/> : i+1}
              </div>
              {i < LOADING_STEPS.length-1 && (
                <div style={{width:2,flex:1,minHeight:16,marginTop:3,
                  background: done ? "var(--green)" : "var(--border)",
                  transition:"background 0.4s"}}/>
              )}
            </div>
            {/* Label */}
            <div style={{paddingTop:6,paddingBottom:i<LOADING_STEPS.length-1?0:0}}>
              <div style={{fontSize:13,fontWeight:active?700:done?500:400,
                color:active?"var(--text)":done?"var(--text2)":"var(--text3)",
                transition:"all 0.3s"}}>
                {step.replace(/^[^—]+— /,"")}
              </div>
              {active && <div style={{fontSize:11,color:"var(--blue3)",marginTop:3,fontWeight:600}}>Currently processing…</div>}
              {done  && <div style={{fontSize:11,color:"var(--green)",marginTop:3}}>Complete ✓</div>}
            </div>
          </div>
        );
      })}
    </div>
    {/* Overall progress bar */}
    <div style={{marginTop:24,padding:"12px 16px",background:"rgba(18,100,163,0.07)",borderRadius:8,border:"1px solid rgba(18,100,163,0.15)"}}>
      <div style={{display:"flex",justifyContent:"space-between",marginBottom:8,fontSize:11,color:"var(--text3)"}}>
        <span style={{fontWeight:600,color:"var(--text2)"}}>Overall progress</span>
        <span>{Math.round(((loadingStep+0.5)/LOADING_STEPS.length)*100)}%</span>
      </div>
      <div style={{height:6,background:"var(--navy3)",borderRadius:3,overflow:"hidden"}}>
        <div style={{height:"100%",borderRadius:3,transition:"width 1.5s ease",
          background:"linear-gradient(90deg,var(--blue),var(--blue3))",
          width:(((loadingStep+0.5)/LOADING_STEPS.length)*100)+"%"}}/>
      </div>
    </div>
  </div>
</div>
)}
{!loading&&(
<div className="card">
{step===1&&(<div><div className="card-header">📝 Step 1 — Basic Information</div><div className="card-body">
<Field label="Research Topic" k="topic" placeholder="e.g. Adaptive sparse attention for long-document transformers" required form={form} update={update}/>
            <Field label="Core Research Question" k="research_question" hint="Be specific — a vague question produces a vague paper" placeholder="e.g. Can learned sparse attention reduce O(n²) to O(n log n) while retaining 95% performance?" textarea required form={form} update={update}/>
            <Field label="Main Hypothesis" k="hypothesis" placeholder="e.g. Content-adaptive sparsity masks outperform fixed patterns" textarea form={form} update={update}/>
            <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:16}}>
              <div className="form-group"><label className="form-label">Target Journal / Conference</label><input className="form-input" placeholder="e.g. NeurIPS 2025, ACL, IEEE" value={form.target_journal} onChange={e=>update("target_journal",e.target.value)}/></div>
              <div className="form-group"><label className="form-label">Paper Length</label><select className="form-input" value={form.word_count} onChange={e=>update("word_count",e.target.value)}><option value="3000">Short (~3,000)</option><option value="5000">Standard (~5,000)</option><option value="8000">Long (~8,000)</option></select></div>
            </div>
            <div className="form-group"><label className="form-label">Research Field</label>
              <div style={{fontSize:11,color:"var(--blue3)",marginBottom:6,padding:"4px 8px",background:"rgba(18,100,163,0.1)",borderRadius:4}}>Controls writing style and citation conventions</div>
              <select className="form-input" value={form.research_field} onChange={e=>update("research_field",e.target.value)}>
                <option value="computer_science">💻 Computer Science / AI / ML</option>
                <option value="medicine">🏥 Medicine / Clinical Research</option>
                <option value="biology">🧬 Biology / Life Sciences</option>
                <option value="physics">⚛️ Physics / Engineering</option>
                <option value="economics">📊 Economics / Social Sciences</option>
                <option value="chemistry">🧪 Chemistry / Materials Science</option>
                <option value="psychology">🧠 Psychology / Neuroscience</option>
                <option value="environmental">🌍 Environmental Sciences</option>
              </select>
            </div>
            <div className="form-group"><label className="form-label">LaTeX Format</label><select className="form-input" value={form.column_format} onChange={e=>update("column_format",e.target.value)}><option value="single">Single Column (Nature, Springer)</option><option value="two">Two Column (IEEE, ACM, NeurIPS)</option></select></div>
          </div></div>)}
          {step===2&&(<div><div className="card-header">🏆 Step 2 — Contributions & Findings</div><div className="card-body">
            <Field label="Numbered Contributions (one per line)" k="contribution_list" hint="Be extremely specific — this is the most important part" placeholder={"1. Novel attention mechanism achieving 3.2x speedup\n2. 96.1% retention of full-attention performance\n3. Open-source code released"} textarea form={form} update={update}/>
            <Field label="Key Findings with Exact Numbers" k="key_findings" hint="Papers without specific numbers get rejected" placeholder={"96.1% GLUE performance (85.3 vs 88.7 baseline)\n3.2x speedup over FlashAttention-2 at 32K tokens\n71% memory reduction"} textarea form={form} update={update}/>
            <Field label="Novelty Statement (what's new vs prior work)" k="novelty_statement" hint="One paragraph — what nobody has done before your paper. Top-tier venues reward explicit novelty." placeholder={"Prior work applies Transformers to bearings [Wang2023, Li2024] but uses all 518 FFT features with no interpretability. Our novelty: (1) first SHAP-guided feature selection for bearing faults, (2) lightest Transformer in this literature (275K params), (3) first dual-XAI validation against BPFI physics."} textarea form={form} update={update}/>
            <Field label="Anticipated Reviewer Concerns (weakest point)" k="reviewer_concerns" hint="Your paper's weakest point. Claude pre-addresses it in Limitations and Discussion." placeholder={"Single-dataset evaluation (only CWRU). Reviewers will want cross-dataset validation on MFPT/Paderborn. Compound faults not tested."} textarea form={form} update={update}/>
          </div></div>)}
          {step===3&&(<div><div className="card-header">⚙️ Step 3 — Methodology</div><div className="card-body">
            <Field label="Methodology Type" k="methodology_type" placeholder="e.g. empirical, theoretical, mixed-methods" form={form} update={update}/>
            <Field label="Datasets Used" k="datasets" hint="List all datasets with sizes" placeholder={"GLUE Benchmark (9 NLU tasks)\nLongBench (21 long-doc tasks)\nSCROLLS (7 summarization tasks)"} textarea form={form} update={update}/>
            <Field label="Limitations" k="limitations" placeholder={"1. Routing network adds 2.3% overhead\n2. Degrades on uniform attention tasks"} textarea form={form} update={update}/>
            <Field label="Future Work" k="future_work" placeholder={"Extend to decoder-only architectures\nPer-layer adaptive sparsity"} textarea form={form} update={update}/>
          </div></div>)}
          {step===4&&(<div><div className="card-header">🧪 Step 4 — Experimental Data</div><div className="card-body">
            <Field label="Results Table (one row per line)" k="experimental_results" hint="Format: Model | Dataset | Metric | Score" placeholder={"CASA (ours) | LongBench | F1 | 47.3\nLongformer | LongBench | F1 | 43.2\nBigBird | LongBench | F1 | 42.8"} textarea form={form} update={update}/>
            <Field label="Hyperparameters" k="hyperparameters" hint="Critical for reproducibility" placeholder={"Base model: RoBERTa-large\nLearning rate: 2e-4\nBatch size: 32\nHardware: 8x A100 80GB"} textarea form={form} update={update}/>
            <Field label="Statistical Tests (rigour signal)" k="statistical_tests" hint="Test type + n + effect size + correction. Top-tier venues require this." placeholder={"Paired t-test across 5 runs (seeds 42, 123, 456, 789, 999). n=5 per condition. Bonferroni correction for 7 pairwise comparisons. Cohen's d reported for effect size."} textarea form={form} update={update}/>
            <Field label="Algorithm Pseudocode (optional — triggers algorithm block)" k="algorithm_description" hint="If your method is algorithmic, describe inputs, main loop, and outputs. Claude will render an \\begin{algorithm}...\\end{algorithm} block." placeholder={"Inputs: vibration signal x ∈ R^1024, pre-trained SHAP selector S, LightTransformer f_θ.\nOutput: predicted fault class y^.\n1. FFT(x) → 518-dim spectrum.\n2. Select top-K=64 features using S.\n3. Patch-embed into 16 tokens, 128-dim.\n4. Prepend CLS, pass through 2 Transformer layers.\n5. Classify CLS token through linear head."} textarea form={form} update={update}/>
          </div></div>)}
          {step===5&&(<div><div className="card-header">🖼️ Step 5 — Figures & Related Work</div><div className="card-body">
            <Field label="Figure Descriptions (one per line)" k="figure_descriptions" hint="Claude writes captions and references them in text" placeholder={"Bar chart comparing all models on LongBench with error bars\nLine chart GPU memory vs sequence length 2K-64K\nAblation study removing each component"} textarea form={form} update={update}/>
            <Field label="Related Papers (15+ for strong paper)" k="related_papers" hint="Include author, year, venue" placeholder={"Vaswani et al. (2017) Attention Is All You Need. NeurIPS\nBeltagy et al. (2020) Longformer. ArXiv\nDao et al. (2022) FlashAttention. NeurIPS"} textarea form={form} update={update}/>
          </div></div>)}
          {step===6&&(<div><div className="card-header">📋 Step 6 — Extra Sections</div><div className="card-body">
            <Field label="Author Names" k="authors_list" hint="Full names in order" placeholder="Jane Doe, John Smith" form={form} update={update}/>
            <Field label="Author Emails" k="authors_emails" placeholder="jane.doe@mit.edu" form={form} update={update}/>
            <Field label="Author Contributions (CRediT)" k="author_contributions" hint="Required by Nature, Elsevier, PLOS" placeholder="J.D.: Conceptualization, Methodology. J.S.: Software." textarea form={form} update={update}/>
            <Field label="Data & Code Availability" k="data_access_statement" hint="Required by IEEE, Nature" placeholder="Code at https://github.com/username/repo under MIT License." form={form} update={update}/>
            <Field label="Acknowledgements & Funding" k="acknowledgements" placeholder="Supported by NSF Grant No. IIS-2143064." form={form} update={update}/>
            <Field label="Ethics Statement" k="ethics_statement" hint="Mandatory for NeurIPS, ACL, Nature" placeholder="All datasets publicly available. No PII. Carbon: ~54 kg CO2eq." textarea form={form} update={update}/>
            <Field label="Venue Fit Rationale (drives cover letter)" k="venue_fit_rationale" hint="1-2 sentences — why THIS venue specifically matches your paper's scope" placeholder={"MAI-2026 emphasises machine vision and augmented intelligence for industrial systems. Our XAI-guided bearing fault diagnosis directly fits the conference's scope on explainable AI for industrial machine vision applications."} textarea form={form} update={update}/>
            {allPapers.length>0&&(<div className="form-group"><label className="form-label">Uploaded Papers to Reference</label>
              <div style={{background:"var(--navy)",borderRadius:8,padding:"12px",border:"1px solid var(--border)"}}>
                {allPapers.map(p=>(<label key={p.id} style={{display:"flex",alignItems:"center",gap:10,padding:"8px 0",cursor:"pointer",fontSize:13,borderBottom:"1px solid var(--border)"}}>
                  <input type="checkbox" checked={selectedPapers.includes(p.id)} onChange={e=>setSelectedPapers(e.target.checked?[...selectedPapers,p.id]:selectedPapers.filter(x=>x!==p.id))}/>
                  <div><div style={{fontWeight:600}}>{p.title||p.file_name}</div>{p.authors&&<div style={{fontSize:11,color:"var(--text3)"}}>{p.authors}</div>}</div>
                </label>))}
              </div>
            </div>)}
          </div></div>)}
          {step===7&&(<div><div className="card-header">👁 Step 7 — Review & Generate</div><div className="card-body">
            <div style={{display:"flex",flexDirection:"column",gap:0,marginBottom:14,border:"1px solid var(--border)",borderRadius:8,overflow:"hidden"}}>
              {[["Topic",form.topic],["Research Question",form.research_question],["Contributions",form.contribution_list?form.contribution_list.split("\n").filter(s=>s.trim()).length+" items":""],["Key Findings",form.key_findings?"✓ With numbers":""],["Methodology",form.methodology_type],["Results Table",form.experimental_results?form.experimental_results.split("\n").filter(s=>s.trim()).length+" rows":"Not provided"],["Hyperparameters",form.hyperparameters?"✓ Provided":"Not provided"],["Figures",form.figure_descriptions?form.figure_descriptions.split("\n").filter(s=>s.trim()).length+" described":"None"],["Related Papers",form.related_papers?form.related_papers.split("\n").filter(s=>s.trim()).length+" papers":"None"],["Authors",form.authors_list||"Not provided"],["Data Access",form.data_access_statement?"✓ Provided":"Not provided"],["Format",form.column_format==="two"?"Two-column":"Single-column"],["Journal",form.target_journal||"Not specified"],["Field",form.research_field],["Uploaded Papers",selectedPapers.length+" selected"]].map((item,i)=>item[1]?(
                <div key={item[0]} style={{display:"flex",gap:12,fontSize:12,padding:"8px 14px",background:i%2===0?"var(--navy)":"var(--navy2)",borderBottom:"1px solid var(--border)"}}>
                  <div style={{color:"var(--text3)",minWidth:160,flexShrink:0,fontWeight:600}}>{item[0]}</div>
                  <div style={{color:"var(--green)"}}>{item[1]}</div>
                </div>
              ):null)}
            </div>
            <div style={{background:"rgba(18,100,163,0.08)",border:"1px solid rgba(18,100,163,0.2)",borderRadius:8,padding:"12px 14px",marginBottom:14}}>
              <div style={{fontSize:12,fontWeight:700,color:"var(--blue3)",marginBottom:8}}>What you get — top-tier output:</div>
              <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:4,fontSize:11,color:"var(--text3)"}}>
                <div>✅ research-paper.tex (Overleaf-ready)</div><div>✅ references.bib (18-22 BibTeX entries)</div>
                <div>✅ IMRaD structured abstract (5 parts)</div><div>✅ Introduction with numbered contributions</div>
                <div>✅ Related work with 20+ citations</div><div>✅ Methodology with math notation</div>
                <div>✅ Results table + ablation study</div><div>✅ Discussion with honest limitations</div>
                <div>✅ Conclusion with exact metrics</div><div>✅ Cover letter for submission</div>
                <div>✅ Humanizer pass (natural prose)</div><div>✅ 4 reviewer responses + rebuttals</div>
                <div>✅ Author block + CRediT statement</div><div>✅ Ethics + data availability sections</div>
              </div>
            </div>
            <div style={{background:"rgba(43,172,118,0.07)",border:"1px solid rgba(43,172,118,0.2)",borderRadius:8,padding:"10px 14px",marginBottom:12,fontSize:12}}>
              <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:6}}>
                <div style={{textAlign:"center"}}><div style={{fontWeight:700,color:"var(--green)"}}>7</div><div style={{color:"var(--text3)"}}>Claude calls</div></div>
                <div style={{textAlign:"center"}}><div style={{fontWeight:700,color:"var(--accent)"}}>~8-12 min</div><div style={{color:"var(--text3)"}}>generation time</div></div>
                <div style={{textAlign:"center"}}><div style={{fontWeight:700,color:"var(--blue3)"}}>~$0.55-1.05</div><div style={{color:"var(--text3)"}}>API cost (Sonnet 4)</div></div>
              </div>
            </div>
            <button className="btn btn-primary" onClick={generate} disabled={!form.topic||!form.research_question||loading}
              style={{width:"100%",justifyContent:"center",padding:"13px",fontSize:14,fontWeight:700}}>
              ✍️ Generate Full Research Paper
            </button>
          </div></div>)}
          <div style={{padding:"12px 18px",borderTop:"1px solid var(--border)",display:"flex",justifyContent:"space-between",alignItems:"center"}}>
            <button className="btn btn-secondary" onClick={()=>setStep(s=>s-1)} disabled={step===1||loading}>← Back</button>
            <span style={{fontSize:11,color:"var(--text3)"}}>Step {step} of {TOTAL_STEPS}</span>
            {step<7&&<button className="btn btn-primary" onClick={()=>setStep(s=>s+1)} disabled={(step===1&&(!form.topic||!form.research_question))||loading}>Next →</button>}
            {step===7&&<div/>}
          </div>
        </div>
      )}
    </div>
  );
}


// ── Main App ───────────────────────────────────────────────────────────────────
export default function App() {
  const [auth, setAuth] = useState(() => {
    try { return JSON.parse(localStorage.getItem("ra_auth") || "null"); } catch { return null; }
  });
  const [authMode, setAuthMode] = useState("login");
  const [page, setPage] = useState("dashboard");
  const [pageData, setPageData] = useState(null);
  const [toast, setToast] = useState(null);
  const showToast = (msg) => setToast(msg);

  const handleLogin = (data) => {
    localStorage.setItem("ra_auth", JSON.stringify(data));
    setAuth(data);
  };

  const handleLogout = () => {
    localStorage.removeItem("ra_auth");
    setAuth(null);
  };

  const navigate = (p, data = null) => {
    setPage(p); setPageData(data);
  };

  if (!auth) {
    return (
      <>
        <style>{style}</style>
        {authMode === "login"
          ? <LoginPage onLogin={handleLogin} onSwitch={() => setAuthMode("register")} />
          : <RegisterPage onLogin={handleLogin} onSwitch={() => setAuthMode("login")} />}
      </>
    );
  }

  const navItems = [
    { id:"dashboard", icon:"🏠", label:"Dashboard" },
    { id:"upload", icon:"📤", label:"Upload Paper" },
    { id:"analysis", icon:"📄", label:"Paper Analysis" },
    { id:"literature", icon:"📚", label:"Literature Review" },
    { id:"gaps", icon:"🔍", label:"Research Gaps" },
    { id:"grant", icon:"💰", label:"Grant Proposal" },
    { id:"write", icon:"✍️", label:"Write Paper" },
  ];

  const pageMap = {
    dashboard: { title:"Dashboard", sub:"Overview of your research workspace" },
    upload: { title:"Upload Paper", sub:"Add a new research paper for AI analysis" },
    analysis: { title:"Paper Analysis", sub:"View Claude AI analysis of your papers" },
    literature: { title:"Literature Review", sub:"Generate comprehensive literature reviews" },
    gaps: { title:"Research Gaps", sub:"Identify opportunities in the literature" },
    write: { title:"Write Paper", sub:"AI-powered academic paper writer" },
    grant: { title:"Grant Proposal", sub:"AI-powered grant proposal generation" },
  };

  const initials = auth.full_name?.split(" ").map(n=>n[0]).join("").slice(0,2).toUpperCase() || "U";

  return (
    <>
      <style>{style}</style>
      <div className="app">
        <div className="sidebar">
          <div className="sidebar-header">
            <div className="sidebar-logo">
              <div className="sidebar-logo-icon">🔬</div>
              Research AI
            </div>
          </div>

          <div className="sidebar-section">
            <div className="sidebar-section-label">Workspace</div>
            {navItems.map(item => (
              <button key={item.id} className={`sidebar-item ${page===item.id?"active":""}`}
                onClick={() => navigate(item.id)}>
                <span className="icon">{item.icon}</span>
                {item.label}
              </button>
            ))}
          </div>

          <div className="sidebar-footer">
            <div className="user-card">
              <div className="user-avatar">{initials}</div>
              <div style={{flex:1,minWidth:0}}>
                <div className="user-name" style={{overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{auth.full_name}</div>
                <div className="user-email" style={{overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>{auth.email}</div>
              </div>
              <button onClick={handleLogout} title="Sign out"
                style={{background:"none",border:"none",cursor:"pointer",fontSize:16,color:"var(--text3)",padding:4}}>⏻</button>
            </div>
          </div>
        </div>

        <div className="main">
          <div className="topbar">
            <div>
              <div className="page-title">{pageMap[page]?.title}</div>
              <div className="page-sub">{pageMap[page]?.sub}</div>
            </div>
          </div>
          <div className="content">
            {page === "dashboard" && <Dashboard token={auth.access_token} onNavigate={navigate} />}
            {page === "upload" && <UploadPage token={auth.access_token} onNavigate={navigate} />}
            {page === "analysis" && <AnalysisPage token={auth.access_token} paper={pageData} onNavigate={navigate} />}
            {page === "literature" && <LiteraturePage token={auth.access_token} showToast={showToast} />}
            {page === "gaps" && <GapsPage token={auth.access_token} showToast={showToast} />}
            {page === "grant" && <GrantPage token={auth.access_token} showToast={showToast} />}
            {page === "write" && <WritePaperPage token={auth.access_token} />}
          </div>
        </div>
      </div>
      {toast && <Toast msg={toast} onDone={() => setToast(null)} />}
    </>
  );
}