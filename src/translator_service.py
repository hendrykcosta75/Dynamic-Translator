import os
import logging
from deep_translator import GoogleTranslator
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

class TranslatorService:
    def __init__(self, target_lang='pt'):
        self.target_lang = target_lang
        self.logger = logging.getLogger(__name__)
        self.refresh_config()

    def refresh_config(self):
        """Reloads configuration (API Key, Provider) from env or internal state."""
        load_dotenv(override=True) # Reload env vars if changed file
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.provider = os.getenv("TRANSLATOR_PROVIDER", "openai") # default to openai if key exists
        self.model = os.getenv("OPENAI_MODEL", "gpt-5.2-chat-latest")
        
        self.openai_client = None
        if self.api_key and not self.api_key.startswith("your-api-key"):
            try:
                self.openai_client = OpenAI(api_key=self.api_key)
            except Exception as e:
                self.logger.error(f"Failed to initialize OpenAI client: {e}")

        # Always have Google as fallback/option
        self.google_translator = GoogleTranslator(source='auto', target=self.target_lang)

    def translate_stream(self, text, provider=None, model=None):
        """
        Yields chunks of translated text.
        """
        if not text or not text.strip():
            return

        current_provider = provider if provider else self.provider
        current_model = model if model else self.model

        # OpenAI Stream
        if current_provider == "openai" and self.openai_client:
            try:
                stream = self.openai_client.chat.completions.create(
                    model=current_model,
                    messages=[
                        {"role": "system", "content": f"You are a translator. Translate the following text to Portuguese (Brazil). Output ONLY the translation."},
                        {"role": "user", "content": text}
                    ],
                    max_completion_tokens=1000,
                    stream=True
                )
                for chunk in stream:
                    if chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                return
            except Exception as e:
                self.logger.error(f"OpenAI stream failed: {e}. Falling back to Google.")
                yield f"[Error: {e}. Fallback to Google...]\n"

        # Google (Simulated Stream)
        try:
            result = self.google_translator.translate(text)
            yield result
        except Exception as e:
            self.logger.error(f"Google translation error: {e}")
            yield f"[Error: {e}]"

    def translate(self, text):
        """Legacy method for non-streaming usage."""
        full_text = ""
        for chunk in self.translate_stream(text):
            full_text += chunk
        return full_text
