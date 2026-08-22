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

        localStorage.setItem(
            "mediscan-theme",
            theme
        );

    });

}


// ============================================================================
// Search Navigation
// ============================================================================

function goToResults(medicine) {

    const value =
        String(medicine || "").trim();

    if (!value) {
        return;
    }

    localStorage.setItem(
        "lastMedicine",
        value
    );

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

            goToResults(
                input?.value
            );

        });


    document
        .querySelectorAll(".search-chip")
        .forEach((chip) => {

            chip.addEventListener(
                "click",
                () => {

                    goToResults(
                        chip.dataset.medicine
                    );

                }
            );

        });


    document
        .getElementById("result-search")
        ?.addEventListener("submit", (event) => {

            event.preventDefault();

            const input =
                document.getElementById("result-input");

            goToResults(
                input?.value
            );

        });

}


// ============================================================================
// Results Page
// ============================================================================

function initResultPage() {

    const nameElement =
        document.getElementById(
            "medicine-name"
        );

    const aiNameElement =
        document.getElementById(
            "ai-medicine"
        );

    const resultInput =
        document.getElementById(
            "result-input"
        );


    if (
        !nameElement &&
        !resultInput
    ) {
        return;
    }


    const params =
        new URLSearchParams(
            window.location.search
        );


    // URL is the source of truth
    const medicine =
        params.get("medicine") || "";


    if (!medicine) {
        return;
    }


    localStorage.setItem(
        "lastMedicine",
        medicine
    );


    if (nameElement) {

        nameElement.textContent =
            medicine;

    }


    if (aiNameElement) {

        aiNameElement.textContent =
            medicine;

    }


    if (resultInput) {

        resultInput.value =
            medicine;

    }


    if (
        typeof searchMedicine ===
        "function"
    ) {

        loadLiveResults(
            medicine
        );

    }

}


// ============================================================================
// Backend API
// ============================================================================

async function loadLiveResults(
    medicine
) {

    const status =
        document.getElementById(
            "data-status"
        );

    const list =
        document.getElementById(
            "pharmacy-list"
        );


    try {

        if (status) {

            status.textContent =
                "Getting your location...";

        }


        if (list) {

            list.innerHTML = `
                <div class="results-loading">
                    Getting nearby pharmacies...
                </div>
            `;

        }


        // Get user's current location.
        const position =
            await getCurrentLocation();


        const lat =
            position.coords.latitude;

        const lon =
            position.coords.longitude;


        console.log(
            "User location:",
            lat,
            lon
        );


        if (status) {

            status.textContent =
                "Finding nearby pharmacies...";

        }


        // Fetch nearby medicine/pharmacy data.
        const data =
            await getNearbyMedicineAvailability(
                medicine,
                lat,
                lon,
                3000
            );


        console.log(
            "MediScan nearby API response:",
            data
        );


        // Get the result array.
        const results =
            Array.isArray(data?.stores)
                ? data.stores
                : [];


        // Render nearby pharmacy markers on the map.
        renderMapMarkers(results);


        // Render results using existing UI.
        renderDynamicResults(
            results
        );


        // Update AI summary.
        updateAiSummary(
            results
        );


        if (status) {

            status.textContent =
                "✓ Live nearby data";

        }


        return data;


    } catch (error) {

        console.error(
            "MediScan API Error:",
            error
        );


        if (status) {

            status.textContent =
                "Unable to load nearby data";

        }


        if (list) {

            list.innerHTML = `
                <div class="results-loading">

                    <strong>
                        Unable to load nearby pharmacies.
                    </strong>

                    <br><br>

                    ${escapeHtml(
                        error.message
                    )}

                    <br><br>

                    Please allow location access
                    and make sure the MediScan
                    backend is running.

                </div>
            `;

        }


        updateAiSummary([]);


        return null;

    }

}


// ============================================================================
// Map Markers
// ============================================================================

function renderMapMarkers(stores) {

    if (!Array.isArray(stores)) {
        return;
    }


    stores.forEach(
        (store) => {

            const latitude =
                Number(
                    store.latitude
                );


            const longitude =
                Number(
                    store.longitude
                );


            const name =
                String(
                    store.name || "Pharmacy"
                ).trim();


            if (
                !Number.isFinite(latitude) ||
                !Number.isFinite(longitude)
            ) {

                return;

            }


            if (
                typeof addMarker ===
                "function"
            ) {

                addMarker(
                    latitude,
                    longitude,
                    name
                );

            }

        }
    );

}


// ============================================================================
// Get Current Location
// ============================================================================

function getCurrentLocation() {

    return new Promise(
        (
            resolve,
            reject
        ) => {

            if (!navigator.geolocation) {

                reject(
                    new Error(
                        "Geolocation is not supported by this browser."
                    )
                );

                return;

            }


            navigator.geolocation.getCurrentPosition(

                resolve,

                (error) => {

                    let message =
                        "Unable to get your location.";


                    if (
                        error.code === 1
                    ) {

                        message =
                            "Location permission was denied. Please allow location access.";

                    }


                    else if (
                        error.code === 2
                    ) {

                        message =
                            "Your location could not be determined.";

                    }


                    else if (
                        error.code === 3
                    ) {

                        message =
                            "Location request timed out. Please try again.";

                    }


                    reject(
                        new Error(
                            message
                        )
                    );

                },

                {
                    enableHighAccuracy: true,
                    timeout: 10000,
                    maximumAge: 0
                }

            );

        }
    );

}


// ============================================================================
// Normalize Backend Offers
// ============================================================================

function normalizeOffers(
    medicines
) {

    if (
        !Array.isArray(
            medicines
        )
    ) {
        return [];
    }


    const offers = [];


    medicines.forEach(
        (medicine) => {

            // ------------------------------------------------------------
            // Preferred backend structure:
            //
            // medicine.offers = [
            //     {
            //         store: "...",
            //         price: 100,
            //         mrp: 120,
            //         url: "..."
            //     }
            // ]
            // ------------------------------------------------------------

            if (
                Array.isArray(
                    medicine.offers
                )
            ) {

                medicine.offers.forEach(
                    (offer) => {

                        offers.push({

                            ...offer,

                            medicine_name:
                                offer.medicine_name ||
                                medicine.medicine_name ||
                                medicine.name ||
                                "Medicine"

                        });

                    }
                );

                return;

            }


            // ------------------------------------------------------------
            // Current backend structure:
            // one medicine object = one offer
            // ------------------------------------------------------------

            offers.push(
                medicine
            );

        }
    );


    return offers;

}


// ============================================================================
// Dynamic Results Renderer
// ============================================================================

function renderDynamicResults(
    medicines
) {

    const list =
        document.getElementById(
            "pharmacy-list"
        );

    const count =
        document.getElementById(
            "result-count"
        );


    if (!list) {
        return;
    }


    list.innerHTML =
        "";


    const offers =
        normalizeOffers(
            medicines
        );


    if (!offers.length) {

        list.innerHTML = `
            <div class="results-loading">

                No matching medicine
                was found.

            </div>
        `;


        if (count) {

            count.textContent =
                "0 stores compared";

        }


        return;

    }


    const records =
        offers
            .map(
                (medicine) => {

                    const price =
                        getNumericPrice(
                            medicine.price ??
                            medicine.selling_price ??
                            medicine.sale_price
                        );


                    const mrp =
                        getNumericPrice(
                            medicine.mrp ??
                            medicine.maximum_retail_price
                        );


                    const store =
                        getStoreInfo(
                            medicine
                        );


                    const available =
                        Boolean(
                            medicine.available ??
                            medicine.in_stock ??
                            medicine.availability ??
                            price > 0
                        );


                    const discount =
                        getDiscountPercentage(
                            medicine,
                            price,
                            mrp
                        );


                    const url =
                        medicine.input_url ||
                        medicine.product_url ||
                        medicine.url ||
                        medicine.link ||
                        "";


                    const distance =
                        Number(
                            medicine.distance
                        );


                    return {

                        medicine,

                        price,

                        mrp,

                        store,

                        available,

                        discount,

                        distance,

                        url

                    };

                }
            )
            .filter(
                (record) =>
                    record.price > 0
            );


    records.sort(
        (a, b) =>
            a.price - b.price
    );


    if (!records.length) {

        list.innerHTML = `
            <div class="results-loading">

                No valid price was returned
                for this medicine.

            </div>
        `;


        if (count) {

            count.textContent =
                "0 stores compared";

        }


        return;

    }


    records.forEach(
        (record, index) => {

            const medicineName =
                record.medicine.medicine_name ||
                record.medicine.name ||
                "Medicine";


            const saveText =
                record.discount > 0
                    ? `Save ${record.discount}%`
                    : "No discount";


            const availabilityText =
                record.available
                    ? "Available"
                    : "Unavailable";


            const row =
                document.createElement(
                    "article"
                );


            row.className =
                `pharmacy-row${
                    index === 0
                        ? " featured"
                        : ""
                }`;


            row.dataset.store =
                record.store.name;


            row.dataset.price =
                record.price;


            row.dataset.available =
                String(
                    record.available
                );


            row.dataset.savings =
                record.discount;


            row.innerHTML = `

                <div class="store">

                    <span
                        class="store-logo ${record.store.className}">

                        ${escapeHtml(
                            record.store.logo
                        )}

                    </span>


                    <div>

                        <strong>

                            ${escapeHtml(
                                record.store.name
                            )}

                        </strong>


                        <small>

                            ${escapeHtml(
                                medicineName
                            )}

                            ·

                            ${availabilityText}

                            ${
                                Number.isFinite(
                                    record.distance
                                )
                                    ? ` · ${record.distance.toFixed(1)} km away`
                                    : ""
                            }

                        </small>

                    </div>

                </div>


                <span class="save-badge">

                    ${escapeHtml(
                        saveText
                    )}

                </span>


                <div class="price-block">

                    <small>

                        ${
                            index === 0
                                ? "Lowest"
                                : "Price"
                        }

                    </small>


                    <strong>

                        ₹${record.price.toFixed(2)}

                    </strong>

                </div>


                <button
                    class="buy-btn deal-action"
                    type="button"
                    data-store="${escapeHtml(
                        record.store.name
                    )}"
                    data-url="${escapeHtml(
                        record.url
                    )}">

                    View Deal

                    <span>
                        ›
                    </span>

                </button>

            `;


            list.appendChild(
                row
            );

        }
    );


    if (count) {

        count.textContent =
            `${records.length} stores compared`;

    }


    initDealButtons();

    initFilters();

}


// ============================================================================
// Price Helpers
// ============================================================================

function getNumericPrice(
    value
) {

    if (
        value &&
        typeof value ===
            "object"
    ) {

        return getNumericPrice(
            value.value
        );

    }


    if (
        typeof value ===
            "number"
    ) {

        return Number.isFinite(
            value
        )
            ? value
            : 0;

    }


    const numeric =
        Number(
            String(
                value || ""
            )
                .replace(
                    /₹/g,
                    ""
                )
                .replace(
                    /,/g,
                    ""
                )
                .trim()
        );


    return Number.isFinite(
        numeric
    )
        ? numeric
        : 0;

}
// ============================================================================
// Discount
// ============================================================================

function getDiscountPercentage(
    medicine,
    price,
    mrp
) {

    // Use backend-provided discount first.
    const backendDiscount =
        medicine.discount_percentage ??
        medicine.discount_percent;


    if (
        backendDiscount !==
            undefined &&
        backendDiscount !==
            null
    ) {

        return Math.max(
            0,
            Math.round(
                Number(
                    backendDiscount
                ) || 0
            )
        );

    }


    // Otherwise calculate it from MRP and selling price.
    if (
        price <= 0 ||
        mrp <= 0 ||
        mrp <= price
    ) {

        return 0;

    }


    return Math.round(
        (
            (
                mrp - price
            ) /
            mrp
        ) * 100
    );

}


// ============================================================================
// Dynamic Store Information
// ============================================================================

function getStoreInfo(
    medicine
) {

    // Preferred:
    // Backend sends the real store name.

    const storeName =
        medicine.name ||
        medicine.store ||
        medicine.store_name ||
        medicine.pharmacy ||
        medicine.pharmacy_name ||
        medicine.vendor ||
        medicine.source;


    if (storeName) {

        const name =
            String(
                storeName
            ).trim();


        return {

            name,

            logo:
                name
                    .charAt(0)
                    .toUpperCase() ||
                "P",

            className:
                "dynamic-store"

        };

    }


    // Fallback:
    // Get pharmacy name from returned URL.

    const productUrl =
        medicine.input_url ||
        medicine.product_url ||
        medicine.url ||
        medicine.link ||
        "";


    if (productUrl) {

        try {

            const hostname =
                new URL(
                    productUrl
                )
                    .hostname
                    .replace(
                        "www.",
                        ""
                    );


            const domain =
                hostname.split(
                    "."
                )[0];


            const name =
                domain
                    .charAt(0)
                    .toUpperCase() +
                domain.slice(1);


            return {

                name:
                    name ||
                    "Pharmacy",

                logo:
                    name
                        .charAt(0)
                        .toUpperCase() ||
                    "P",

                className:
                    "dynamic-store"

            };


        } catch (error) {

            console.warn(
                "Unable to determine pharmacy from URL:",
                error
            );

        }

    }


    return {

        name:
            "Pharmacy",

        logo:
            "P",

        className:
            "dynamic-store"

    };

}


// ============================================================================
// HTML Safety
// ============================================================================

function escapeHtml(
    value
) {

    return String(
        value || ""
    )
        .replace(
            /&/g,
            "&amp;"
        )
        .replace(
            /</g,
            "&lt;"
        )
        .replace(
            />/g,
            "&gt;"
        )
        .replace(
            /"/g,
            "&quot;"
        )
        .replace(
            /'/g,
            "&#039;"
        );

}


// ============================================================================
// AI Summary
// ============================================================================

function updateAiSummary(
    medicines
) {

    const bestPrice =
        document.getElementById(
            "best-price"
        );

    const bestPharmacy =
        document.getElementById(
            "best-pharmacy"
        );

    const bestSaving =
        document.getElementById(
            "best-saving"
        );

    const bestAvailability =
        document.getElementById(
            "best-availability"
        );


    const records =
        normalizeOffers(
            medicines
        )
            .map(
                (medicine) => {

                    const price =
                        getNumericPrice(
                            medicine.price ??
                            medicine.selling_price ??
                            medicine.sale_price
                        );


                    const store =
                        getStoreInfo(
                            medicine
                        );


                    const available =
                        Boolean(
                            medicine.available ??
                            medicine.in_stock ??
                            medicine.availability ??
                            price > 0
                        );


                    return {

                        medicine,

                        price,

                        store,

                        available

                    };

                }
            )
            .filter(
                (record) =>
                    record.price > 0
            )
            .sort(
                (a, b) =>
                    a.price - b.price
            );


    if (!records.length) {

        if (bestPrice) {

            bestPrice.textContent =
                "₹0.00";

        }


        if (bestPharmacy) {

            bestPharmacy.textContent =
                "No result";

        }


        if (bestSaving) {

            bestSaving.textContent =
                "₹0.00";

        }


        if (bestAvailability) {

            bestAvailability.textContent =
                "0 / 0";

        }


        updateAiText(

            "No matching medicine was found.",

            "No price comparison is available yet.",

            "0 stores currently list this medicine."

        );


        return;

    }


    const best =
        records[0];


    const highest =
        Math.max(
            ...records.map(
                (record) =>
                    record.price
            )
        );


    const saving =
        Math.max(
            highest -
            best.price,
            0
        );


    const availableCount =
        records.filter(
            (record) =>
                record.available
        ).length;


    if (bestPrice) {

        bestPrice.textContent =
            `₹${best.price.toFixed(2)}`;

    }


    if (bestPharmacy) {

        bestPharmacy.textContent =
            best.store.name;

    }


    if (bestSaving) {

        bestSaving.textContent =
            `₹${saving.toFixed(2)}`;

    }


    if (bestAvailability) {

        bestAvailability.textContent =
            `${availableCount} / ${records.length}`;

    }


    // Update View Best Deal button.

    const bestDealButton =
        document.querySelector(
            ".best-summary .deal-action"
        );


    if (bestDealButton) {

        bestDealButton.dataset.store =
            best.store.name;


        bestDealButton.dataset.url =
            best.medicine.input_url ||
            best.medicine.product_url ||
            best.medicine.url ||
            best.medicine.link ||
            "";

    }


    const params =
        new URLSearchParams(
            window.location.search
        );


    const medicineName =
        params.get(
            "medicine"
        ) ||
        "this medicine";


    updateAiText(

        `${best.store.name} currently offers the lowest listed price for ${medicineName}.`,

        `You could save up to ₹${saving.toFixed(2)} compared with the highest listed price.`,

        `${availableCount} of ${records.length} stores currently list this medicine as available.`

    );

}


function updateAiText(
    summaryText,
    savingText,
    availabilityText
) {

    const summary =
        document.getElementById(
            "ai-summary-text"
        );

    const saving =
        document.getElementById(
            "ai-saving-text"
        );

    const availability =
        document.getElementById(
            "ai-availability-text"
        );


    if (summary) {

        summary.textContent =
            summaryText;

    }


    if (saving) {

        saving.textContent =
            savingText;

    }


    if (availability) {

        availability.textContent =
            availabilityText;

    }

}


// ============================================================================
// Filters
// ============================================================================

function initFilters() {

    const buttons =
        document.querySelectorAll(
            ".filter-btn"
        );

    const rows =
        document.querySelectorAll(
            ".pharmacy-row"
        );


    if (
        !buttons.length ||
        !rows.length
    ) {

        return;

    }


    buttons.forEach(
        (button) => {

            if (
                button.dataset.bound ===
                "true"
            ) {

                return;

            }


            button.dataset.bound =
                "true";


            button.addEventListener(
                "click",
                () => {

                    buttons.forEach(
                        (item) => {

                            item.classList.remove(
                                "active"
                            );

                        }
                    );


                    button.classList.add(
                        "active"
                    );


                    const filter =
                        button.dataset.filter;


                    const prices =
                        Array.from(
                            rows
                        )
                            .map(
                                (row) =>
                                    Number(
                                        row.dataset.price ||
                                        0
                                    )
                            )
                            .filter(
                                (price) =>
                                    price > 0
                            );


                    const lowestPrice =
                        prices.length
                            ? Math.min(
                                ...prices
                            )
                            : 0;


                    const highestSavings =
                        Math.max(
                            ...Array.from(
                                rows
                            ).map(
                                (row) =>
                                    Number(
                                        row.dataset.savings ||
                                        0
                                    )
                            )
                        );


                    rows.forEach(
                        (row) => {

                            const available =
                                row.dataset.available ===
                                "true";


                            const price =
                                Number(
                                    row.dataset.price ||
                                    0
                                );


                            const savings =
                                Number(
                                    row.dataset.savings ||
                                    0
                                );


                            let visible =
                                true;


                            if (
                                filter ===
                                "available"
                            ) {

                                visible =
                                    available;

                            }


                            else if (
                                filter ===
                                "lowest"
                            ) {

                                visible =
                                    price ===
                                    lowestPrice;

                            }


                            else if (
                                filter ===
                                "savings"
                            ) {

                                visible =
                                    savings ===
                                    highestSavings;

                            }


                            row.style.display =
                                visible
                                    ? "grid"
                                    : "none";

                        }
                    );

                }
            );

        }
    );

}
// ============================================================================
// Pharmacy Deal Buttons
// ============================================================================

function initDealButtons() {

    const dealButtons =
        document.querySelectorAll(
            ".deal-action"
        );


    dealButtons.forEach(
        (button) => {

            if (
                button.dataset.bound ===
                "true"
            ) {

                return;

            }


            button.dataset.bound =
                "true";


            button.addEventListener(
                "click",
                () => {

                    const store =
                        button.getAttribute(
                            "data-store"
                        ) ||
                        "Pharmacy";


                    const url =
                        button.getAttribute(
                            "data-url"
                        );


                    if (!url) {

                        console.error(
                            "Missing data-url for " +
                            store
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

                }
            );

        }
    );


    // Full Analysis Button

    const analysisButton =
        document.getElementById(
            "analysis-btn"
        );


    if (
        analysisButton &&
        analysisButton.dataset.bound !==
        "true"
    ) {

        analysisButton.dataset.bound =
            "true";


        analysisButton.addEventListener(
            "click",
            () => {

                alert(
                    "The full AI analysis can be connected to the backend later."
                );

            }
        );

    }

}


// ============================================================================
// Subscribe Form
// ============================================================================

function initSubscriptions() {

    document
        .querySelectorAll(
            ".subscribe"
        )
        .forEach(
            (form) => {

                form.addEventListener(
                    "submit",
                    (event) => {

                        event.preventDefault();


                        const input =
                            form.querySelector(
                                "input[type='email']"
                            );


                        if (
                            !input ||
                            !input.value.trim()
                        ) {

                            return;

                        }


                        alert(
                            "Thanks for subscribing!"
                        );


                        input.value =
                            "";

                    }
                );

            }
        );

}
