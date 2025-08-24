import argparse, json
from typing import Dict, Iterable
from datetime import datetime
from src.shared.gcp_clients import GCSClient
from tqdm import tqdm

def iter_jsonl_gcs(gcs: GCSClient, uri: str, limit: int | None = None):
    with gcs.open(uri, "r") as f:
        for i, line in enumerate(f):
            if limit and i >= limit:
                break
            yield json.loads(line)

def write_jsonl_gcs(gcs: GCSClient, uri: str, rows: Iterable[Dict]):
    with gcs.open(uri, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def clean_record(rec: Dict):
    """Clean a single arXiv record. Return None if invalid."""
    abstract = (rec.get("abstract") or "").strip()
    if not abstract:
        return None

    return {
        "id": rec.get("id"),
        "title": (rec.get("title") or "").strip(),
        "abstract": " ".join(abstract.split()),  # normalize whitespace
        "categories": rec.get("categories", ""),
        "update_date": rec.get("update_date", ""),
    }

def run(input_uri: str, output_uri: str, limit: int | None = None):
    gcs = GCSClient()
    latest_by_id: Dict[str, Dict] = {}

    for rec in tqdm(iter_jsonl_gcs(gcs, input_uri, limit=limit), desc="cleaning"):
        clean = clean_record(rec)
        if not clean:
            continue

        # Keep only the latest version per paper (by update_date)
        try:
            current_date = datetime.strptime(clean["update_date"], "%Y-%m-%d")
        except Exception:
            current_date = datetime.min

        if clean["id"] not in latest_by_id:
            latest_by_id[clean["id"]] = clean
        else:
            old_date = datetime.strptime(latest_by_id[clean["id"]]["update_date"], "%Y-%m-%d")
            if current_date > old_date:
                latest_by_id[clean["id"]] = clean

    print(f"Keeping {len(latest_by_id)} cleaned records.")
    write_jsonl_gcs(gcs, output_uri, latest_by_id.values())
    print(f"Wrote cleaned dataset to {output_uri}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="gs://.../raw/arxiv.jsonl")
    ap.add_argument("--output", required=True, help="gs://.../clean/arxiv_clean.jsonl")
    ap.add_argument("--limit", type=int, default=None, help="limit records for quick tests")
    args = ap.parse_args()
    run(args.input, args.output, limit=args.limit)
