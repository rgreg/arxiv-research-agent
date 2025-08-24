# --- add these near the top if missing ---
from typing import List, Dict
from google.cloud import bigquery
import asyncio
from vertexai import init as vertex_init
from vertexai.generative_models import GenerativeModel, GenerationConfig

# Local CPU embeddings using sentence-transformers
class LocalEmbeddings:
    """
    sentence-transformers local encoder (intfloat/e5-small-v2, 384-dim).
    Use .embed_passages() for chunks and .embed_queries() for user queries.
    """
    def __init__(self, model_name: str = "intfloat/e5-small-v2"):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)

    def _encode(self, texts):
        # normalize=True -> unit vectors, so dot product ≈ cosine
        return self.model.encode(texts, normalize_embeddings=True).tolist()

    def embed_passages(self, texts):
        return self._encode([f"passage: {t or ''}" for t in texts])

    def embed_queries(self, texts):
        return self._encode([f"query: {t or ''}" for t in texts])

    # kept for backward-compat; defaults to passage behavior
    def embed_texts_sync(self, texts):
        return self.embed_passages(texts)


# BigQuery “manual” vector search (no special vector funcs required)
class BigQueryVectorSearch:
    def __init__(self, project: str, table: str):
        """
        table: fully-qualified table, e.g., "my-proj.arxiv_demo.chunks"
        """
        self.project = project
        self.table = table
        self.client = bigquery.Client(project=project)

    def search(self, query_vec, k: int = 5) -> List[Dict]:
        # Build the BigQuery array literal for the query vector
        vec_lit = ",".join(str(float(x)) for x in query_vec)
        sql = f"""
        DECLARE q ARRAY<FLOAT64>;
        SET q = [{vec_lit}];

        SELECT
          id,
          title,
          chunk_text,
          (
            SELECT SUM(e * qe)
            FROM UNNEST(embedding) AS e WITH OFFSET pos
            JOIN UNNEST(q)        AS qe WITH OFFSET pos2
            ON pos = pos2
          ) AS dot
        FROM `{self.table}`
        ORDER BY dot DESC
        LIMIT {k};
        """
        rows = self.client.query(sql).result()
        return [dict(r) for r in rows]
    

# --- Vertex AI Gemini minimal async wrapper ---
class VertexLLM:
    """
    Thin async wrapper around Vertex AI Gemini models.
    Uses generate_content under the hood and returns response.text.
    """
    def __init__(self, project: str, location: str, model: str = "gemini-1.5-flash"):
        vertex_init(project=project, location=location)
        self._model_name = model
        self._model = GenerativeModel(model)

    async def generate(
        self,
        prompt: str,
        max_output_tokens: int = 512,
        temperature: float = 0.2,
        top_p: float = 0.95,
    ) -> str:
        def _gen_sync():
            return self._model.generate_content(
                [prompt],
                generation_config=GenerationConfig(
                    max_output_tokens=max_output_tokens,
                    temperature=temperature,
                    top_p=top_p,
                ),
            )
        loop = asyncio.get_running_loop()
        resp = await loop.run_in_executor(None, _gen_sync)
        # vertexai responses expose .text with the concatenated candidate
        return getattr(resp, "text", str(resp))
