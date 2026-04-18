let allRecords = [];
let currentRows = [];
let rawJson = null;

async function loadDashboardData(showAlertOnError = true) {
    try {
        const response = await fetch("master_leads.json?ts=" + Date.now());
        if (!response.ok) {
            throw new Error("HTTP " + response.status);
        }

        const data = await response.json();
        rawJson = data;
        allRecords = data.records || [];

 renderStats(data);
renderLastUpdated(data.generated_at);
renderTop25NewLeads(allRecords);
applyFilters(false);
    } catch (error) {
        console.error("Error loading JSON:", error);
        if (showAlertOnError) {
            alert("Could not load master_leads.json");
        }
    }
}

function renderStats(data) {
    document.getElementById("totalLeads").textContent = data.total_leads || 0;
    document.getElementById("taxLeads").textContent = data.tax_sale_leads || 0;
    document.getElementById("probateLeads").textContent = data.probate_leads || 0;
    document.getElementById("stackedLeads").textContent = data.stacked_leads || 0;
    document.getElementById("highScoreLeads").textContent = data.high_score_leads || 0;
    const newCount = allRecords.filter(record => isNewSinceYesterday(record)).length;
const el = document.getElementById("newSinceYesterdayCount");
if (el) el.textContent = newCount;
}

function renderLastUpdated(value) {
    const el = document.getElementById("lastUpdated");

    if (!value) {
        el.textContent = "Last update: unknown";
        return;
    }

    const dt = new Date(value);
    if (isNaN(dt.getTime())) {
        el.textContent = "Last update: " + value;
        return;
    }

    el.textContent = "Last update: " + dt.toLocaleString();
}

function applyFilters(scrollTop = false) {
    const searchValue = document.getElementById("searchInput").value.toLowerCase().trim();
    const filterType = document.getElementById("filterType").value;
    const sortType = document.getElementById("sortType").value;

    let filtered = [...allRecords];

    if (searchValue) {
        filtered = filtered.filter(record =>
            (record.owner || "").toLowerCase().includes(searchValue)
        );
    }

    if (filterType === "stacked") {
        filtered = filtered.filter(record =>
            record.tax_sale === "YES" && record.probate === "YES"
        );
    } else if (filterType === "tax") {
        filtered = filtered.filter(record => record.tax_sale === "YES");
    } else if (filterType === "probate") {
        filtered = filtered.filter(record => record.probate === "YES");
    } else if (filterType === "high70") {
        filtered = filtered.filter(record => Number(record.score) >= 70);
    } else if (filterType === "high80") {
        filtered = filtered.filter(record => Number(record.score) >= 80);
    } else if (filterType === "high90") {
        filtered = filtered.filter(record => Number(record.score) >= 90);
    } else if (filterType === "probate_high") {
        filtered = filtered.filter(record =>
            record.probate === "YES" && Number(record.score) >= 70
        );
    } else if (filterType === "tax_high") {
        filtered = filtered.filter(record =>
            record.tax_sale === "YES" && Number(record.score) >= 70
        );
    } else if (filterType === "business_high") {
        filtered = filtered.filter(record => {
            const tags = Array.isArray(record.tags) ? record.tags.join(", ") : (record.tags || "");
            return tags.toLowerCase().includes("business owner") && Number(record.score) >= 70;
        });
    }

    if (sortType === "score_desc") {
        filtered.sort((a, b) => Number(b.score) - Number(a.score));
    } else if (sortType === "score_asc") {
        filtered.sort((a, b) => Number(a.score) - Number(b.score));
    } else if (sortType === "owner_asc") {
        filtered.sort((a, b) => (a.owner || "").localeCompare(b.owner || ""));
    } else if (sortType === "amount_desc") {
        filtered.sort((a, b) => Number(b.amount_due_num || 0) - Number(a.amount_due_num || 0));
    }

    currentRows = filtered;
    renderTable(filtered);
    renderResultsCount(filtered.length);

    if (scrollTop) {
        window.scrollTo({ top: 0, behavior: "smooth" });
    }
}

function renderResultsCount(count) {
    document.getElementById("resultsCount").textContent = `Showing ${count} leads`;
}

function renderTable(records) {
    const tbody = document.querySelector("#leadsTable tbody");
    tbody.innerHTML = "";

    records.forEach(record => {
        const tr = document.createElement("tr");

        const tags = Array.isArray(record.tags) ? record.tags.join(", ") : (record.tags || "");
        const score = Number(record.score || 0);

        tr.innerHTML = `
            <td>${escapeHtml(record.owner || "")}</td>
            <td>${escapeHtml(record.tax_sale || "")}</td>
            <td>${escapeHtml(record.probate || "")}</td>
            <td>${escapeHtml(record.parcel || "")}</td>
            <td>${escapeHtml(record.amount_due || "")}</td>
            <td>${escapeHtml(record.case_number || "")}</td>
            <td class="${score >= 80 ? "high-score" : score >= 70 ? "medium-score" : ""}">${score}</td>
            <td>${escapeHtml(tags)}</td>
        `;

        tbody.appendChild(tr);
    });
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function convertRowsToCsv(rows) {
    const headers = ["owner", "tax_sale", "probate", "parcel", "amount_due", "case_number", "score", "tags"];
    const lines = [headers.join(",")];

    for (const row of rows) {
        const tags = Array.isArray(row.tags) ? row.tags.join(" | ") : (row.tags || "");
        const values = [
            row.owner || "",
            row.tax_sale || "",
            row.probate || "",
            row.parcel || "",
            row.amount_due || "",
            row.case_number || "",
            row.score ?? "",
            tags
        ].map(v => `"${String(v).replaceAll('"', '""')}"`);

        lines.push(values.join(","));
    }

    return lines.join("\n");
}

function downloadFile(filename, content, type) {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();

    URL.revokeObjectURL(url);
}
function renderTop25NewLeads(records) {
document.getElementById("searchInput").addEventListener("input", () => applyFilters(false));
document.getElementById("filterType").addEventListener("change", () => applyFilters(true));
document.getElementById("sortType").addEventListener("change", () => applyFilters(false));

document.querySelectorAll(".quick-filter-btn").forEach(btn => {
    btn.addEventListener("click", () => {
        document.getElementById("filterType").value = btn.dataset.filter;
        applyFilters(true);
    });
});

document.getElementById("refreshBtn").addEventListener("click", () => {
    const section = document.getElementById("top25NewSection");
    const tbody = document.querySelector("#top25NewTable tbody");

    if (!section || !tbody) return;

    const newestBest = records
        .filter(record => isNewSinceYesterday(record))
        .sort((a, b) => {
            const scoreDiff = Number(b.score || 0) - Number(a.score || 0);
            if (scoreDiff !== 0) return scoreDiff;
            return Number(b.amount_due_num || 0) - Number(a.amount_due_num || 0);
        })
        .slice(0, 25);

    tbody.innerHTML = "";

    newestBest.forEach((record, idx) => {
        const tags = Array.isArray(record.tags) ? record.tags.join(", ") : (record.tags || "");
        const score = Number(record.score || 0);

        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${idx + 1}</td>
            <td>${escapeHtml(record.owner || "")}</td>
            <td>${escapeHtml(record.parcel || "")}</td>
            <td>${escapeHtml(record.amount_due || "")}</td>
            <td>${score}</td>
            <td>${escapeHtml(tags)}</td>
        `;
        tbody.appendChild(tr);
    });

    section.style.display = newestBest.length ? "block" : "none";
}
    loadDashboardData(true);
});

document.getElementById("downloadCsvBtn").addEventListener("click", () => {
    const csv = convertRowsToCsv(currentRows);
    downloadFile("visible_leads.csv", csv, "text/csv;charset=utf-8;");
});

document.getElementById("downloadJsonBtn").addEventListener("click", () => {
    const content = JSON.stringify({ records: currentRows }, null, 2);
    downloadFile("visible_leads.json", content, "application/json;charset=utf-8;");
});

// auto refresh every 15 minutes
setInterval(() => {
    loadDashboardData(false);
}, 15 * 60 * 1000);

loadDashboardData(true);
