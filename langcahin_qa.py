# rag_app.py
import os, json, re
from typing import Dict, List, Optional
from functools import lru_cache
from dotenv import load_dotenv
from pymongo import MongoClient

from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

class RAGApp:
    def __init__(self):
        load_dotenv()  # 프로세스당 1회면 충분 (여러 번 호출돼도 문제 없음)

        # --- env ---
        self.MONGO_URI   = os.getenv("MONGODB_URI")
        self.DB_NAME     = os.getenv("MONGO_DB", "insurance")
        self.COLL_NAME   = os.getenv("MONGO_COLL", "documents")
        self.VECTOR_IDX  = os.getenv("MONGO_VECTOR_INDEX", "vector_index")
        self.TEXT_IDX    = os.getenv("MONGO_TEXT_INDEX", "text_index")

        api_ver = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
        chat_dep = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT", "gpt-4.1-mini")
        emb_dep  = os.getenv("AZURE_OPENAI_EMB_DEPLOYMENT", "text-embedding-3-small")

        # --- clients (한 번만) ---
        self.mongo = MongoClient(self.MONGO_URI)
        self.col   = self.mongo[self.DB_NAME][self.COLL_NAME]

        self.llm = AzureChatOpenAI(azure_deployment=chat_dep, api_version=api_ver, temperature=0.1)
        self.emb = AzureOpenAIEmbeddings(azure_deployment=emb_dep, api_version=api_ver)

        # --- prompt (한 번만) ---
        SYSTEM = ("너는 제공된 컨텍스트에서만 근거를 찾아 간결하고 정확하게 답한다. "
                  "컨텍스트에 없으면 모른다고 답하라. 답변 본문에 출처 표기는 하지 마라.")
        USER = "질문:\n{question}\n\n컨텍스트:\n{context}\n"
        self.prompt = ChatPromptTemplate.from_messages([("system", SYSTEM), ("user", USER)])

        # 질문/답변만 보고 성공판정
        JUDGE_SYS = (
    "너는 답변 품질 심판이다. 질문과 답변을 보고 판단하라"
    "다음 기준으로 success를 결정하고 JSON만 출력하라. "
    "- 스스로 회피(예: 모름/정보 없음/컨텍스트 없음 등)나 동문서답이면 실패."
        )

        JUDGE_USER = """질문:
{question}

답변:
{answer}

JSON만 출력:
{{
  "success": <True|False>,
}}
"""
        self.judge_prompt = ChatPromptTemplate.from_messages([("system", JUDGE_SYS), ("user", JUDGE_USER)])

    # ---------- 유틸 ----------
    @staticmethod
    def _format_context(docs: List[Dict]) -> str:
        import os as _os
        chunks = []
        for i, d in enumerate(docs, 1):
            src  = d.get("source") or "unknown"
            page = d.get("page_number")
            head = f"[{i}] ({_os.path.basename(src) if isinstance(src,str) else src}"
            head += f", p.{page})" if page is not None else ")"
            body = (d.get("content") or "").strip()
            chunks.append(f"{head}\n{body}")
        return "\n\n".join(chunks)

    @staticmethod
    def _build_citations(docs: List[Dict]) -> List[Dict]:
        import os as _os
        seen, cites = set(), []
        for d in docs:
            title = d.get("source") or "unknown"
            if isinstance(title, str): title = _os.path.basename(title)
            page = d.get("page_number")
            key = (title, page)
            if key in seen: continue
            seen.add(key); cites.append({"title": title, "page": page})
        return cites

    # ---------- 검색 (요청마다) ----------
    def _atlas_text_search(self, query: str, k: int = 20, filters: Optional[Dict]=None, paths=["content"]):
        pipe = [{"$search": {"index": self.TEXT_IDX, "text": {"query": query, "path": paths}}}]
        if filters: pipe.append({"$match": filters})
        pipe += [
            {"$project": {"_id":1, "content":1, "source":1, "page_number":1,
                          "_lexScore": {"$meta":"searchScore"}}},
            {"$limit": k}
        ]
        return list(self.col.aggregate(pipe))

    def _atlas_vector_search(self, query: str, k: int = 20, num_candidates: int = 400, filters: Optional[Dict]=None):
        qvec = self.emb.embed_query(query)
        pipe = [{"$vectorSearch": {"index": self.VECTOR_IDX, "path": "embedding",
                                   "queryVector": qvec, "numCandidates": num_candidates, "limit": k}}]
        if filters: pipe.append({"$match": filters})
        pipe += [{"$project": {"_id":1, "content":1, "source":1, "page_number":1,
                               "_semScore":{"$meta":"vectorSearchScore"}}}]
        return list(self.col.aggregate(pipe))

    @staticmethod
    def _rrf_fuse(lex_docs: List[Dict], sem_docs: List[Dict], k: int = 60, topk: int = 6) -> List[Dict]:
        rank = {}
        for i, d in enumerate(lex_docs):
            _id = d["_id"]; score = 1.0/(k+i+1)
            rank.setdefault(_id, {"doc": d, "score": 0.0})
            rank[_id]["score"] += score
        for i, d in enumerate(sem_docs):
            _id = d["_id"]; score = 1.0/(k+i+1)
            rank.setdefault(_id, {"doc": d, "score": 0.0})
            rank[_id]["doc"] = d
            rank[_id]["score"] += score
        fused = sorted(rank.values(), key=lambda x: x["score"], reverse=True)
        docs = [x["doc"] for x in fused[:topk]]
        for d in docs: d.setdefault("_lexScore", 0.0); d.setdefault("_semScore", 0.0)
        return docs

    def hybrid_search(self, query: str, k: int = 6, num_candidates: int = 800, filters: Optional[Dict]=None):
        sem = self._atlas_vector_search(query, k=max(k*5, 20), num_candidates=num_candidates, filters=filters)
        lex = self._atlas_text_search(query, k=max(k*5, 20), filters=filters)
        if not sem and not lex: return []
        if not sem: return lex[:k]
        if not lex: return sem[:k]
        return self._rrf_fuse(lex, sem, k=60, topk=k)

    # ---------- judge (질문/답변만) ----------
    def judge_qa(self, question: str, answer: str) -> Dict:
        if not answer or not answer.strip():
            return {"success": False}
        msgs = self.judge_prompt.format_messages(question=question, answer=answer)
        raw  = self.llm.invoke(msgs).content
        try:
            j = json.loads(raw)
        except Exception:
            j = {"success": False}
        j["success"] = bool(j.get("success", False))
        return j

    # ---------- 최종 API ----------
    def answer_json(self, question: str) -> Dict:
        docs = self.hybrid_search(question, k=5)
        context = self._format_context(docs)
        msgs = self.prompt.format_messages(question=question, context=context)
        ai   = self.llm.invoke(msgs).content
        return {
            "success": self.judge_qa(question, ai)["success"],
            "messages": [{"HumanMessage": question}, {"AIMessage": ai}],
            "citations": self._build_citations(docs)
        }


@lru_cache(maxsize=1)
def get_app() -> RAGApp:
    return RAGApp()


app = get_app()  # ← 초기화 1회
q = "가족과 형제·자매 한정운전 특별약관 알려줘"  # ← 요청마다 바뀜
result = app.answer_json(q)  # ← 요청마다 실행
result_json = json.dumps(result, ensure_ascii=False, indent=2)
print(result_json)