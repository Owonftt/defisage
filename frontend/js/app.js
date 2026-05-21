/**
 * DeFiSage frontend logic — talks to the FastAPI backend at the same origin
 * (or override window.DEFISAGE_API_BASE in the page if hosted separately).
 */

const API_BASE = window.DEFISAGE_API_BASE || (location.hostname === "localhost" || location.hostname === "127.0.0.1"
    ? "http://localhost:8000"
    : "");

const fmt = {
    int: (n) => Number(n || 0).toLocaleString("en-US"),
    pct: (n) => `${(n || 0).toFixed(1)}%`,
    short: (s, n = 60) => (s && s.length > n ? s.slice(0, n) + "…" : s || ""),
    duration: (s) => {
        s = Math.floor(s || 0);
        if (s < 60) return `${s}s`;
        if (s < 3600) return `${Math.floor(s / 60)}m`;
        return `${(s / 3600).toFixed(1)}h`;
    }
};

// ---------- Tab navigation ----------
document.querySelectorAll(".nav-link").forEach((link) => {
    link.addEventListener("click", (e) => {
        e.preventDefault();
        const target = link.dataset.tab;
        document.querySelectorAll(".nav-link").forEach((n) => n.classList.remove("active"));
        link.classList.add("active");
        document.querySelectorAll(".tab-content").forEach((s) => s.classList.remove("active"));
        document.getElementById(`tab-${target}`).classList.add("active");
    });
});

// ---------- Stats polling ----------
async function fetchJSON(url, opts = {}) {
    const r = await fetch(`${API_BASE}${url}`, opts);
    if (!r.ok) {
        const text = await r.text();
        throw new Error(`HTTP ${r.status}: ${text.slice(0, 200)}`);
    }
    return r.json();
}

async function pollStats() {
    try {
        const stats = await fetchJSON("/api/stats");
        document.getElementById("statTokens").textContent = fmt.int(stats.total_tokens_today);
        document.getElementById("statCalls").textContent = fmt.int(stats.api_calls_today);
        document.getElementById("statAnalyses").textContent = fmt.int(stats.analyses_completed);
        document.getElementById("statUptime").textContent = fmt.duration(stats.uptime_seconds);
        document.getElementById("tokenCount").textContent = fmt.int(stats.total_tokens_today);

        const pct = Math.min(100, stats.budget_used_pct || 0);
        document.getElementById("tokenBar").style.width = `${pct}%`;

        const breakdown = stats.agent_breakdown || {};
        document.getElementById("agentRisk").textContent = `${fmt.int(breakdown.risk_scanner || 0)} tokens`;
        document.getElementById("agentTokens").textContent = `${fmt.int(breakdown.tokenomics_auditor || 0)} tokens`;
        document.getElementById("agentGov").textContent = `${fmt.int(breakdown.governance_analyst || 0)} tokens`;
        document.getElementById("agentThesis").textContent = `${fmt.int(breakdown.thesis_composer || 0)} tokens`;

        document.getElementById("statusDot").classList.remove("error");
    } catch (err) {
        console.warn("stats poll failed", err);
        document.getElementById("statusDot").classList.add("error");
    }
}

async function pollTrend() {
    try {
        const { trend } = await fetchJSON("/api/stats/trend?days=7");
        const max = Math.max(1, ...trend.map((d) => d.tokens));
        const html = trend
            .map((d) => {
                const h = (d.tokens / max) * 100;
                const date = d.date.slice(5);
                return `<div class="trend-bar" style="height:${h}%" title="${date}: ${fmt.int(d.tokens)} tokens">
                            <span class="trend-bar-label">${date}</span>
                        </div>`;
            })
            .join("");
        document.getElementById("trendChart").innerHTML = html || `<div class="empty-state">No data yet</div>`;
    } catch (err) {
        console.warn("trend poll failed", err);
    }
}

// ---------- Render analysis result ----------
function renderAnalysis(result) {
    if (!result) return "(empty result)";
    const c = result.complexity || {};
    const p = result.pipeline || {};

    const block = (title, agent) => {
        if (!agent || !agent.result) return "";
        const tokens = fmt.int(agent.tokens_used || 0);
        const elapsed = (agent.elapsed || 0).toFixed(1);
        const chunks = agent.chunks_analyzed ? `· ${agent.chunks_analyzed} chunks` : "";
        return `<div class="result-section">
            <h4>${title}</h4>
            <div class="meta">${tokens} tokens · ${elapsed}s ${chunks}</div>
            <div>${escapeHtml(agent.result)}</div>
        </div>`;
    };

    const validation = result.validation || {};
    const issues = validation.issues && validation.issues.length
        ? `<div class="meta">⚠️ ${validation.issues.join(" · ")}</div>` : "";

    return `
        <div class="result-section">
            <h4>📌 Analysis Header</h4>
            <div class="meta">
                ID: <span class="mono">${result.analysis_id}</span> ·
                Protocol: <strong>${escapeHtml(result.protocol_name)}</strong> ·
                Chain: ${escapeHtml(result.chain_hint || "?")}<br>
                Complexity: <strong>${c.level}</strong> (score ${c.score}, ~${c.expected_chunks} chunks) ·
                Total tokens: <strong>${fmt.int(result.total_tokens_used)}</strong> ·
                Elapsed: <strong>${result.total_elapsed_seconds}s</strong>
            </div>
            ${issues}
        </div>
        ${block("🛡️ Risk Scan", p.risk_scan)}
        ${block("💰 Tokenomics Audit", p.tokenomics_audit)}
        ${block("🏛️ Governance Analysis", p.governance_analysis)}
        ${block("📜 Final Thesis", p.thesis_synthesis)}
    `;
}

function escapeHtml(s) {
    return String(s ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

function setLoading(area, msg = "Running multi-agent pipeline (this can take 30-90s)...") {
    area.innerHTML = `<div><span class="spinner"></span>${msg}</div>`;
}

// ---------- Analyze tab ----------
document.getElementById("btnScaffold").addEventListener("click", async () => {
    const name = document.getElementById("protocolName").value.trim() || "Unknown Protocol";
    const chain = document.getElementById("protocolChain").value.trim() || "Ethereum";
    try {
        const r = await fetchJSON("/api/scaffold", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ protocol_name: name, chain }),
        });
        document.getElementById("protocolSnapshot").value = r.snapshot;
    } catch (err) {
        alert(`Scaffold error: ${err.message}`);
    }
});

document.getElementById("btnAnalyze").addEventListener("click", async () => {
    const snapshot = document.getElementById("protocolSnapshot").value.trim();
    if (!snapshot) return alert("Please paste a protocol snapshot first.");

    const protocolName = document.getElementById("protocolName").value.trim() || "Unknown Protocol";
    const chain = document.getElementById("protocolChain").value.trim() || "Ethereum";
    const runGov = document.getElementById("runGovernance").checked;
    const area = document.getElementById("analyzeResult");
    const btn = document.getElementById("btnAnalyze");

    btn.disabled = true;
    setLoading(area);

    try {
        const result = await fetchJSON("/api/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                snapshot,
                protocol_name: protocolName,
                chain,
                run_governance: runGov,
            }),
        });
        area.innerHTML = renderAnalysis(result);
        pollStats();
    } catch (err) {
        area.innerHTML = `<div class="severity-high">Analyze failed: ${escapeHtml(err.message)}</div>`;
    } finally {
        btn.disabled = false;
    }
});

document.getElementById("btnUpload").addEventListener("click", () => {
    document.getElementById("fileInput").click();
});

document.getElementById("fileInput").addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const protocolName = document.getElementById("protocolName").value.trim() || file.name.replace(/\.[^.]+$/, "");
    const chain = document.getElementById("protocolChain").value.trim() || "Ethereum";
    const area = document.getElementById("analyzeResult");
    setLoading(area, "Uploading and analyzing...");

    const fd = new FormData();
    fd.append("file", file);
    fd.append("protocol_name", protocolName);
    fd.append("chain", chain);

    try {
        const r = await fetch(`${API_BASE}/api/upload`, { method: "POST", body: fd });
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const data = await r.json();
        area.innerHTML = renderAnalysis(data);
        pollStats();
    } catch (err) {
        area.innerHTML = `<div class="severity-high">Upload failed: ${escapeHtml(err.message)}</div>`;
    }
});

// ---------- Batch tab ----------
document.getElementById("btnBatch").addEventListener("click", async () => {
    const raw = document.getElementById("batchInput").value.trim();
    if (!raw) return alert("Paste at least one snapshot.");

    const parallel = document.getElementById("batchParallel").checked;
    const maxConcurrent = parseInt(document.getElementById("maxConcurrent").value) || 3;
    const area = document.getElementById("batchResult");
    const btn = document.getElementById("btnBatch");

    const protocols = raw
        .split(/^===PROTOCOL===\s*$/m)
        .map((s) => s.trim())
        .filter(Boolean)
        .map((s) => {
            const nameMatch = s.match(/^Name:\s*(.+)$/im) || s.match(/^# OVERVIEW\s*\nName:\s*(.+)$/im);
            const name = nameMatch ? nameMatch[1].trim() : "Unknown";
            return { snapshot: s, protocol_name: name, chain: "Ethereum", run_governance: true };
        });

    if (!protocols.length) {
        return alert("No valid protocols parsed. Use ===PROTOCOL=== separator.");
    }
    if (protocols.length > 10) {
        return alert("Max 10 per batch.");
    }

    btn.disabled = true;
    setLoading(area, `Running batch on ${protocols.length} protocols...`);

    try {
        const result = await fetchJSON("/api/batch-analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ protocols, parallel, max_concurrent: maxConcurrent }),
        });
        const sections = result.results.map((r, i) => {
            if (r.error) {
                return `<div class="result-section"><h4>Protocol ${i + 1}: ERROR</h4>${escapeHtml(r.error)}</div>`;
            }
            return `<div class="result-section">
                <h4>Protocol ${i + 1}: ${escapeHtml(r.protocol_name)}</h4>
                <div class="meta">tokens: ${fmt.int(r.total_tokens_used)} · ${r.total_elapsed_seconds}s · ${r.complexity?.level}</div>
                <div>${escapeHtml((r.report || "").slice(0, 1500))}…</div>
            </div>`;
        }).join("");
        area.innerHTML = `<div class="meta">batch ${result.batch_id} · ${result.total_protocols} protocols · parallel=${result.parallel}</div>${sections}`;
        pollStats();
    } catch (err) {
        area.innerHTML = `<div class="severity-high">Batch failed: ${escapeHtml(err.message)}</div>`;
    } finally {
        btn.disabled = false;
    }
});

// ---------- Chat tab ----------
const chatHistory = document.getElementById("chatHistory");
const chatInput = document.getElementById("chatInput");
const btnChat = document.getElementById("btnChat");

function addChatMsg(role, text) {
    const div = document.createElement("div");
    div.className = `chat-msg ${role}`;
    div.textContent = text;
    chatHistory.appendChild(div);
    chatHistory.scrollTop = chatHistory.scrollHeight;
    return div;
}

async function sendChat() {
    const msg = chatInput.value.trim();
    if (!msg) return;
    addChatMsg("user", msg);
    chatInput.value = "";

    const placeholder = addChatMsg("agent", "…thinking…");
    btnChat.disabled = true;

    try {
        const result = await fetchJSON("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: msg }),
        });
        placeholder.textContent = result.response || "(no response)";
        pollStats();
    } catch (err) {
        placeholder.textContent = `Error: ${err.message}`;
    } finally {
        btnChat.disabled = false;
    }
}

btnChat.addEventListener("click", sendChat);
chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
        sendChat();
    }
});

// ---------- Boot ----------
pollStats();
pollTrend();
setInterval(pollStats, 5000);
setInterval(pollTrend, 60_000);
