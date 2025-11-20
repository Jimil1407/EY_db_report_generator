"""
Configuration and setup for the application.
"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def load_environment():
    """Load environment variables from .env.local file."""
    env_path = Path(__file__).parent / ".env.local"
    logger.info(f"Looking for .env.local file at: {env_path}")

    if env_path.exists():
        logger.info(f".env.local file found at {env_path}")
        load_dotenv(dotenv_path=env_path)
        if os.getenv("GEMINI_API_KEY"):
            logger.info(f"API key loaded from .env.local: {os.getenv('GEMINI_API_KEY')[:10]}...")
        else:
            logger.error("GEMINI_API_KEY not found in .env.local file")
    else:
        logger.error(f".env.local file not found at {env_path}")


def get_gemini_api_key() -> str:
    """Get Gemini API key from environment."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured in backend/.env.local file or environment")
    return api_key


# Few-shot examples for SQL generation
FEW_SHOT_EXAMPLES = [
    {
        "user_name": "John Doe",
        "user_email": "john.doe@example.com",
        "q": "How many patients are there?",
        "a": "SELECT COUNT(*) FROM ASRIT_PATIENT;",
    },
    {
        "user_name": "Jane Smith",
        "user_email": "jane.smith@example.com",
        "q": "Show me all patient details for patients older than 18",
        "a": "SELECT * FROM ASRIT_PATIENT WHERE AGE > 18;",
    },
    {
        "user_name": "Bob Johnson",
        "user_email": "bob.johnson@example.com",
        "q": "Get patient ID and name for female patients",
        "a": "SELECT PATIENT_ID, FIRST_NAME, MIDDLE_NAME, LAST_NAME FROM ASRIT_PATIENT WHERE GENDER = 'F';",
    },
    {
        "user_name": "Alice Brown",
        "user_email": "alice.brown@example.com",
        "q": "Show me all patient details including name, age, gender, address, and contact information for patients older than 18, top 10 rows",
        "a": "SELECT * FROM ASRIT_PATIENT WHERE AGE > 18 FETCH FIRST 10 ROWS ONLY;",
    },
    {
        "user_name": "Charlie Wilson",
        "user_email": "charlie.wilson@example.com",
        "q": "Get all patient information",
        "a": "SELECT * FROM ASRIT_PATIENT;",
    },
    {
        "user_name": "Report User",
        "user_email": "report@example.com",
        "q": "Show me a detailed report for dialysis cases (M6 disease, M6.5 surgery) in phase 7, excluding AP state, approved between April 1, 2024 and March 31, 2025. Include patient ration card, case ID, gender, hospital details with district, surgery details, patient district, all case dates (discharge, surgery, death, approval), preauth amount (prioritize CMO amount, then CEO if not zero, else Trust amount), number of biometric cycles per case, financial year (based on 3 months before approval date formatted as YYYY-YYYY+1), and month name and number from approval date.",
        "a": """SELECT AP.RATION_CARD_NO,
AC.CASE_ID,
AP.GENDER,
AH.HOSP_ID,
AH.HOSP_NAME,
ADS1.DIST_NAME HOSP_DIST,
ACS.SURGERY_CODE,
AS1.SURGERY_DESC,
ADS2.DIST_NAME PATIENT_DIST,
AC.CS_DIS_DT,
AC.CS_SURG_DT,
AC.CS_DEATH_DT,
AC.CS_APPRV_REJ_DT,
DECODE(ACC.CASE_CMO_APRV_AMT,
NULL,
(DECODE(ACC.CASE_CEO_APRV_AMT,
null,
ACC.CASE_TRUST_APRV_AMT,
0,
ACC.CASE_TRUST_APRV_AMT,
ACC.CASE_CEO_APRV_AMT)),
ACC.CASE_CMO_APRV_AMT) PREAUTH_AMOUNT,
(SELECT COUNT(*)
FROM ASRIT_CASE_PATIENT_BIOMETRIC
WHERE CASE_ID = AC.CASE_ID) NO_OF_CYCLES,
(TO_CHAR(ADD_MONTHS(AC.CS_APPRV_REJ_DT, -3), 'YYYY')) || '-' ||
(TO_CHAR(ADD_MONTHS(AC.CS_APPRV_REJ_DT, -3), 'YYYY') + 1) FY,
TO_CHAR(AC.CS_APPRV_REJ_DT, 'MON') MON,
TO_CHAR(AC.CS_APPRV_REJ_DT, 'MM') MM
FROM ASRIT_CASE AC,
ASRIT_CASE_SURGERY ACS,
ASRIT_PATIENT AP,
ASRIM_HOSPITALS AH,
ASRIM_DIST_SEQ ADS1,
ASRIM_DIST_SEQ ADS2,
ASRIM_SURGERY AS1,
ASRIT_CASE_CLAIM ACC
WHERE AC.CASE_ID = ACS.CASE_ID
AND AC.CASE_PATIENT_NO = AP.PATIENT_ID
AND AC.CASE_HOSP_CODE = AH.HOSP_ID
AND AH.DIST_ID = ADS1.DIST_ID
AND AP.DISTRICT_CODE = ADS2.DIST_ID
AND ACS.SURGERY_CODE = AS1.SURGERY_ID
AND AC.CASE_ID = ACC.CASE_ID
AND AC.CS_DIS_MAIN_CODE = 'M6'
AND ACS.SURGERY_CODE = 'M6.5'
AND AC.PHASE_ID = '7'
AND AS1.STATE_FLAG <> 'AP'
AND AC.CS_APPRV_REJ_DT BETWEEN
    TO_DATE('01/04/2024 00:00:00', 'DD/MM/YYYY HH24:MI:SS') AND
    TO_DATE('31/03/2025 23:59:59', 'DD/MM/YYYY HH24:MI:SS');""",
    },
]

