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
