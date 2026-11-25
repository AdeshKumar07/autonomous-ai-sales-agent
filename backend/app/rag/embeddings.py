"""ChromaDB embedding function powered by the official Google Gen AI SDK."""

from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from google import genai
from app.core.config import Settings, validate_gemini_config


class GeminiEmbeddingFunction(EmbeddingFunction[Documents]):
    """Generates vector embeddings via Gemini's embedding model without extra local downloads."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = validate_gemini_config(settings)
        self._client = genai.Client(api_key=self._settings.gemini_api_key)
        self._model = self._settings.gemini_embedding_model

    @property
    def model_name(self) -> str:
        return self._model

    def __call__(self, input: Documents) -> Embeddings:
        if not input:
            return []

        response = self._client.models.embed_content(
            model=self._model,
            contents=list(input),
        )
        return [list(item.values) for item in response.embeddings]
