import logging
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self, api_key):
        self.client = genai.Client()
        self.model_name = "gemini-2.5-flash"


    def generate_sql(self, full_prompt: str) -> str:
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    top_p=0.8,
                    max_output_tokens=500
    )
)

            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini API generation error: {e}")
            raise
