import logging
from google.generativeai import GenerativeModel
from ..config import settings

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = GenerativeModel(settings.GEMINI_MODEL)
        # Set API key in environment or client config
        # (depending on google-generativeai setup)

    def generate_sql(self, prompt: str) -> str:
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.3,
                    "top_p": 0.8,
                    "max_output_tokens": 500
                }
            )
            return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini API generation error: {e}")
            raise
