# src/data_pipeline/nlp_extractor.py
from google.cloud import language_v2 as language
from google.cloud import bigquery
import json

def analyze(text: str):
    client = language.LanguageServiceClient()
    doc = {"content": text, "type_": language.Document.Type.PLAIN_TEXT}
    ents = client.analyze_entities(document=doc).entities
    sent = client.analyze_sentiment(document=doc).document_sentiment
    return {
        "entities": [
            {"name": e.name, "type": language.Entity.Type(e.type_).name, "salience": e.salience}
            for e in ents
        ],
        "sentiment": {"score": sent.score, "magnitude": sent.magnitude},
    }

def write_bq(project: str, table: str, rows: list[dict]):
    bq = bigquery.Client(project=project)
    bq.insert_rows_json(table, rows)

# Batch over a sample of documents/chunks:
# read chunk_text + id,title from BQ, run analyze(), write to `${project}.arxiv_demo.extractions`
