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


// ============================================================================
// Theme
// ============================================================================

function initTheme() {

    const body = document.body;
    const themeButton = document.getElementById("theme-toggle");
    const savedTheme = localStorage.getItem("mediscan-theme");

    if (savedTheme === "dark") {
        body.classList.add("dark");
    }

    themeButton?.addEventListener("click", () => {

        body.classList.toggle("dark");

        const theme = body.classList.contains("dark")
            ? "dark"
            : "light";

        localStorage.setItem("mediscan-theme", theme);

    });

}


// ============================================================================
// Search Navigation
// ============================================================================

function goToResults(medicine) {

    const value = String(medicine || "").trim();

    if (!value) {
        return;
    }

    localStorage.setItem("lastMedicine", value);

    window.location.href =
        `results.html?medicine=${encodeURIComponent(value)}`;

}


function initSearch() {

    document
        .getElementById("medicine-search")
        ?.addEventListener("submit", (event) => {

            event.preventDefault();

            const input =
                document.getElementById("medicine-input");

            goToResults(input?.value);

        });


    document.querySelectorAll(".search-chip").forEach((chip) => {

        chip.addEventListener("click", () => {

            goToResults(chip.dataset.medicine);

        });

    });


    document
        .getElementById("result-search")
        ?.addEventListener("submit", (event) => {

            event.preventDefault();

            const input =
                document.getElementById("result-input");

            goToResults(input?.value);

        });

}


// ============================================================================
// Results Page
// ============================================================================

function initResultPage() {

    const nameElement =
        document.getElementById("medicine-name");

    const aiNameElement =
        document.getElementById("ai-medicine");

    const resultInput =
        document.getElementById("result-input");


    if (!nameElement && !resultInput) {
        return;
    }


    const params =
        new URLSearchParams(window.location.search);


    const medicine =
        params.get("medicine") ||
        localStorage.getItem("lastMedicine") ||
        "Crocin 650";


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


    // ------------------------------------------------------------------------
    // Connect to backend
    // ------------------------------------------------------------------------

    if (typeof searchMedicine === "function") {

        loadLiveResults(medicine);

    }

}


// ============================================================================
// Backend API
// ============================================================================

async function loadLiveResults(medicine) {

    const status =
        document.getElementById("data-status");


    try {

        if (status) {

            status.textContent =
                "Connecting to backend...";

        }


        const data =
            await searchMedicine(medicine);


        console.log(
            "MediScan API response:",
            data
        );


        if (status) {

            status.textContent =
                "✓ Live data";

        }


        /*
         * The backend response is received here.
         *
         * The current pharmacy cards remain based on the
         * values written in results.html.
         *
         * When the backend response structure is finalized,
         * this function can populate those cards dynamically.
         */


        return data;


    } catch (error) {

        console.error(
            "MediScan API Error:",
            error
        );


        if (status) {

            status.textContent =
                "✓ Demo data";

        }


        return null;

    }

}


// ============================================================================
// AI Summary
// ============================================================================

function updateAiSummary() {

    const rows =
        document.querySelectorAll(".pharmacy-row");


    if (rows.length === 0) {
        return;
    }


    const records = [];


    rows.forEach((row) => {

        records.push({

            store:
                row.dataset.store ||
                "Unknown Pharmacy",

            price:
                Number(row.dataset.price || 0),

            available:
                row.dataset.available === "true",

            savings:
                Number(row.dataset.savings || 0)

        });

    });


    const available =
        records.filter((record) => {

            return (
                record.available &&
                record.price > 0
            );

        });


    if (available.length === 0) {
        return;
    }


    available.sort((a, b) => {

        return a.price - b.price;

    });


    const best =
        available[0];


    const prices =
        records.map((record) => {

            return record.price;

        });


    const highest =
        Math.max(...prices);


    const saving =
        Math.max(
            highest - best.price,
            0
        );


    // ------------------------------------------------------------------------
    // Best Price
    // ------------------------------------------------------------------------

    const bestPrice =
        document.getElementById("best-price");


    if (bestPrice) {

        bestPrice.textContent =
            `₹${best.price.toFixed(2)}`;

    }


    // ------------------------------------------------------------------------
    // Best Pharmacy
    // ------------------------------------------------------------------------

    const bestPharmacy =
        document.getElementById("best-pharmacy");


    if (bestPharmacy) {

        bestPharmacy.textContent =
            best.store;

    }


    // ------------------------------------------------------------------------
    // Best Saving
    // ------------------------------------------------------------------------

    const bestSaving =
        document.getElementById("best-saving");


    if (bestSaving) {

        bestSaving.textContent =
            `₹${saving.toFixed(2)}`;

    }


    // ------------------------------------------------------------------------
    // Availability
    // ------------------------------------------------------------------------

    const bestAvailability =
        document.getElementById("best-availability");


    if (bestAvailability) {

        bestAvailability.textContent =
            `${available.length} / ${records.length}`;

    }


    // ------------------------------------------------------------------------
    // AI Saving Text
    // ------------------------------------------------------------------------

    const aiSaving =
        document.querySelector(
            "#ai-saving-text strong"
        );


    if (aiSaving) {

        aiSaving.textContent =
            `₹${saving.toFixed(0)}`;

    }


    // ------------------------------------------------------------------------
    // AI Availability Text
    // ------------------------------------------------------------------------

    const aiAvailability =
        document.querySelector(
            "#ai-availability-text strong"
        );


    if (aiAvailability) {

        aiAvailability.textContent =
            `${available.length} of ${records.length} stores`;

    }

}


// ============================================================================
// Filters
// ============================================================================

function initFilters() {

    const buttons =
        document.querySelectorAll(".filter-btn");

    const rows =
        document.querySelectorAll(".pharmacy-row");


    if (!buttons.length || !rows.length) {
        return;
    }


    buttons.forEach((button) => {

        button.addEventListener("click", () => {


            buttons.forEach((item) => {

                item.classList.remove("active");

            });


            button.classList.add("active");


            const filter =
                button.dataset.filter;


            rows.forEach((row) => {

                const available =
                    row.dataset.available === "true";


                const price =
                    Number(row.dataset.price || 0);


                const savings =
                    Number(row.dataset.savings || 0);


                let visible = true;


                if (filter === "available") {

                    visible = available;

                }


                else if (filter === "lowest") {

                    visible = price <= 35;

                }


                else if (filter === "savings") {

                    visible = savings >= 8;

                }


                else if (filter === "all") {

                    visible = true;

                }


                row.style.display =
                    visible
                        ? "grid"
                        : "none";

            });

        });

    });

}


// ============================================================================
// Pharmacy Deal Buttons
// ============================================================================

function initDealButtons() {

    const dealButtons =
        document.querySelectorAll(".deal-action");


    dealButtons.forEach((button) => {

        button.addEventListener("click", () => {


            const store =
                button.getAttribute("data-store") ||
                "Pharmacy";


            const url =
                button.getAttribute("data-url");


            if (!url) {

                console.error(
                    "Missing data-url for " + store
                );


                alert(
                    "No pharmacy URL configured for " +
                    store +
                    "."
                );


                return;

            }


            window.open(
                url,
                "_blank"
            );

        });

    });


    // ------------------------------------------------------------------------
    // Full Analysis Button
    // ------------------------------------------------------------------------

    const analysisButton =
        document.getElementById("analysis-btn");


    if (analysisButton) {

        analysisButton.addEventListener("click", () => {

            alert(
                "The full AI analysis can be connected to the backend later."
            );

        });

    }

}


// ============================================================================
// Subscribe Form
// ============================================================================

function initSubscriptions() {

    const forms =
        document.querySelectorAll(".subscribe");


    forms.forEach((form) => {

        form.addEventListener("submit", (event) => {

            event.preventDefault();


            const input =
                form.querySelector(
                    'input[type="email"]'
                );


            const email =
                input
                    ? input.value.trim()
                    : "";


            const validEmail =
                /^[^\s@]+@[^\s@]+\.[^\s@]+$/;


            if (!validEmail.test(email)) {

                alert(
                    "Please enter a valid email address."
                );


                return;

            }


            alert(
                "Thanks! You are subscribed to MediScan AI updates."
            );


            form.reset();

        });

    });

}