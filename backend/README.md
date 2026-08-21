<img width="960" height="437" alt="image" src="https://github.com/user-attachments/assets/5a2cce4d-551d-4aee-9d65-bcedaf148a8a" />## 🧩 Day 1 — Medicine Data Analyzer

### 🎯 Objective
Built the first Python program to analyze and validate medicine data received from Bright Data.

### ✅ Work Completed

- Created a Python-based **Medicine Data Analyzer**.
- Processed medicine information including:
  - 💊 Medicine Name
  - 💰 Price
  - 🏷️ MRP
  - 🏭 Manufacturer
  - 💉 Dosage
  - 🧪 Salt
  - 📅 Availability
  - 🩺 Uses
- Implemented extraction and display of important medicine details.
- Implemented **discount percentage calculation** using Price and MRP.
- Added **medicine data completeness validation**.
- Checked whether the following important fields are available:
  - Medicine Name
  - Price
  - MRP
  - Manufacturer
  - Availability
- Added automatic data status:
  - `COMPLETE` → All required information is available.
  - `INCOMPLETE` → One or more required fields are missing.
- Added identification of the **specific missing fields**.

#### 🧾 Example

> **Medicine:** P-500 Tablet  
> **Price:** ₹11.43  
> **MRP:** ₹14.65  
> **Manufacturer:** APEX LABORATORIES PRIVATE LIMITED  
> **Availability:** April 2029  
> **Uses:** To treat fever and pain

#### 🔍 Data Validation

- ✅ If all important information exists → `Data Status: COMPLETE`
- ⚠️ If any important information is missing → `Data Status: INCOMPLETE`
- ❌ Missing fields are displayed, e.g. `Missing: price`

---

### 🏆 **Status: ✅ Day 1 Completed**


# 💊 Medicine Aggregator & Price Tracker (Backend API)

This is a pure REST API engine that manages commercial medicine databases, monitors historic price fluctuations, tracks price trends, and automatically calculates generic substitutions using the government **Jan Aushadhi Scheme** dataset.

## 🚀 Server Initialization
- **Base URL:** `http://127.0.0.1:5000`
- **Environment Stack:** Python, Flask, Bright Data Web Scraper IDE Client

---

## 📡 API Endpoints Documentation

### 1. Backend Status Health Check
Checks if the backend microservice is online.
- **Route:** `GET /`
- **Frontend Usage:** Use this to verify connection status on application boot.

### 2. Live Global Search & Generic Substitution Matcher
Scans local indexes for a medicine name, attaches historic price trends, and automatically triggers high-value financial savings alerts if an affordable government generic alternative exists.
- **Route:** `GET /api/search?q={medicine_name}`
- **Example Call:** `GET http://127.0.0`
- **Key Payload Fields to Display on UI:**
  - `mrp`: The high-cost commercial price.
  - `savings_alert.has_generic_alternative`: Boolean flag (`true`/`false`).
  - `savings_alert.alert_banner_trigger`: If `true`, display a massive high-contrast **"Save Money Alert"** banner component on the UI.
  - `savings_alert.generic_brand_name`: The name of the cheap government generic medicine.
  - `savings_alert.money_saved_rupees`: Exact amount of cash saved.
  - `savings_alert.savings_percentage`: Percentage saved (e.g., `80.8%` cheaper).
  - `price_history_log`: Array of timestamped price entries to plot line-graphs or tracking charts.

### 3. Complete Bulk Inventory Directory
Returns every cached commercial medicine row stored locally.
- **Route:** `GET /api/medicines`

### 4. Direct Medicine Single Record
Fetches details for one single item using exact string matching rules.
- **Route:** `GET /api/medicines/{exact_medicine_name}`

### 5. On-Demand Live Web Scraper Sync (Bright Data System)
Invokes your cloud web scraping cluster using your account credits to crawl a live pharmacy search index, refresh the local data inventory cache, log fresh point entries inside the price tracker history files, and compute new generic matches.
- **Route:** `POST /api/scrape-and-sync`
- **Headers Required:** `Content-Type: application/json`
- **JSON Body Payload Structure:**
  ```json
  {
    "url": "https://www.apollopharmacy.in/search-medicines/Fixderma"
  }
  ```
- **Frontend Usage:** Attach this route to a **"Run Live Price Sync"** action button or background cron scheduler inside the admin panels.
