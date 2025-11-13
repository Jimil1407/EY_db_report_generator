# Test Prompts for CSV Download Functionality

These prompts are designed to test the CSV download feature by generating queries that return multiple columns and more than 5 rows.

## Prompts for Multiple Columns + Many Rows

### 1. Patient Demographics (Basic Info)
**Prompt:** "Show me all patient details including name, age, gender, address, and contact information for patients older than 18"

**Expected:** Returns PATIENT_NAME, MIDDLE_NAME, LAST_NAME, AGE, GENDER, ADDRESS, ADDRESS2, MOBILE, EMAIL, STATE, DISTRICT_CODE, PIN_CODE

---

### 2. Complete Patient Profile
**Prompt:** "Get me a complete list of all patient information including personal details, registration details, and card information"

**Expected:** Returns all or most columns (SELECT * or many columns)

---

### 3. Patient Registration Details
**Prompt:** "Show me patient registration information including patient ID, name, registration number, hospital details, and card status for all patients"

**Expected:** Returns PATIENT_ID, PATIENT_NAME, REGISTRATION_NO, REG_CARD_NO, REG_HOSP_NO, REG_HOSP_ID, REG_HOSP_DATE, CARD_STATUS, and related fields

---

### 4. Patient Card Information
**Prompt:** "List all patients with their card issue dates, renewal dates, card status, and related card information"

**Expected:** Returns CARD_ISSUE_DATE, CARD_ISSUE_TYPE, CARD_ISSUE_REASON, CARD_RENEWAL_DATE, CARD_RENEWAL_REASON, CARD_STATUS, CARD_CANCEL_DATE, CARD_REPLACEMENT_DATE, etc.

---

### 5. Patient Demographics with Location
**Prompt:** "Show me patient names, ages, genders, addresses, state, district, pin code, caste, and occupation for all patients"

**Expected:** Returns PATIENT_NAME, MIDDLE_NAME, LAST_NAME, AGE, GENDER, ADDRESS, ADDRESS2, STATE, DISTRICT_CODE, PIN_CODE, CASTE, OCCUPATION

---

### 6. Patient Contact and Personal Info
**Prompt:** "Get me patient ID, full name, date of birth, age, gender, mobile number, email, and marital status for all patients"

**Expected:** Returns PATIENT_ID, PATIENT_NAME, MIDDLE_NAME, LAST_NAME, DOB, AGE, GENDER, MOBILE, EMAIL, MARITAL_STATUS

---

### 7. Patient Registration and Card Details
**Prompt:** "Show all patients with their registration numbers, card numbers, hospital registration details, card issue information, and card status"

**Expected:** Returns REGISTRATION_NO, REG_CARD_NO, REG_HOSP_NO, REG_HOSP_ID, REG_HOSP_DATE, CARD_ISSUE_DATE, CARD_ISSUE_TYPE, CARD_STATUS, and related fields

---

### 8. Patient with All Dates
**Prompt:** "List patients with all their important dates including date of birth, registration date, card issue date, renewal date, and report date"

**Expected:** Returns DOB, REG_HOSP_DATE, CARD_ISSUE_DATE, CARD_RENEWAL_DATE, REPORT_DATE, CARD_CANCEL_DATE, CARD_REPLACEMENT_DATE, SET_UPD_DT

---

### 9. Complete Patient Record
**Prompt:** "Get me complete patient records with all personal information, address details, registration info, and card details"

**Expected:** Returns most/all columns from the table

---

### 10. Patient Demographics Extended
**Prompt:** "Show me patient information including ID, name, age, gender, address, state, district, pin code, caste, occupation, marital status, mobile, email, and registration details"

**Expected:** Returns 15+ columns covering demographics and registration

---

## Prompts for Testing Row Count (>5 rows)

### 11. All Patients Above Age
**Prompt:** "Show me all patients who are older than 25 years with their basic information"

**Expected:** Should return many rows if there are patients > 25

---

### 12. Patients by Gender
**Prompt:** "List all female patients with their name, age, and contact details"

**Expected:** Should return many rows if there are female patients

---

### 13. Patients with Cards Issued
**Prompt:** "Show me all patients who have a card issue date, including their patient ID, name, and card details"

**Expected:** Should return many rows if cards have been issued

---

### 14. Recent Registrations
**Prompt:** "Get me all patients registered in the last year with their registration and personal details"

**Expected:** Should return many rows if there are recent registrations

---

### 15. Patients by State
**Prompt:** "Show me all patients from a specific state with their complete address and contact information"

**Expected:** Should return many rows depending on state

---

## Prompts for Testing Both (Many Columns + Many Rows)

### 16. Complete Patient List
**Prompt:** "Get me a complete export of all patient data including all available columns"

**Expected:** Returns all columns (SELECT *) and many rows

---

### 17. Patient Demographics Report
**Prompt:** "Generate a comprehensive patient demographics report with all personal information, address, contact details, registration info, and card status"

**Expected:** Returns 20+ columns and many rows

---

### 18. Full Patient Details
**Prompt:** "Show me all patient records with complete information including personal details, address, registration, card information, and all dates"

**Expected:** Returns most/all columns and many rows

---

### 19. Patient Master Data
**Prompt:** "Export all patient master data with every available field"

**Expected:** Returns all columns (SELECT *) and all rows

---

### 20. Comprehensive Patient List
**Prompt:** "List all patients with their ID, full name, age, gender, complete address, mobile, email, registration number, card number, card status, and all important dates"

**Expected:** Returns 15+ columns and many rows

---

## Tips for Testing

1. **Test CSV Download**: Use prompts 16-20 to ensure CSV download works with large datasets
2. **Test Preview**: Use prompts 1-10 to verify the 5-row preview displays correctly
3. **Test Persistence**: After downloading CSV, verify the download button remains available
4. **Test Edge Cases**: 
   - Queries returning exactly 5 rows (should show table, not CSV)
   - Queries returning 6 rows (should show CSV + preview)
   - Queries returning 0 rows (should show appropriate message)

## Expected SQL Patterns

Most of these prompts should generate SQL like:
- `SELECT PATIENT_ID, PATIENT_NAME, AGE, GENDER, ... FROM ASRIT_PATIENT WHERE ...`
- `SELECT * FROM ASRIT_PATIENT WHERE ...`
- `SELECT [multiple columns] FROM ASRIT_PATIENT WHERE ... FETCH FIRST N ROWS ONLY`

