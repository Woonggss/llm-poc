# 🚀 고객 피드백 기반 제품 개선 AI

> 고객 리뷰 데이터를 바탕으로
> **제품 개선 인사이트를 자동으로 도출**하는 AI 챗봇


## 🎯 1. 프로젝트 개요


### ✔ 대상 사용자

* 제품/상품 기업의 CX, 마케팅, 기획팀

### ✔ 문제

* 리뷰 데이터가 많아질수록 **분석 시간이 오래 걸림**
* 인사이트가 **일관되지 않음**

### ✔ 목표

* 리뷰 데이터를 바탕으로
  **필터 + 검색 + AI 분석 → 빠르고 명확하게 인사이트 제공**


## ✨ 2. 주요 기능
💬 **대화형 방식**으로, 하나의 인사이트를 도출한 뒤 자연스럽게 질문을 이어갈 수 있습니다.

| 기능            | 설명                         |
| ------------- | -------------------------- |
| 조건 기반 분석   | 성별 / 나이 / 제품군 필터 후 인사이트 제공 |
| 인사이트 자동 도출 | 요약 인사이트 / 분석 포인트 / 추가 제안  |
| 리뷰 분포 제공 | 필터링 되지 않은 조건에 대한 리뷰 분포 제공    |
| 리뷰 다운로드   | 인사이트의 근거가 되는 리뷰를 .csv 파일로 다운로드   |

## 🏗 3. 아키텍처

```
사용자
  ↓
Streamlit UI / Azure Web App (웹) 
  ↓
Azure OpenAI (LLM/Embedding)
  - 추론 모델(gpt-4.1)
  - 임베딩 모델(text-embedding-3-small)
  ↓
Azure AI Search (RAG 검색)
  - 필터 검색
  - 키워드/벡터 + 시맨틱 검색
  - Facet 기반 통계
  ↓
Azure Blob Storage (데이터 저장)
```

| 구성 요소           | 역할                              |
| --------------- | ------------------------------- |
| Streamlit       | UI / 인터랙션                       |
| Azure Web App   | 프로젝트 배포                      |
| Azure OpenAI    | 인사이트 도출 및 쿼리 임베딩                |
| Azure AI Search | Hybrid + Semantic 검색 / 필터링 / 통계 |
| Azrue Blob Storage    | 리뷰 데이터 및 검색 결과 저장                       |


## 🛠 4. 기술 스택

| 영역       | 사용 기술                               |
| -------- | ----------------------------------- |
| Frontend & Backend | Python / Streamlit                           |
| Application Hosting |  Azure Web App                          |
| AI       | Azure OpenAI(gpt-4.1, text-embedding-3-small)                        |
| Search & Retrieval   | Azure AI Search (Hybrid + Semantic) |
| Object Storage  | Azure Blob Storage                  |


---

## 🧠 5. 핵심 기술 포인트

| 포인트              | 설명                   |
| ---------------- | -------------------- |
| Hybrid Search    | 키워드 + 벡터 검색 결합(기존 키워드 검색 대비 유의미한 성능 개선 확인 - "불만, 불평"과 같이 키워드에는 등장하지 않았지만 의미 상 반영되어야 하는 질문)       |
| Semantic Ranking | 의미 기반으로 문서를 정렬하여, 사용자에게 연관도가 높은 순으로 리뷰 정보를 제공          |
| Facets 활용        | 옵션을 선택하지 않은 조건의 분포 자동 출력하여, 사용자에게 다음 질문을 유도 |
| 필터링 적용    | 채팅 UI 내에서 필터링을 유도하여, 사용자 편의성 증대 및 보다 명확한 검색 결과를 도출       |
| Blob SAS 다운로드    | private 상태의 Blob Storage에서 파일 URL 기반 다운로드 및 URL의 유효기간 설정하여 보안성 확보    |

---

## 🎬 6. 데모 시연 링크
👉 [데모 바로가기](https://pro-sean-webapp-ecc9gzgpc8btafa3.westus3-01.azurewebsites.net/)

---

## 🚧 7. 추가로 고민해 볼 사항들
기능 및 기술적으로 고민해 볼 사항들입니다.

| 보완 사항      | 설명                |
| ----------- | ----------------- |
| 기획서 초안 작성 | 대화 내용을 기반으로 기획서 초안 자동 생성 |
| 피드백 데이터 확장 | 리뷰에서 설문, VoC와 같은 데이터로 확장 가능 |
| Tool Calling 도입 | 유용하면서도 LLM 추론이 상대적으로 덜한 작업들(조건에 맞는 리뷰 데이터 전체 검색 등) |
| 적절한 top-k | 검색 시 활용할 적절한 상위 문서의 갯수 설정 |
| 답변 캐시 | 빈번한 질문에 대한 답변들은 캐시함으로써 소요되는 토큰 절감 |
| 데이터 ETL 자동화 | Azure Function App을 활용하여 주기적으로 데이터 수집-전처리-적재 |

---
## 📎 참고. 프로젝트 실행 방법

소스코드 클론 및 인덱스 초기화(`util/init_vector_index.py`) 이후

```bash
pip install -r requirements.txt
streamlit run main.py
```

또는

```bash
uv sync
uv run streamlit run main.py
```
