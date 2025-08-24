import argparse, json
from typing import Dict, Iterable, List

from google.cloud import aiplatform
from google.cloud.aiplatform_v1.types import IndexDatapoint
from tqdm import tqdm

from src.shared.gcp_clients import GCSClient

# ---------- IO ----------
def iter_jsonl_gcs(gcs: GCSClient, uri: str, limit: int | None = None):
    with gcs.open(uri, "r") as f:
        for i, line in enumerate(f):
            if limit and i >= limit:
                break
            yield json.loads(line)

# ---------- Index lifecycle ----------
def create_index(project: str, location: str, display_name: str, dim: int, distance: str):
    """
    distance: "COSINE", "DOT_PRODUCT", or "EUCLIDEAN"
    """
    aiplatform.init(project=project, location=location)
    idx = aiplatform.MatchingEngineIndex.create_tree_ah_index(
        display_name=display_name,
        dimensions=dim,
        distance_measure_type=distance,
        # small demo-friendly defaults:
        leaf_node_embedding_count=1000,
        leaf_nodes_to_search_percent=10,
        approximate_neighbors_count=20,
        shard_size="SHARD_SIZE_SMALL", 
        description="ArXiv demo index",
        labels={"app":"arxiv-research-agent"},
        sync=True,
    )
    print(f" Created Index: {idx.resource_name}")
    return idx

def create_index_endpoint(project: str, location: str, display_name: str):
    aiplatform.init(project=project, location=location)
    ep = aiplatform.MatchingEngineIndexEndpoint.create(
        display_name=display_name,
        description="ArXiv demo endpoint",
        labels={"app":"arxiv-research-agent"},
        public_endpoint_enabled=True,
        sync=True,
    )
    print(f" Created IndexEndpoint: {ep.resource_name}")
    return ep

def deploy_index(index: aiplatform.MatchingEngineIndex,
                 endpoint: aiplatform.MatchingEngineIndexEndpoint,
                 deployed_index_id: str):
    endpoint.deploy_index(
        index=index,
        deployed_index_id=deployed_index_id,
        machine_type="e2-standard-2",   # tiny, cheap
        min_replica_count=1,
        max_replica_count=1,
        sync=True,
    )
    print(f" Deployed Index: deployed_index_id={deployed_index_id}")

# ---------- Upsert ----------
def make_datapoint(dp_id: str, vector: List[float]) -> IndexDatapoint:
    # Note: IndexDatapoint takes a plain list of floats for feature_vector
    return IndexDatapoint(datapoint_id=dp_id, feature_vector=vector)

def upsert_embeddings(endpoint: aiplatform.MatchingEngineIndexEndpoint,
                      deployed_index_id: str,
                      emb_uri: str,
                      dim: int,
                      batch_size: int = 100,
                      limit: int | None = None):
    gcs = GCSClient()
    batch: List[IndexDatapoint] = []
    total = 0

    for rec in tqdm(iter_jsonl_gcs(gcs, emb_uri, limit=limit), desc="upserting"):
        vec = rec.get("embedding")
        if not vec or len(vec) != dim:
            continue
        batch.append(make_datapoint(rec["id"], vec))

        if len(batch) >= batch_size:
            endpoint.upsert_datapoints(
                deployed_index_id=deployed_index_id,
                datapoints=batch,
                sync=True,
            )
            total += len(batch)
            batch = []

    if batch:
        endpoint.upsert_datapoints(
            deployed_index_id=deployed_index_id,
            datapoints=batch,
            sync=True,
        )
        total += len(batch)

    print(f" Upserted {total} datapoints.")

# ---------- Runner ----------
def run(project: str, location: str, dim: int, distance: str,
        embeddings_uri: str, index_name: str, endpoint_name: str, deployed_index_id: str,
        batch_size: int = 100, limit: int | None = None):

    aiplatform.init(project=project, location=location)

    index = create_index(project, location, index_name, dim, distance)
    endpoint = create_index_endpoint(project, location, endpoint_name)
    deploy_index(index, endpoint, deployed_index_id)

    upsert_embeddings(endpoint, deployed_index_id, embeddings_uri, dim, batch_size=batch_size, limit=limit)

    print("Done. Save these for Module 4:")
    print(f"INDEX_ENDPOINT_NAME={endpoint.resource_name}")
    print(f"DEPLOYED_INDEX_ID={deployed_index_id}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", required=True)
    ap.add_argument("--location", default="us-central1")
    ap.add_argument("--dim", type=int, required=True, help="Embedding dimension (e.g., 384 for e5-small-v2)")
    # ap.add_argument("--distance", default="DOT_PRODUCT", choices=["COSINE","DOT_PRODUCT","EUCLIDEAN"])
    ap.add_argument(
    "--distance",
    default="COSINE_DISTANCE",
    choices=["COSINE_DISTANCE", "DOT_PRODUCT_DISTANCE", "SQUARED_L2_DISTANCE"],
)
    ap.add_argument("--embeddings", required=True)
    ap.add_argument("--index_name", default="arxiv-index-small")
    ap.add_argument("--endpoint_name", default="arxiv-index-endpoint-small")
    ap.add_argument("--deployed_index_id", default="arxiv-small")
    ap.add_argument("--batch_size", type=int, default=100)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    run(
        project=args.project,
        location=args.location,
        dim=args.dim,
        distance=args.distance,
        embeddings_uri=args.embeddings,
        index_name=args.index_name,
        endpoint_name=args.endpoint_name,
        deployed_index_id=args.deployed_index_id,
        batch_size=args.batch_size,
        limit=args.limit,
    )
