document.addEventListener("DOMContentLoaded", () => {

    const connectBtn = document.getElementById("connect-btn");
    const syncBtn = document.getElementById("sync-btn");
    const figmaInput = document.getElementById("figma-input");
    const connectStatus = document.getElementById("connect-status");
    const syncStatus = document.getElementById("sync-status");
    const syncInsight = document.getElementById("sync-insight");
    const insightsList = document.getElementById("insights-list");

    function escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    }

    function formatAiHtml(text) {
        return escapeHtml(text).replace(/\n/g, "<br>");
    }

    function buildAiCard(summary, timestamp, label) {
        return `
            <div class="ai-card">
                <div class="ai-card-header">
                    <img src="/static/images/chat.svg" width="28" height="28" alt="">
                    <span class="ai-card-meta">${label} · ${timestamp}</span>
                </div>
                <div class="ai-output">${formatAiHtml(summary)}</div>
            </div>
        `;
    }

    if (connectBtn) {
        connectBtn.addEventListener("click", async () => {
            const value = figmaInput.value.trim();
            if (!value) {
                connectStatus.textContent = "Please paste a Figma URL or file key.";
                return;
            }

            connectBtn.disabled = true;
            connectStatus.textContent = "Connecting...";

            try {
                const res = await fetch(`/project/${PROJECT_ID}/figma/connect`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ file_key: value }),
                });

                const data = await res.json();

                if (data.success) {
                    connectStatus.textContent = data.message;
                    setTimeout(() => window.location.reload(), 800);
                } else {
                    connectStatus.textContent = "Error: " + data.message;
                }
            } catch (err) {
                connectStatus.textContent = "Network error: " + err.message;
            } finally {
                connectBtn.disabled = false;
            }
        });
    }

    if (syncBtn) {
        syncBtn.addEventListener("click", async () => {
            syncBtn.disabled = true;
            syncStatus.textContent = "Syncing from Figma... (AI may take 10–20 sec)";
            syncInsight.innerHTML = "";

            try {
                const res = await fetch(`/project/${PROJECT_ID}/figma/sync`, {
                    method: "POST",
                });

                const data = await res.json();

                if (data.success) {
                    syncStatus.textContent = data.message;

                    if (data.insight) {
                        const noInsights = document.getElementById("no-insights");
                        if (noInsights) noInsights.remove();

                        const wrapper = document.createElement("div");
                        wrapper.innerHTML = buildAiCard(
                            data.insight.summary,
                            data.insight.created_at,
                            "Design Alert"
                        );

                        if (insightsList) {
                            insightsList.prepend(wrapper.firstElementChild);
                        }

                        syncInsight.innerHTML = `
                            <div class="alert alert-warning mt-2">
                                <strong>New AI insight</strong>
                            </div>
                        ` + buildAiCard(
                            data.insight.summary,
                            data.insight.created_at,
                            "Just now"
                        );
                    }
                } else {
                    syncStatus.textContent = "Error: " + data.message;
                }
            } catch (err) {
                syncStatus.textContent = "Network error: " + err.message;
            } finally {
                syncBtn.disabled = false;
            }
        });
    }
});
