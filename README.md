# AI Q&A Service

LangChain과 RAG(Retrieval-Augmented Generation)를 활용한 질의응답 서비스입니다. Azure OpenAI와 MongoDB Atlas Vector Search를 사용하여 문서 기반의 정확한 답변을 제공합니다.

## 🚀 주요 기능

- **RAG 기반 질의응답**: MongoDB에 저장된 문서를 벡터 검색으로 찾아 정확한 답변 생성
- **FastAPI 웹 서버**: RESTful API를 통한 질의응답 서비스
- **Docker 컨테이너**: 쉽고 빠른 배포 및 확장
- **Azure App Services 지원**: 클라우드 환경에서의 원활한 운영

## 🏗️ 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client App    │───▶│   FastAPI       │───▶│   LangChain     │
│                 │    │   Web Server    │    │   RAG Chain     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                        ┌─────────────────┐    ┌─────────────────┐
                        │ Environment     │    │ MongoDB Atlas   │
                        │ Variables       │    │ Vector Search   │
                        └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                        ┌─────────────────┐    ┌─────────────────┐
                        │ Azure OpenAI    │    │ Document Store  │
                        │ (GPT-4, Embed) │    │ (Insurance)     │
                        └─────────────────┘    └─────────────────┘
```

## 📋 API 명세

### POST /qna

**Request:**
```json
{
    "input_message": "자동차보험료 계산 방법 알려줘"
}
```

**Response (200 OK):**
```json
{
    "success": true,
    "messages": [
        {"HumanMessage": "자동차보험료 계산 방법 알려줘"},
        {"AIMessage": "자동차보험료는 다음과 같이 계산됩니다..."}
    ],
    "citations": [
        {"title": "보험료계산서.pdf", "page": 15},
        {"title": "자동차보험가이드.pdf", "page": 23}
    ]
}
```

**Response (422/500):**
```json
{
    "success": false,
    "error": "Error message"
}
```

## 🛠️ 설치 및 실행

### 사전 요구사항

- Python 3.11+
- Docker
- Azure 구독
- MongoDB Atlas 계정

### 1. 저장소 클론

```bash
git clone <repository-url>
cd project03_model
```

### 2. 환경 변수 설정

`env.example` 파일을 참고하여 `.env` 파일을 생성하세요.

```bash
# Azure OpenAI 설정
AZURE_OPENAI_API_KEY=your-azure-openai-api-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2025-01-01-preview

# MongoDB 설정
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

### 4. 로컬 실행

```bash
python main.py
```

또는

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Docker로 실행

```bash
# 이미지 빌드
docker build -t rag-qna-service .

# 컨테이너 실행
docker run -p 8000:8000 rag-qna-service

# 또는 Docker Compose 사용
docker-compose up --build
```

## 🐳 Docker Hub 배포

### 1. Docker Hub 로그인

```bash
docker login
```

### 2. 배포 스크립트 실행

```bash
# 실행 권한 부여
chmod +x deploy.sh

# 배포 실행
./deploy.sh hadonas v1.0.0
```

## ☁️ Azure App Services 배포

### 🚨 중요: 보안 고려사항

**현재 방식은 보안상 권장되지 않습니다.** 프로덕션 환경에서는 Azure Key Vault 사용을 강력히 권장합니다.

### 배포 방법

자세한 배포 방법은 다음 가이드를 참조하세요:

- **[AZURE_DEPLOYMENT_SIMPLE.md](AZURE_DEPLOYMENT_SIMPLE.md)** - Azure Key Vault 없이 배포 (현재 권장)
- **[AZURE_DEPLOYMENT_GUIDE.md](AZURE_DEPLOYMENT_GUIDE.md)** - Azure Key Vault 사용하여 배포 (보안 강화)

### 주요 단계:

1. **Docker 이미지 빌드 및 푸시**
2. **App Service 생성 및 설정**
3. **환경 변수 직접 설정**
4. **서비스 테스트 및 모니터링**

## 🔧 개발

### 프로젝트 구조

```
project03_model/
├── model.py                      # LangChain RAG 모델 (수정하지 않음)
├── main.py                       # FastAPI 웹 서버
├── requirements.txt              # Python 의존성
├── Dockerfile                    # Docker 이미지 정의
├── docker-compose.yml            # 로컬 개발용 Docker Compose
├── deploy.sh                     # 배포 스크립트
├── AZURE_DEPLOYMENT_SIMPLE.md   # 간단한 Azure 배포 가이드
├── AZURE_DEPLOYMENT_GUIDE.md    # Azure Key Vault 사용 배포 가이드
├── azure_app_settings.json      # Azure App Service 환경 변수 템플릿
└── README.md                     # 프로젝트 문서
```

### 로컬 개발

```bash
# 개발 서버 실행 (자동 리로드)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# API 문서 확인
# http://localhost:8000/docs
```

## 📊 모니터링

### 헬스체크

```bash
curl http://localhost:8000/health
```

### 로그 확인

```bash
# Docker 컨테이너 로그
docker logs <container-id>

# Azure App Service 로그
az webapp log tail --name rag-qna-service --resource-group ragQnaResourceGroup
```

## 🔒 보안

### 현재 방식의 제한사항

- **환경 변수 노출**: Azure Portal에서 환경 변수가 평문으로 표시됨
- **접근 권한**: App Service에 접근할 수 있는 모든 사용자가 환경 변수 확인 가능

### 보안 강화 방안

1. **IP 제한**: 특정 IP에서만 App Service 접근 허용
2. **HTTPS 강제**: HTTP에서 HTTPS로 리다이렉트 설정
3. **정기적인 키 순환**: API 키를 정기적으로 변경
4. **Azure Key Vault 사용**: 관리자에게 Key Vault 접근 권한 요청

## 🚨 문제 해결

### 일반적인 문제들

1. **환경 변수 오류**
   - 모든 필수 환경 변수가 설정되었는지 확인
   - 환경 변수 이름이 정확한지 확인 (대소문자 구분)

2. **MongoDB 연결 오류**
   - MongoDB Atlas의 IP 화이트리스트에 Azure App Service IP 추가
   - 연결 문자열이 올바른지 확인

3. **Azure OpenAI API 오류**
   - API 키가 올바른지 확인
   - 배포명이 올바른지 확인
   - 리소스 지역이 올바른지 확인

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🤝 기여

버그 리포트나 기능 제안은 이슈를 통해 제출해 주세요.

## 📞 지원

기술적 지원이 필요한 경우 프로젝트 이슈를 통해 문의해 주세요.