/**
 * Initialize all event listeners and DOM interactions
 */
document.addEventListener("DOMContentLoaded", () => {
    // ===== THEME TOGGLE =====
    const body = document.body;
    const themeButton = document.getElementById("theme-toggle");

    // Load saved theme preference
    if (localStorage.getItem("mediscan-theme") === "dark") {
        body.classList.add("dark");
    }

    // Toggle theme on button click
    themeButton?.addEventListener("click", () => {
        body.classList.toggle("dark");
        const theme = body.classList.contains("dark") ? "dark" : "light";
        localStorage.setItem("mediscan-theme", theme);
    });

    // ===== NAVIGATION FUNCTION =====
    const goToResults = (medicine) => {
        const value = medicine.trim();
        if (!value) return;
        localStorage.setItem("lastMedicine", value);
        window.location.href = `results.html?medicine=${encodeURIComponent(value)}`;
    };

    // ===== MAIN SEARCH FORM =====
    document.getElementById("medicine-search")?.addEventListener("submit", (e) => {
        e.preventDefault();
        const medicineInput = document.getElementById("medicine-input");
        goToResults(medicineInput.value);
    });

    // ===== SEARCH CHIPS =====
    document.querySelectorAll(".search-chip").forEach((chip) => {
        chip.addEventListener("click", () => {
            goToResults(chip.dataset.medicine);
        });
    });

    // ===== LOAD MEDICINE DATA =====
    const params = new URLSearchParams(window.location.search);
    const medicine = params.get("medicine") || localStorage.getItem("lastMedicine") || "Crocin 650";

    const name = document.getElementById("medicine-name");
    const aiName = document.getElementById("ai-medicine");
    const resultInput = document.getElementById("result-input");

    if (name) {
        name.textContent = medicine;
    }
    if (aiName) {
        aiName.textContent = medicine;
    }
    if (resultInput) {
        resultInput.value = medicine;
    }

    // ===== RESULTS PAGE SEARCH =====
    document.getElementById("result-search")?.addEventListener("submit", (e) => {
        e.preventDefault();
        goToResults(resultInput.value);
    });

    // ===== FILTER BUTTONS =====
    document.querySelectorAll(".filter-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
            // Remove active class from all buttons
            document.querySelectorAll(".filter-btn").forEach((button) => {
                button.classList.remove("active");
            });
            // Add active class to clicked button
            btn.classList.add("active");
        });
    });

    // ===== DEAL ACTION BUTTONS =====
    document.querySelectorAll(".deal-action").forEach((btn) => {
        btn.addEventListener("click", () => {
            const store = btn.dataset.store || "the selected pharmacy";
            alert(
                `Deal selected: ${store}\n\n` +
                `Connect this button to the pharmacy URL/API when the backend is ready.`
            );
        });
    });

    // ===== EMAIL SUBSCRIPTION =====
    document.querySelectorAll(".subscribe").forEach((form) => {
        form.addEventListener("submit", (e) => {
            e.preventDefault();
            const input = form.querySelector("input");
            
            // Validate email format
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!input.value.trim() || !emailRegex.test(input.value)) {
                alert("Please enter a valid email address.");
                return;
            }
            
            // Success message and reset
            alert("Thanks! You are subscribed to MediScan AI updates.");
            input.value = "";
        });
    });
});
