import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("API key is required for GeminiClient")
        
        # Configure the Gemini API with the provided key
        genai.configure(api_key=api_key)
        self.model_name = "gemini-2.5-flash"
        
        # Create a generative model instance
        self.model = genai.GenerativeModel(self.model_name)

    def generate_sql(self, full_prompt: str) -> str:
        try:
            # Generate content using the correct API
            logger.info(f"Generating SQL with model: {self.model_name}")
            
            generation_config = {
                "temperature": 0.3,
                "top_p": 0.8,
                "max_output_tokens": 8192,  # Increased to allow longer queries without truncation
            }
            
            response = self.model.generate_content(
                full_prompt,
                generation_config=generation_config
            )
            
            # Extract the text from the response
            if hasattr(response, 'text'):
                return response.text.strip()
            else:
                logger.warning(f"Unexpected response format: {type(response)}")
                return str(response).strip()
                
        except Exception as e:
            logger.error(f"Gemini API generation error: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise
