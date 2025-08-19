import os, json
from typing import Optional, Dict, List

from dotenv import load_dotenv
from pymongo import MongoClient

from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser


# =========================
# 0) 환경설정
# =========================
load_dotenv()  # .env에 키/엔드포인트/버전/MONGODB_URI 저장 권장

# 필수 환경변수 (이미 os.environ에 설정되어 있어도 사용 가능)
AZURE_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")

# Azure 배포명 (deployment name)
CHAT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4.1-mini")
EMB_DEPLOYMENT  = os.getenv("AZURE_OPENAI_EMB_DEPLOYMENT",  "text-embedding-ada-002")

# MongoDB
MONGO_URI = os.getenv("MONGODB_URI")  # "mongodb+srv://..."
DB_NAME = os.getenv("MONGO_DB", "insurance")
COLL_NAME = os.getenv("MONGO_COLL", "documents")
VECTOR_INDEX = os.getenv("MONGO_VECTOR_INDEX", "vector_idx")  # Atlas Vector Search 인덱스명

# =========================
# 1) 클라이언트/모델
# =========================
# Mongo
mongo = MongoClient(MONGO_URI)
col = mongo[DB_NAME][COLL_NAME]

# Chat / Embedding (Azure 배포명 사용)
llm = AzureChatOpenAI(
    azure_deployment=CHAT_DEPLOYMENT,
    api_version=AZURE_API_VERSION,
    temperature=0.1,
)

emb = AzureOpenAIEmbeddings(
    azure_deployment=EMB_DEPLOYMENT,
    api_version=AZURE_API_VERSION,
)


# =========================
# 2) 벡터 검색
# =========================
def mongo_vector_search(
    query: str,
    k: int = 4,
    num_candidates: int = 200,
    filters: Optional[Dict] = None,
) -> List[Dict]:
    """Atlas $vectorSearch 파이프라인으로 상위 k개 검색."""
    qvec = emb.embed_query(query)
    pipeline = [
        {
            "$vectorSearch": {
                "index": VECTOR_INDEX,
                "path": "embedding",
                "queryVector": qvec,
                "numCandidates": num_candidates,
                "limit": k,
            }
        },
        *([{ "$match": filters }] if filters else []),
        {
            "$project": {
                "content": 1,
                "source": 1,
                "page_number": 1,
                "_score": { "$meta": "vectorSearchScore" },
            }
        },
    ]
    return list(col.aggregate(pipeline))


def format_docs(docs: List[Dict]) -> str:
    """검색 문서를 LLM 컨텍스트 문자열로 정리."""
    lines = []
    for i, d in enumerate(docs, 1):
        src = d.get("source", "unknown")
        page = d.get("page_number")
        head = f"[{i}] ({src}" + (f", p.{page})" if page is not None else ")")
        body = (d.get("content") or "").strip()
        score = d.get("_score", 0.0)
        lines.append(f"{head}  score={score:.3f}\n{body}")
    return "\n\n".join(lines)


# =========================
# 3) 프롬프트 & 체인
# =========================
SYSTEM = (
    "너는 근거 기반으로 답한다. 제공된 컨텍스트 범위에서만 간결하고 정확하게 답하고, "
    "모르면 모른다고 말해라."
)
USER = """질문:
{question}

컨텍스트:
{context}
"""

prompt = ChatPromptTemplate.from_messages([("system", SYSTEM), ("user", USER)])

def retrieve_fn(q: str) -> List[Dict]:
    return mongo_vector_search(q, k=4)

rag_chain = (
    {
        "context": RunnableLambda(lambda q: format_docs(retrieve_fn(q))),
        "question": RunnablePassthrough(),
    }
    | prompt
    | llm
    | StrOutputParser()
)


# --- 설정 (필요시 네 값으로 덮어쓰기) ---
INDEX_NAME = "vector_index"  # ← Atlas Vector Search 인덱스명

# --- 프롬프트 (출처는 본문에 넣지 않도록) ---
SYSTEM = (
    "너는 제공된 컨텍스트에서만 근거를 찾아 간결하고 정확하게 답한다. "
    "컨텍스트에 없으면 모른다고 답하라. 답변 본문에 출처 표기는 하지 마라."
)
USER = """질문:
{question}

컨텍스트:
{context}
"""
prompt = ChatPromptTemplate.from_messages([("system", SYSTEM), ("user", USER)])

# --- 컨텍스트 문자열 생성(점수 제외, 깔끔하게) ---
def _format_context(docs: List[Dict]) -> str:
    chunks = []
    for i, d in enumerate(docs, 1):
        src = d.get("source") or "unknown"
        page = d.get("page_number")
        head = f"[{i}] ({os.path.basename(src) if isinstance(src, str) else src}"
        head += f", p.{page})" if page is not None else ")"
        body = (d.get("content") or "").strip()
        chunks.append(f"{head}\n{body}")
    return "\n\n".join(chunks)

# --- citations 구성 (중복 제거) ---
def _build_citations(docs: List[Dict]) -> List[Dict]:
    seen = set()
    cites = []
    for d in docs:
        title = d.get("source") or "unknown"
        if isinstance(title, str):
            title = os.path.basename(title)
        page = d.get("page_number")
        key = (title, page)
        if key in seen:
            continue
        seen.add(key)
        cites.append({"title": title, "page": page})
    return cites

# --- Atlas Vector Search 래퍼 (네가 만든 함수 써도 됨) ---
def mongo_vector_search(query: str, k: int = 4, num_candidates: int = 400, filters: Optional[Dict]=None):
    qvec = emb.embed_query(query)
    pipeline = [
        {
            "$vectorSearch": {
                "index": INDEX_NAME,
                "path": "embedding",
                "queryVector": qvec,
                "numCandidates": num_candidates,
                "limit": k,
            }
        },
        *([{ "$match": filters }] if filters else []),
        { "$project": {
            "content": 1, "source": 1, "page_number": 1,
            "_score": { "$meta": "vectorSearchScore" }
        }}
    ]
    return list(col.aggregate(pipeline))

# --- 최종: JSON 형태로 반환 ---
def answer_json(question: str) -> Dict:
    try:
        docs = mongo_vector_search(question, k=4)
        context = _format_context(docs)
        messages = prompt.format_messages(question=question, context=context)
        ai = llm.invoke(messages).content

        return {
            "success": True,
            "messages": [
                {"HumanMessage": question},
                {"AIMessage": ai}
            ],
            "citations": _build_citations(docs)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "messages": [{"HumanMessage": question}],
            "citations": []
        }

# --- 사용 예시 ---
if __name__ == "__main__":
    q = "자동차보험료 계산 방법 알려줘"
    result = answer_json(q)
    # 파이썬 dict → JSON 문자열 출력
    print(json.dumps(result, ensure_ascii=False, indent=2))