# --- add these near the top if missing ---
from typing import List, Dict
from google.cloud import bigquery

# Local CPU embeddings using sentence-transformers
class LocalEmbeddings:
    """
    Uses sentence-transformers locally (default: intfloat/e5-small-v2, 384-dim).
    Embeddings are L2-normalized so dot product ≈ cosine similarity.
    """
    def __init__(self, model_name: str = "intfloat/e5-small-v2"):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)
        self.prefix = "passage: "

    def embed_texts_sync(self, texts: List[str]) -> List[List[float]]:
        texts = [self.prefix + (t or "") for t in texts]
        # normalize=True gives unit-length vectors (cosine-ready)
        return self.model.encode(texts, normalize_embeddings=True).tolist()

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
