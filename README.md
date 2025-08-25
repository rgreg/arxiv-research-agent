# arxiv-research-agent

This is a prototype system built on Google Cloud to explore retrieval-augmented generation (RAG) with arXiv abstracts.  
The flow is: dataset → clean → embeddings → BigQuery → API → Gemini.

## Setup

1. Clone the repo
   ```bash
   git clone https://github.com/rgreg/arxiv-research-agent.git
   cd arxiv-research-agent
   ```

2. Create and activate a virtual environment
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. Set environment variables
   ```bash
   export GCP_PROJECT="your-project-id"
   export GCP_REGION="us-central1"
   export BUCKET="your-bucket-name"
   export BQ_TABLE="$GCP_PROJECT.arxiv_demo.chunks"
   export GEMINI_MODEL="gemini-2.5-flash-lite"
   ```

## Dataset

- Source: [arXiv Kaggle dataset](https://www.kaggle.com/datasets/Cornell-University/arxiv)
- Upload the raw file to a GCS bucket manually.

## Data pipeline

1. Clean the dataset:
   ```bash
   python -m src.data_pipeline.cleaner \
     --input gs://$BUCKET/raw/arxiv.jsonl \
     --output gs://$BUCKET/clean/arxiv_clean.jsonl
   ```

2. Generate embeddings:
   ```bash
   python -m src.data_pipeline.embed_generator \
     --project $GCP_PROJECT \
     --location $GCP_REGION \
     --embed_model text-embedding-004 \
     --input gs://$BUCKET/clean/arxiv_clean.jsonl \
     --embeddings gs://$BUCKET/embeddings/arxiv_embeddings.jsonl \
     --store gs://$BUCKET/store/arxiv_store.jsonl \
     --limit 100
   ```

3. Load to BigQuery:
   ```bash
   bq load --source_format=NEWLINE_DELIMITED_JSON $BQ_TABLE \
     gs://$BUCKET/embeddings/arxiv_embeddings.jsonl
   ```

## Run API locally

```bash
uvicorn src.agent_api.main:app --reload --port 8000
```

Test:
```bash
curl -s http://127.0.0.1:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"What are transformer models?", "k":3}'
```

## Deploy to Cloud Run

```bash
./deploy_cloud_run.sh
```
