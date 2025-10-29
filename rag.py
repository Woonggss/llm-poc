import os
from dotenv import load_dotenv
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
from azure.core.exceptions import ClientAuthenticationError, HttpResponseError
from prompt import PROMPT_INSIGHT

load_dotenv()

AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
AZURE_SEARCH_INDEX_NAME = os.getenv("AZURE_SEARCH_INDEX_NAME")

def get_answer(user_text) -> str:

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
        
    docs = list(search_client.search(
        search_text=user_text,
        query_type="semantic",
        semantic_configuration_name="review-v2-semantic-configuration",
        top=5,
        select=["product_name", "product_group", "gender", "age_group", "rating", "review_text"]
    ))

    if not docs:
        return "관련 정보를 찾지 못했습니다."

    sources = "\n".join(
        f"- {doc.get('product_name', '')} ({doc.get('product_group', '')}, "
        f"{doc.get('gender', '')}, {doc.get('age_group', '')}) : "
        f"{doc.get('review_text', '')}"
        for doc in docs
    )

    
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
    
    return rag_answer