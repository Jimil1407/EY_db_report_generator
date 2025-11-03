from gemini_client import GeminiClient
from schema_manager import load_schema, format_schema
from prompt_builder import build_gemini_prompt
from dotenv import load_dotenv
import os

load_dotenv()

# Get the API key
g_api_key = os.getenv('GEMINI_API_KEY')

class SQLGenerator:
    def __init__(self, few_shots: list):
        # Load fixed schema once and format for prompt context
        schema_json = load_schema()  # returns JSON dict from file
        #print(type(schema_json))
        self.schema_context = format_schema(schema_json)  # formatted schema string
        self.few_shots = few_shots
        self.gemini_client = GeminiClient(api_key=g_api_key)

    def generate_query(self, user_question: str) -> str:
        # Build full combined prompt using the shared prompt builder
        prompt = build_gemini_prompt(
            user_question=user_question,
            few_shots=self.few_shots,
            schema_context=self.schema_context,
        )

        # Call Gemini API to generate SQL
        sql = self.gemini_client.generate_sql(prompt)

        # For now, just print SQL query
        print(f"Generated SQL for question '{user_question}':\n{sql}\n")

        # Return SQL for further processing
        return sql


if __name__ == "__main__":
    few_shots = [
        {
            "q": "How many claims are pending?",
            "a": "SELECT COUNT(*) FROM claims WHERE status = 'PENDING';",
        },
        {
            "q": "Show approved claims in last month.",
            "a": (
                "SELECT * FROM claims "
                "WHERE status = 'APPROVED' "
                "AND claim_date >= TRUNC(ADD_MONTHS(SYSDATE, -1), 'MM');"
            ),
        },
    ]

    sql_gen = SQLGenerator(few_shots)
    sample_question = "Give me report for pending approvals for last month"
    sql_gen.generate_query(sample_question)
