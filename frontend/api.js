// ============================================================================
// MediScan AI - API helper
// ============================================================================

const API_URL =
    "http://10.123.62.1:5000/api";


// ============================================================================
// Search Medicine
// ============================================================================

async function searchMedicine(medicine) {

    const value =
        String(medicine || "").trim();

    if (!value) {

        throw new Error(
            "Medicine name is required."
        );

    }

    const url =
        `${API_URL}/search?q=${encodeURIComponent(value)}`;

    const response =
        await fetch(url);

    if (!response.ok) {

        throw new Error(
            `HTTP Error: ${response.status}`
        );

    }

    return response.json();
}


// ============================================================================
// Nearby Medicine / Pharmacy Availability
// ============================================================================

async function getNearbyMedicineAvailability(
    medicine,
    lat,
    lon,
    radius = 3000
) {

    const value =
        String(medicine || "").trim();

    if (!value) {

        throw new Error(
            "Medicine name is required."
        );

    }

    if (
        !Number.isFinite(Number(lat)) ||
        !Number.isFinite(Number(lon))
    ) {

        throw new Error(
            "Valid latitude and longitude are required."
        );

    }

    const url =
        `${API_URL}/medicine-availability-nearby` +
        `?medicine=${encodeURIComponent(value)}` +
        `&lat=${encodeURIComponent(lat)}` +
        `&lon=${encodeURIComponent(lon)}` +
        `&radius=${encodeURIComponent(radius)}`;

    const response =
        await fetch(url);

    if (!response.ok) {

        throw new Error(
            `HTTP Error: ${response.status}`
        );

    }

    return response.json();
}


// ============================================================================
// Get All Medicines
// ============================================================================

async function getMedicines() {

    const url =
        `${API_URL}/medicines`;

    const response =
        await fetch(url);

    if (!response.ok) {

        throw new Error(
            `HTTP Error: ${response.status}`
        );

    }

    return response.json();
}


// ============================================================================
// Get Specific Medicine
// ============================================================================

async function getMedicine(medicine) {

    const value =
        String(medicine || "").trim();

    if (!value) {

        throw new Error(
            "Medicine name is required."
        );

    }

    const url =
        `${API_URL}/medicines/${encodeURIComponent(value)}`;

    const response =
        await fetch(url);

    if (!response.ok) {

        throw new Error(
            `HTTP Error: ${response.status}`
        );

    }

    return response.json();
}