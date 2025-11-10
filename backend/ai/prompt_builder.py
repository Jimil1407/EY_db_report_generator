def build_gemini_prompt(user_question: str, few_shots: list, schema_context: str) -> str:
    system_instruction = """
You are an Oracle SQL assistant for medical claims. Your task is to convert natural language questions into Oracle SQL queries.

IMPORTANT INSTRUCTIONS:
1. Generate ONLY SELECT queries - no INSERT, UPDATE, DELETE, DROP, or any other data-modifying statements
2. Return ONLY the SQL query without any explanations or comments
3. Use only tables and columns provided in the schema
4. Generate a valid Oracle SQL query that answers the user's question

SCHEMA:
"""
    
    # Format few-shot examples
    few_shot_text = "\n\n".join([f"Question: {fs['q']}\nSQL: {fs['a']}" for fs in few_shots])
    
    # Build the full prompt
    prompt = (
        f"{system_instruction}\n"
        f"{schema_context}\n\n"
        f"EXAMPLES:\n{few_shot_text}\n\n"
        f"USER QUESTION: {user_question}\n\n"
        f"SQL QUERY:"
    )
    return prompt
