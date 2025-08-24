import os
from pydantic import BaseModel

class Settings(BaseModel):
    gcp_project: str = os.getenv("GCP_PROJECT", "")
    gcp_region: str = os.getenv("GCP_REGION", "us-central1")
    vertex_location: str = os.getenv("VERTEX_LOCATION", "us-central1")
    gcs_bucket: str = os.getenv("GCS_BUCKET", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    embed_model: str = os.getenv("EMBED_MODEL", "text-embedding-004")
    store_uri: str = os.getenv("STORE_URI", "")
    index_endpoint_name: str = os.getenv("INDEX_ENDPOINT_NAME", "")
    deployed_index_id: str = os.getenv("DEPLOYED_INDEX_ID", "")

settings = Settings()
