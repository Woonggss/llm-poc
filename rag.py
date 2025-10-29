import os
from dotenv import load_dotenv
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
from azure.core.exceptions import ClientAuthenticationError, HttpResponseError
from prompt import PROMPT_INSIGHT
from typing import Dict, Optional

load_dotenv()

AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_SEARCH_INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME")

def get_answer(user_text: str, selected_filters: Dict[str, Optional[str]]) -> tuple:

    """ RAG 접근 방식을 사용하여 사용자 질문에 답변을 생성합니다. """

    try:
        search_credential = AzureKeyCredential(AZURE_SEARCH_API_KEY)

        # Initialize the OpenAI client
        openai_client = AzureOpenAI(api_version="2024-06-01",
                                    azure_endpoint=AZURE_OPENAI_ENDPOINT,
                                    api_key=AZURE_OPENAI_API_KEY,
        )

        # Initialize the Search client
        search_client = SearchClient(endpoint=AZURE_SEARCH_ENDPOINT,
                                    index_name=AZURE_SEARCH_INDEX_NAME,
                                    credential=search_credential)
    
    except ClientAuthenticationError as auth_error:
        return f"인증 오류가 발생했습니다. API 키와 엔드포인트를 확인하세요. {str(auth_error)}"

    except HttpResponseError as http_error:
        return f"HTTP 응답 오류가 발생했습니다. {str(http_error)}"

    except Exception as e:
        return f"알 수 없는 오류가 발생했습니다. {str(e)}"
    
    ls_filter = [
        f"{field} eq '{value}'"
        for field, value in selected_filters.items()
        if value
    ]

    ls_facets = [
        f"{field}" for field, value in selected_filters.items()
        if not value
    ]

    filter_expression = " and ".join(ls_filter) if ls_filter else None

    print(filter_expression)
    print(ls_facets)

    result = search_client.search(
        search_text=user_text,
        query_type="semantic",
        semantic_configuration_name="review-v2-semantic-configuration",
        top=5,
        select=["product_name", "product_group", "gender", "age_group", "rating", "review_text"],
        filter=filter_expression,
        facets=ls_facets
    )

    facets = result.get_facets()
    print(f"리뷰 건수 : {facets}")
    
    docs = list(result)
    if not docs:
        return "관련 정보를 찾지 못했습니다."

    sources = "\n".join(
        f"- {doc.get('product_name', '')} ({doc.get('product_group', '')}, "
        f"{doc.get('gender', '')}, {doc.get('age_group', '')}) : "
        f"{doc.get('review_text', '')}"
        for doc in docs
    )

    print(sources)

    prompt = PROMPT_INSIGHT.format(query=user_text, sources=sources)
    
    response = openai_client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
    
    rag_answer = response.choices[0].message.content
    
    return (rag_answer, summarize_statistics(facets) if facets else None)


def summarize_statistics(data: dict) -> str:
    """
    주어진 통계 데이터(facet)를 자연어로 요약하는 함수.
    예: {'gender': [{'value': '남성', 'count': 10}, ...]}
    """
    summaries = ["**[답변 통계]**"]

    for key, values in data.items():
        # 총합 및 최다 항목 계산
        total = sum(item["count"] for item in values)
        top_item = max(values, key=lambda x: x["count"])
        detail_summary = ", ".join([f"{v['value']} {v['count']}명" for v in values])

        # 한글 키 이름 변환
        label_map = {
            "gender": "성별",
            "age_group": "연령대",
            "product_group": "제품군",
        }
        label = label_map.get(key, key)

        # 요약 문장 생성
        summaries.append(
            f"{label}별 분포는 총 {total}명 중 "
            f"{top_item['value']}({top_item['count']}명)가 가장 많습니다. "
            f"({detail_summary})"
        )

    return "\n\n".join(summaries)
