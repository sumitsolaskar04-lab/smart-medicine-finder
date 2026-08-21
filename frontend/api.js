// ============================================================================
// MediScan AI - API helper
// ============================================================================

const API_URL =
    "http://10.231.8.182:5000/api";


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