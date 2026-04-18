let allRecords = [];

fetch("master_leads.json")
    .then(response => response.json())
    .then(data => {
        allRecords = data.records || [];
        renderStats(data);
        applyFilters();
    })
    .catch(error => {
        console.error("Error loading JSON:", error);
        alert("Could not load master_leads.json");
    });

function renderStats(data) {
    document.getElementById("totalLeads").textContent = data.total_leads || 0;
    document.getElementById("taxLeads").textContent = data.tax_sale_leads || 0;
    document.getElementById("probateLeads").textContent = data.probate_leads || 0;
    document.getElementById("stackedLeads").textContent = data.stacked_leads || 0;
    document.getElementById("highScoreLeads").textContent = data.high_score_leads || 0;
}

function applyFilters() {
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
    } else if (filterType === "high") {
        filtered = filtered.filter(record => Number(record.score) >= 70);
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

    renderTable(filtered);
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
            <td class="${score >= 70 ? "high-score" : ""}">${score}</td>
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

document.getElementById("searchInput").addEventListener("input", applyFilters);
document.getElementById("filterType").addEventListener("change", applyFilters);
document.getElementById("sortType").addEventListener("change", applyFilters);