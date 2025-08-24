import argparse, json
from typing import Dict, Iterable, List
from tqdm import tqdm

from src.shared.gcp_clients import (
    GCSClient,
    VertexEmbeddings,
    LocalEmbeddings,
)

def iter_jsonl_gcs(gcs: GCSClient, uri: str, limit: int | None = None) -> Iterable[Dict]:
    with gcs.open(uri, "r") as f:
        for i, line in enumerate(f):
            if limit and i >= limit: break
            yield json.loads(line)

def write_jsonl_gcs(gcs: GCSClient, uri: str, rows: Iterable[Dict]):
    with gcs.open(uri, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def chunk_text(txt: str, max_words: int = 180) -> List[str]:
    words = (txt or "").split()
    return [" ".join(words[i:i+max_words]) for i in range(0, len(words), max_words)]

def run(
    project: str,
    location: str,
    embed_model: str,
    input_uri: str,
    embeddings_uri: str,
    store_uri: str,
    batch_size: int = 16,
    limit: int | None = None,
    batch_sleep_secs: float = 1.5,
    max_retries: int = 6,
    provider: str = "vertex",
    local_model: str = "intfloat/e5-small-v2",
):
    gcs = GCSClient()

    if provider.lower() == "local":
        embedder = LocalEmbeddings(model_name=local_model)
    else:
        embedder = VertexEmbeddings(
            project=project,
            location=location,
            model=embed_model,
            batch_sleep_secs=batch_sleep_secs,
            max_retries=max_retries,
        )

    store_rows, embed_rows = [], []

    for rec in tqdm(iter_jsonl_gcs(gcs, input_uri, limit=limit), desc="processing"):
        doc_id = rec.get("id")
        title = (rec.get("title") or "").strip()
        abstract = (rec.get("abstract") or "").strip()
        if not abstract:
            continue

        chunks = chunk_text(abstract)
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]
            vecs = embedder.embed_texts_sync(batch)
            for j, vec in enumerate(vecs):
                idx = i + j
                vector_id = f"{doc_id}#{idx}"
                embed_rows.append({"id": vector_id, "embedding": vec})
                store_rows.append({
                    "id": vector_id,
                    "doc_id": doc_id,
                    "title": title,
                    "chunk_index": idx,
                    "chunk_text": batch[j],
                })

    write_jsonl_gcs(gcs, embeddings_uri, embed_rows)
    write_jsonl_gcs(gcs, store_uri, store_rows)
    print(f"Wrote embeddings -> {embeddings_uri}")
    print(f"Wrote store -> {store_uri}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--location", default="us-central1")
    ap.add_argument("--embed_model", default="text-embedding-004")
    ap.add_argument("--input", required=True)
    ap.add_argument("--embeddings", required=True)
    ap.add_argument("--store", required=True)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--batch_size", type=int, default=16)
    ap.add_argument("--batch_sleep_secs", type=float, default=1.5)
    ap.add_argument("--max_retries", type=int, default=6)
    ap.add_argument("--provider", choices=["vertex","local"], default="vertex")
    ap.add_argument("--local_model", default="intfloat/e5-small-v2")
    args = ap.parse_args()
    run(
        project=args.project,
        location=args.location,
        embed_model=args.embed_model,
        input_uri=args.input,
        embeddings_uri=args.embeddings,
        store_uri=args.store,
        batch_size=args.batch_size,
        limit=args.limit,
        batch_sleep_secs=args.batch_sleep_secs,
        max_retries=args.max_retries,
        provider=args.provider,
        local_model=args.local_model,
    )
