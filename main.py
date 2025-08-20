from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List
import uvicorn
import logging
import os

# Azure Key Vault에서 환경 변수 로드 (선택적)
try:
    import azure_keyvault
    logger.info("Azure Key Vault 모듈 로드 성공")
except ImportError as e:
    logging.warning(f"Azure Key Vault 모듈 로드 실패: {e}")

# langchain_qa.py에서 RAGApp 클래스 import
try:
    from langchain_qa import get_app
    logger.info("LangChain QA 모듈 로드 성공")
except ImportError as e:
    logging.error(f"LangChain QA 모듈 로드 실패: {e}")
    raise

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Q&A Service",
    description="LangChain과 RAG를 활용한 질의응답 서비스",
    version="1.0.0"
)

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response 모델 정의
class QnARequest(BaseModel):
    input_message: str

class QnAResponse(BaseModel):
    success: bool
    messages: List[Dict[str, str]]
    citations: List[Dict[str, str]]

class ErrorResponse(BaseModel):
    success: bool
    error: str

@app.get("/")
async def root():
    """헬스체크용 루트 엔드포인트"""
    logger.info("Root endpoint accessed")
    return {"message": "AI Q&A Service is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    """헬스체크 엔드포인트"""
    logger.info("Health check endpoint accessed")
    
    # 기본적인 서비스 상태 확인
    health_status = {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z",  # 실제로는 datetime.now().isoformat() 사용
        "service": "AI Q&A Service",
        "version": "1.0.0"
    }
    
    # 환경변수 상태 확인
    try:
        required_env_vars = [
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_ENDPOINT", 
            "MONGODB_URI"
        ]
        
        missing_vars = []
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            health_status["status"] = "degraded"
            health_status["missing_env_vars"] = missing_vars
            health_status["message"] = f"Missing environment variables: {', '.join(missing_vars)}"
        else:
            health_status["message"] = "All required environment variables are set"
            
    except Exception as e:
        logger.error(f"Health check error: {e}")
        health_status["status"] = "error"
        health_status["error"] = str(e)
    
    return health_status

@app.post("/qna", response_model=QnAResponse)
async def qna_endpoint(request: QnARequest):
    """
    질문을 받아서 AI 모델을 통해 답변을 생성하는 엔드포인트
    """
    try:
        logger.info(f"Received question: {request.input_message}")
        
        # langchain_qa.py의 RAGApp 객체 활용 (캐싱된 객체 사용)
        rag_app = get_app()
        result = rag_app.answer_json(request.input_message)
        
        if result.get("success"):
            logger.info("Successfully generated response")
            return QnAResponse(**result)
        else:
            logger.info("Model generated response but quality check failed")
            # 성공하지 않았지만 에러는 아님 - 모델이 답변을 생성했지만 품질이 낮음
            return QnAResponse(**result)
            
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

if __name__ == "__main__":
    logger.info("Starting AI Q&A Service...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
