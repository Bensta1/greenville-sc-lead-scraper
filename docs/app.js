let allRecords = [];
let currentRows = [];
let rawJson = null;

function isNewSinceYesterday(record) {
    if (!record.generated_at) return false;

    const leadDate = new Date(record.generated_at);
    if (isNaN(leadDate.getTime())) return false;

    const now = new Date();
    const yesterday = new Date(now);
    yesterday.setDate(now.getDate() - 1);
    yesterday.setHours(0, 0, 0, 0);

    return leadDate >= yesterday;
}

async function loadDashboardData(showAlertOnError = true) {
    try {
        // ✅ FIXED PATH HERE
        const response = await fetch("master_leads.json?ts=" + Date.now())

        if (!response.ok) {
            throw new Error("HTTP " + response.status);
        }

        const data = await response.json();
        rawJson = data;
        allRecords = data.records || [];

        renderStats(data);
        renderLastUpdated(data.generated_at);
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
    }

    if (sortType === "score_desc") {
        filtered.sort((a, b) => Number(b.score) - Number(a.score));
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

function renderTable(rows) {
    const tbody = document.querySelector("#mainTable tbody");
    if (!tbody) return;

    tbody.innerHTML = "";

    rows.forEach((r, index) => {
        const tr = document.createElement("tr");

        tr.innerHTML = `
            <td>${index + 1}</td>
            <td>${r.owner || ""}</td>
            <td>${r.tax_sale}</td>
            <td>${r.probate}</td>
            <td>${r.parcel || ""}</td>
            <td>${r.amount_due || ""}</td>
            <td>${r.case_number || ""}</td>
            <td>${r.score}</td>
            <td>${(r.tags || []).join(", ")}</td>
        `;

        tbody.appendChild(tr);
    });
}

// ✅ AUTO LOAD DASHBOARD
document.addEventListener("DOMContentLoaded", () => {
    loadDashboardData();
});
