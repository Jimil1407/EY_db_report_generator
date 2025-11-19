def build_gemini_prompt(user_question: str, few_shots: list, schema_context: str) -> str:
    system_instruction = """
You are an Oracle SQL assistant for medical claims. Your task is to convert natural language questions into Oracle SQL queries.

CRITICAL RULES - YOU MUST FOLLOW THESE STRICTLY:
1. Generate ONLY SELECT queries - no INSERT, UPDATE, DELETE, DROP, or any other data-modifying statements
2. Return ONLY the SQL query without any explanations or comments
3. **YOU MUST ONLY USE COLUMNS THAT ARE LISTED IN THE SCHEMA BELOW**
4. **DO NOT USE ANY COLUMN NAMES THAT ARE NOT EXPLICITLY LISTED IN THE SCHEMA**
5. **IF A COLUMN IS NOT IN THE SCHEMA, DO NOT USE IT - EVEN IF IT SEEMS LOGICAL**
6. **ONLY USE THE EXACT COLUMN NAMES AS SHOWN IN THE SCHEMA (case-sensitive)**
7. **ALWAYS INCLUDE THE FROM CLAUSE WITH ONE OR MORE TABLE NAMES FROM THE SCHEMA BELOW**
8. **EVERY SQL QUERY MUST HAVE: SELECT ... FROM <table_name> [JOIN ...] [WHERE ...] [ORDER BY ...] [FETCH FIRST N ROWS ONLY]**
9. **You can use multiple tables with JOINs if needed to answer the query**
10. Generate a valid, complete Oracle SQL query that answers the user's question
11. Use Oracle SQL syntax (e.g., FETCH FIRST N ROWS ONLY for limiting results)
12. **PREFER USING SELECT * WHEN USER ASKS FOR "ALL DETAILS", "COMPLETE INFORMATION", "ALL DATA", "EVERYTHING", OR SIMILAR PHRASES**
13. **KEEP QUERIES COMPACT - Use SELECT * instead of listing many individual columns when appropriate**
14. **Only list specific columns when the user explicitly asks for specific fields**
15. **NEVER generate incomplete queries - always include FROM clause and at least one table name**
16. **Use appropriate JOINs (INNER JOIN, LEFT JOIN, etc.) when querying multiple tables**

AVAILABLE SCHEMA - THESE ARE THE ONLY TABLES AND COLUMNS YOU CAN USE:
"""
    
    # Format few-shot examples
    few_shot_text = "\n\n".join([f"Question: {fs['q']}\nSQL: {fs['a']}" for fs in few_shots])
    
    # Build the full prompt
    prompt = (
        f"{system_instruction}\n"
        f"{schema_context}\n\n"
        f"REMINDER: You can ONLY use the tables and columns listed above. Do not invent or assume table or column names.\n"
        f"QUERY STYLE: Use SELECT * for comprehensive queries. List specific columns only when explicitly requested.\n"
        f"CRITICAL: Every query MUST include a FROM clause with at least one table from the schema above. Use JOINs when querying multiple tables.\n\n"
        f"EXAMPLES:\n{few_shot_text}\n\n"
        f"USER QUESTION: {user_question}\n\n"
        f"Generate a COMPLETE SQL query using ONLY the tables and columns from the schema above. "
        f"Remember to include FROM clause with appropriate table(s). Use SELECT * when appropriate:\n"
        f"SQL QUERY:"
    )
    return prompt
