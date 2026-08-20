// ============================================================================
// MediScan AI - Frontend interactions
// ============================================================================

document.addEventListener("DOMContentLoaded", () => {
    initTheme();
    initSearch();
    initResultPage();
    initFilters();
    initDealButtons();
    initSubscriptions();
});

// ----------------------------------------------------------------------------
// Theme
// ----------------------------------------------------------------------------
function initTheme() {
    const body = document.body;
    const themeButton = document.getElementById("theme-toggle");

    const savedTheme = localStorage.getItem("mediscan-theme");

    if (savedTheme === "dark") {
        body.classList.add("dark");
    }

    themeButton?.addEventListener("click", () => {
        body.classList.toggle("dark");

        const theme = body.classList.contains("dark") ? "dark" : "light";
        localStorage.setItem("mediscan-theme", theme);
    });
}

// ----------------------------------------------------------------------------
// Search navigation
// ----------------------------------------------------------------------------
function goToResults(medicine) {
    const value = String(medicine || "").trim();

    if (!value) {
        return;
    }

    localStorage.setItem("lastMedicine", value);
    window.location.href = `results.html?medicine=${encodeURIComponent(value)}`;
}

function initSearch() {
    document.getElementById("medicine-search")?.addEventListener("submit", (event) => {
        event.preventDefault();

        const input = document.getElementById("medicine-input");
        goToResults(input?.value);
    });

    document.querySelectorAll(".search-chip").forEach((chip) => {
        chip.addEventListener("click", () => {
            goToResults(chip.dataset.medicine);
        });
    });

    document.getElementById("result-search")?.addEventListener("submit", (event) => {
        event.preventDefault();

        const input = document.getElementById("result-input");
        goToResults(input?.value);
    });
}

// ----------------------------------------------------------------------------
// Results page
// ----------------------------------------------------------------------------
function initResultPage() {
    const nameElement = document.getElementById("medicine-name");
    const aiNameElement = document.getElementById("ai-medicine");
    const resultInput = document.getElementById("result-input");

    if (!nameElement && !resultInput) {
        return;
    }

    const params = new URLSearchParams(window.location.search);
    const medicine = params.get("medicine") || localStorage.getItem("lastMedicine") || "Crocin 650";

    if (nameElement) {
        nameElement.textContent = medicine;
    }

    if (aiNameElement) {
        aiNameElement.textContent = medicine;
    }

    if (resultInput) {
        resultInput.value = medicine;
    }

    updateAiSummary();

    // Live backend can be enabled later without changing the page structure.
    if (typeof searchMedicine === "function" && window.MEDISCAN_API_URL) {
        loadLiveResults(medicine);
    }
}

async function loadLiveResults(medicine) {
    const status = document.getElementById("data-status");

    try {
        const data = await searchMedicine(medicine);
        console.log("MediScan API response:", data);

        if (status) {
            status.textContent = "✓ Live data";
        }
    } catch (error) {
        console.warn("Live API unavailable. Keeping demo results.", error);

        if (status) {
            status.textContent = "✓ Demo data";
        }
    }
}

function updateAiSummary() {
    const rows = Array.from(document.querySelectorAll(".pharmacy-row"));

    if (!rows.length) {
        return;
    }

    const records = rows.map((row) => ({
        store: row.dataset.store,
        price: Number(row.dataset.price),
        available: row.dataset.available === "true",
        savings: Number(row.dataset.savings || 0)
    }));

    const available = records.filter((record) => record.available);
    const sorted = [...available].sort((a, b) => a.price - b.price);
    const best = sorted[0];
    const highest = Math.max(...records.map((record) => record.price));
    const saving = Math.max(highest - best.price, 0);

    document.getElementById("best-price")?.replaceChildren(document.createTextNode(`₹${best.price.toFixed(2)}`));
    document.getElementById("best-pharmacy")?.replaceChildren(document.createTextNode(best.store));
    document.getElementById("best-saving")?.replaceChildren(document.createTextNode(`₹${saving.toFixed(2)}`));
    document.getElementById("best-availability")?.replaceChildren(document.createTextNode(`${available.length} / ${records.length}`));

    const aiSaving = document.querySelector("#ai-saving-text strong");
    const aiAvailability = document.querySelector("#ai-availability-text strong");

    if (aiSaving) {
        aiSaving.textContent = `₹${saving.toFixed(0)}`;
    }

    if (aiAvailability) {
        aiAvailability.textContent = `${available.length} of ${records.length} stores`;
    }
}

// ----------------------------------------------------------------------------
// Filters
// ----------------------------------------------------------------------------
function initFilters() {
    const buttons = document.querySelectorAll(".filter-btn");
    const rows = document.querySelectorAll(".pharmacy-row");

    if (!buttons.length || !rows.length) {
        return;
    }

    buttons.forEach((button) => {
        button.addEventListener("click", () => {
            buttons.forEach((item) => item.classList.remove("active"));
            button.classList.add("active");

            const filter = button.dataset.filter;

            rows.forEach((row) => {
                const available = row.dataset.available === "true";
                const price = Number(row.dataset.price);

                let visible = true;

                if (filter === "available") {
                    visible = available;
                } else if (filter === "lowest") {
                    visible = price <= 35;
                } else if (filter === "savings") {
                    visible = Number(row.dataset.savings) >= 8;
                }

                row.style.display = visible ? "grid" : "none";
            });
        });
    });
}

// ----------------------------------------------------------------------------
// Deal buttons
// ----------------------------------------------------------------------------
function initDealButtons() {
    document.querySelectorAll(".deal-action").forEach((button) => {
        button.addEventListener("click", () => {
            const store = button.dataset.store || "selected pharmacy";
            alert(`Selected deal: ${store}\n\nConnect this action to the pharmacy URL or backend when the project is ready.`);
        });
    });

    document.getElementById("analysis-btn")?.addEventListener("click", () => {
        alert("The full AI analysis can be connected to the backend later.");
    });
}

// ----------------------------------------------------------------------------
// Subscribe form
// ----------------------------------------------------------------------------
function initSubscriptions() {
    document.querySelectorAll(".subscribe").forEach((form) => {
        form.addEventListener("submit", (event) => {
            event.preventDefault();

            const input = form.querySelector('input[type="email"]');
            const email = input?.value.trim() || "";
            const validEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

            if (!validEmail.test(email)) {
                alert("Please enter a valid email address.");
                return;
            }

            alert("Thanks! You are subscribed to MediScan AI updates.");
            form.reset();
        });
    });
}
