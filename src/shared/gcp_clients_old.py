import time
from typing import List
from google.api_core.exceptions import ResourceExhausted
import vertexai
from vertexai.language_models import TextEmbeddingModel

class VertexEmbeddings:
    """
    Vertex AI embeddings with gentle rate limiting + retries to avoid quota errors.
    """
    def __init__(
        self,
        project: str,
        location: str,
        model: str = "text-embedding-004",
        batch_sleep_secs: float = 1.5,
        max_retries: int = 6,
    ):
        self.project = project
        self.location = location
        self.model_name = model
        self.batch_sleep_secs = batch_sleep_secs
        self.max_retries = max_retries
        vertexai.init(project=project, location=location)
        self._model = TextEmbeddingModel.from_pretrained(self.model_name)

    async def embed_text(self, text: str) -> List[float]:
        # single item wrapper
        for attempt in range(self.max_retries + 1):
            try:
                res = self._model.get_embeddings([text])
                time.sleep(self.batch_sleep_secs)
                return res[0].values
            except ResourceExhausted as e:
                if attempt >= self.max_retries:
                    raise
                sleep = min(2 ** (attempt + 1), 64)
                print(f"[embed_text] Quota hit; backing off {sleep}s")
                time.sleep(sleep)

    def embed_texts_sync(self, texts: List[str]) -> List[List[float]]:
        """
        Rate-limited, retrying batch embed to reduce 429s.
        """
        for attempt in range(self.max_retries + 1):
            try:
                res = self._model.get_embeddings(texts)
                time.sleep(self.batch_sleep_secs)  # soft throttle per batch
                return [e.values for e in res]
            except ResourceExhausted:
                if attempt >= self.max_retries:
                    raise
                sleep = min(2 ** (attempt + 1), 64)
                print(f"[embed_texts_sync] Quota hit; backing off {sleep}s")
                time.sleep
