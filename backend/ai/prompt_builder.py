from schema_manager import load_schema
schema_context = load_schema()

def build_gemini_prompt(user_question: str, few_shots: list, schema_context: str) -> str:
    system_instruction = (
        "You are an Oracle SQL assistant for medical claims. "
        "Generate only SELECT queries. Return only the SQL query, no explanations.\n"
    )
    few_shot_text = "\n".join([f"Q: {fs['q']}\nA: {fs['a']}" for fs in few_shots])
    prompt = (
        f"{system_instruction}"
        f"Schema:\n{schema_context}\n"
        f"Few-Shot Examples:\n{few_shot_text}\n"
        f"User Question:\n{user_question}\n"
    )
    return prompt
