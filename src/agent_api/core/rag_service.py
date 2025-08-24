# src/agent_api/core/rag_service.py
from typing import List, Dict
from textwrap import dedent

from src.agent_api.core.config import settings
from src.shared.gcp_clients import LocalEmbeddings, BigQueryVectorSearch, VertexLLM

class RAGService:
    def __init__(self,
                 project: str | None = None,
                 location: str | None = None,
                 bq_table: str | None = None,
                 embed_model: str = "intfloat/e5-small-v2",
                 gemini_model: str | None = None,
                 max_context_chunks: int | None = None,
                 max_chunk_chars: int | None = None):
        project = project or settings.project
        location = location or settings.location
        bq_table = bq_table or settings.bq_table
        gemini_model = gemini_model or settings.gemini_model
        self.max_context_chunks = max_context_chunks or settings.max_context_chunks
        self.max_chunk_chars = max_chunk_chars or settings.max_chunk_chars

        # Embeddings (local CPU; 384-dim, normalized)
        self.embedder = LocalEmbeddings(embed_model)
        # BigQuery vector search (manual dot product SQL)
        self.searcher = BigQueryVectorSearch(project=project, table=bq_table)
        # Gemini (Vertex AI)
        self.llm = VertexLLM(project=project, location=location, model=gemini_model)

    def _build_prompt(self, question: str, hits: List[Dict]) -> str:
        bullets = []
        for h in hits[: self.max_context_chunks]:
            title = (h.get("title") or "").strip()
            chunk = (h.get("chunk_text") or "").strip()[: self.max_chunk_chars]
            bullets.append(f"- TITLE: {title}\n  EXCERPT: {chunk}")
        context = "\n".join(bullets) if bullets else "None"

        prompt = dedent(f"""
        You are a meticulous research assistant. Use the provided context snippets (which may come from different
        papers) to answer the user's question succinctly, with citations to titles. If the context is insufficient,
        say so briefly and suggest what to search for next.

        Question:
        {question}

        Context snippets:
        {context}

        Instructions:
        - Write a short synthesis (3–6 sentences).
        - Then list 3–5 bullet points of key facts.
        - Cite supporting titles inline like [Title].
        - Avoid guessing; prefer cautious wording if uncertain.
        """).strip()
        return prompt

    async def answer(self, question: str, k: int = 5) -> Dict:
        # 1) Embed question
        # q_vec = self.embedder.embed_texts_sync([question])[0]
        q_vec = self.embedder.embed_queries([question])[0]
        # 2) Search BQ
        hits = self.searcher.search(q_vec, k=k)  # returns [{id,title,chunk_text,dot}, ...]
        # 3) Build prompt for Gemini
        prompt = self._build_prompt(question, hits)
        # 4) Generate
        text = await self.llm.generate(prompt)
        # 5) Return with simple citations (titles)
        citations = [h.get("title") for h in hits if h.get("title")]
        return {"answer": text, "citations": citations, "matches": hits[:k]}
