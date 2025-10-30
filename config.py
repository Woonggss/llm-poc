from dotenv import load_dotenv
import os

CATEGORY_CONFIG = [
    {
        "key": "gender",
        "label": "성별",
        "sample_size": 3,
        "pool": [
            "여성",
            "남성",
            "미지정"
        ],
    },
    {
        "key": "age_group",
        "label": "나이",
        "sample_size": 6,
        "pool": [
            "10대",
            "20-24세",
            "25-29세",
            "30대",
            "40대",
            "50대 이상",
        ],
    },
    {
        "key": "product_group",
        "label": "제품군",
        "sample_size": 5,
        "pool": [
            "스킨케어",
            "메이크업",
            "향수",
            "헤어케어",
            "바디케어"
        ],
    },
]


load_dotenv()

AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_SEARCH_INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME")
AZURE_OPENAI_EMBED_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBED_DEPLOYMENT")
AZURE_STORAGE_ACCOUNT = os.getenv("AZURE_STORAGE_ACCOUNT")
AZURE_STORAGE_KEY = os.getenv("AZURE_STORAGE_KEY")
AZURE_STORAGE_CONTAINER = os.getenv("AZURE_STORAGE_CONTAINER")
AZURE_STORAGE_ENDPOINT = os.getenv("AZURE_STORAGE_ENDPOINT")