import os
import csv
from datetime import datetime
from typing import List, Dict

# Azure Search SDK
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.search.documents.indexes.models import (
    SimpleField,
    SearchField,
    SearchFieldDataType,
    SearchableField,
    SearchIndex,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
)

from langchain_openai import AzureOpenAIEmbeddings
from dotenv import load_dotenv

load_dotenv()

# =========================
# 0) 환경 변수/상수
# =========================

AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_OPENAI_EMBED_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBED_DEPLOYMENT")
AZURE_SEARCH_INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME")
CSV_PATH  = os.getenv("CSV_PATH")

# =========================
# 1) 클라이언트 준비
# ========================="

search_credential = AzureKeyCredential(AZURE_SEARCH_API_KEY)
index_client  = SearchIndexClient(endpoint=AZURE_SEARCH_ENDPOINT, credential=search_credential)
search_client = SearchClient(endpoint=AZURE_SEARCH_ENDPOINT, index_name=AZURE_SEARCH_INDEX_NAME, credential=search_credential)

embeddings = AzureOpenAIEmbeddings(
    azure_deployment=AZURE_OPENAI_EMBED_DEPLOYMENT,
    openai_api_version="2024-12-01-preview",
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
)

# 임베딩 차원 
EMBED_DIM = 1536  # "text-embedding-3-small" 모델 기준

# =========================
# 2) 인덱스 스키마 정의
# =========================
fields = [
    SimpleField(name="review_id", type=SearchFieldDataType.String, key=True, filterable=True),
    SearchableField(name="product_name",  type=SearchFieldDataType.String, filterable=True, sortable=True, facetable=True),
    SearchableField(name="product_group", type=SearchFieldDataType.String, filterable=True, sortable=True, facetable=True),
    SearchableField(name="gender",       type=SearchFieldDataType.String, filterable=True, facetable=True),
    SearchableField(name="age_group",    type=SearchFieldDataType.String, filterable=True, facetable=True),
    SimpleField(   name="rating",        type=SearchFieldDataType.Double, filterable=True, sortable=True, facetable=True),
    SearchableField(name="review_text",  type=SearchFieldDataType.String),
    # 벡터 필드
    SearchField(
        name="review_vector",
        type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
        searchable=True,
        vector_search_dimensions=EMBED_DIM,
        vector_search_profile_name="vp-hnsw",
    ),
    # 날짜
    SimpleField(name="created_at", type=SearchFieldDataType.DateTimeOffset, filterable=True, sortable=True, facetable=True),
]

vector_search = VectorSearch(
    algorithms=[HnswAlgorithmConfiguration(name="algo-hnsw", kind="hnsw")],
    profiles=[VectorSearchProfile(name="vp-hnsw", algorithm_configuration_name="algo-hnsw")]
)

semantic_config = SemanticConfiguration(
    name="sem-config",
    prioritized_fields=SemanticPrioritizedFields(
        title_field=SemanticField(field_name="product_name"),
        content_fields=[SemanticField(field_name="review_text")],
        keywords_fields=[SemanticField(field_name="product_group")],
    ),
)

semantic_search = SemanticSearch(configurations=[semantic_config])

index = SearchIndex(
    name=AZURE_SEARCH_INDEX_NAME,
    fields=fields,
    vector_search=vector_search,
    semantic_search=semantic_search,
    suggesters=[{"name": "sg", "source_fields": ["product_name", "product_group"]}],
)

# =========================
# 3) 인덱스 생성/업데이트
# =========================
print(f"Creating or updating index '{AZURE_SEARCH_INDEX_NAME}' (vector dim: {EMBED_DIM})...")
index_client.create_or_update_index(index)
print("Index ready.")

# =========================
# 4) CSV → 임베딩 → 업서트
# =========================
def to_iso_utc(s: str) -> str:
    """'YYYY-MM-DD HH:MM:SS' → 'YYYY-MM-DDTHH:MM:SSZ' (간단 변환)"""
    try:
        dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
        return dt.isoformat() + "Z"
    except Exception:
        return s  # 원문 유지

# 배치 수행을 위한 Helper
def chunked(iterable, size):
    buf = []
    for it in iterable:
        buf.append(it)
        if len(buf) >= size:
            yield buf
            buf = []
    if buf:
        yield buf

def embed_texts(texts: List[str]) -> List[List[float]]:
    # LangChain: embed_documents는 리스트 입력을 받아 임베딩을 수행
    return embeddings.embed_documents(texts)

def load_and_upload(csv_path: str, batch_size: int = 64):
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    
    # 배치 단위로 임베딩 및 업서트
    for rows_batch in chunked(rows, batch_size):
        texts = [r.get("review_text", "") or "" for r in rows_batch]
        vecs  = embed_texts(texts)

        docs_batch: List[Dict] = []
        for r, v in zip(rows_batch, vecs):
            doc = {
                "review_id":     r.get("review_id"),
                "product_name":  r.get("product_name", ""),
                "product_group": r.get("product_group", ""),
                "gender":        r.get("gender", ""),
                "age_group":     r.get("age_group", ""),
                "rating":        r.get("rating"),
                "review_text":   r.get("review_text", ""),
                "review_vector": v,
                "created_at":    to_iso_utc(r.get("created_at", "")),
            }
            docs_batch.append(doc)

        result = search_client.merge_or_upload_documents(docs_batch)
        failed = [r for r in result if not r.succeeded]
        if failed:
            raise RuntimeError(f"Upload failed for {len(failed)} docs. First error: {failed[0].error_message}")
        print(f"Uploaded batch of {len(docs_batch)} documents.")
    
    print("All documents uploaded.")

load_and_upload(CSV_PATH, batch_size=64)

# =========================
# 5) 벡터 검색 + Facet 예시
# =========================
def vector_search_example(query_text: str):
    q_vec = embeddings.embed_query(query_text)
    vq = VectorizedQuery(vector=q_vec, k=5, fields="review_vector")

    results = search_client.search(
        search_text=None,
        vector_queries=[vq],
        facets=["product_group", "gender", "age_group"],
        filter=None,  # 예) "product_group eq '스킨케어'"
    )

    print("Top hits:")
    for doc in results:
        print(f"- {doc['review_id']} | {doc.get('product_name')} | product_group={doc.get('product_group')} | review_text={doc.get('review_text')[:50]}...")

    if hasattr(results, "get_facets") and results.get_facets():
        print("\nFacets:")
        for fname, buckets in results.get_facets().items():
            print(f"  {fname}:")
            for b in buckets:
                print(f"    {b['value']} ({b['count']})")

vector_search_example("수분 공급이 잘 되는 스킨케어 제품 추천해줘")
print("Done.")
