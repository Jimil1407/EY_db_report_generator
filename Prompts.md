DIALYSIS UNIQUE PATIENTS REPORT:

Show me a detailed report for dialysis cases (M6 disease, M6.5 surgery) in phase 7, excluding AP state, approved between April 1, 2024 and March 31, 2025. Include patient ration card, case ID, gender, hospital details with district, surgery details, patient district, all case dates (discharge, surgery, death, approval), preauth amount (prioritize CMO amount, then CEO if not zero, else Trust amount), number of biometric cycles per case, financial year (based on 3 months before approval date formatted as YYYY-YYYY+1), and month name and number from approval date.

AHS_CLAIM_PAID REPORT:

Show me a summary of paid claims by hospital and disease for FY 2024-2025. Include hospital ID, name, type, government hospital type, count of paid cases, sum of total claim amounts, disease main ID and name, and financial year (calculated from 3 months before transaction date as YYYY-YYYY+1). Only include cases with payment sent date and transaction date not null, where transaction date is between April 1, 2024 and March 31, 2025. Group by hospital type, government hospital type, hospital ID, hospital name, disease main ID, disease main name, and financial year.

Generate a report for dialysis cases (disease main code M6, surgery code M6.5) in phase 7, excluding Andhra Pradesh state, for the financial year 2024-2025 (from April 1, 2024 to March 31, 2025). 

Include the following fields:
- Patient ration card number
- Case ID
- Patient gender
- Hospital ID and hospital name
- Hospital district name
- Surgery code and surgery description
- Patient district name
- Case discharge date (CS_DIS_DT)
- Case surgery date (CS_SURG_DT)
- Case death date (CS_DEATH_DT)
- Case approval/rejection date (CS_APPRV_REJ_DT)
- Preauth amount calculated as: if CMO approved amount exists, use that; otherwise if CEO approved amount exists and is not zero, use CEO approved amount; otherwise use Trust approved amount
- Number of cycles (count of biometric records for each case)
- Financial year calculated as: year from 3 months before approval date, then format as "YYYY-YYYY+1"
- Month name from approval date
- Month number from approval date

Filter conditions:
- Disease main code must be 'M6'
- Surgery code must be 'M6.5'
- Phase ID must be '7'
- Surgery state flag must not be 'AP' (Andhra Pradesh)
- Approval/rejection date must be between April 1, 2024 00:00:00 and March 31, 2025 23:59:59

