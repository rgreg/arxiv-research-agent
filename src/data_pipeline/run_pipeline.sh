#!/usr/bin/env bash
set -euo pipefail

while [[ $# -gt 0 ]]; do
  case $1 in
    --project) PROJECT="$2"; shift 2;;
    --region) REGION="$2"; shift 2;;
    --bucket) BUCKET="$2"; shift 2;;
    --input) INPUT="$2"; shift 2;;
    --clean) CLEAN="$2"; shift 2;;
    --embeddings) EMBEDDINGS="$2"; shift 2;;
    --store) STORE="$2"; shift 2;;
    *) echo "Unknown arg $1"; exit 1;;
  esac
done

echo "Step 1: Cleaning raw data..."
python -m src.data_pipeline.data_cleaner \
  --input "$INPUT" \
  --output "$CLEAN" \
  --limit 10000   # remove or increase when scaling full dataset

echo "Step 2: Generating embeddings..."
python -m src.data_pipeline.embed_generator \
  --project "$PROJECT" \
  --location "${VERTEX_LOCATION:-us-central1}" \
  --embed_model "${EMBED_MODEL:-text-embedding-004}" \
  --input "$CLEAN" \
  --embeddings "$EMBEDDINGS" \
  --store "$STORE"
