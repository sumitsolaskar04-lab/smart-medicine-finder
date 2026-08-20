// ============================================================================
// MediScan AI - API helper
// ============================================================================

// Replace this value when Person 1 provides the deployed backend URL.
const API_URL = window.MEDISCAN_API_URL || "";

/**
 * Search for a medicine using the project backend.
 *
 * Expected backend format:
 * GET /search?medicine=<medicine-name>
 */
async function searchMedicine(medicine) {
    const value = String(medicine || "").trim();

    if (!value) {
        throw new Error("Medicine name is required.");
    }

    if (!API_URL) {
        throw new Error("Backend URL is not configured yet.");
    }

    const url = `${API_URL.replace(/\/$/, "")}/search?medicine=${encodeURIComponent(value)}`;
    const response = await fetch(url);

    if (!response.ok) {
        throw new Error(`HTTP Error: ${response.status}`);
    }

    return response.json();
}
