# AI Q&A Service

LangChain과 RAG(Retrieval-Augmented Generation)를 활용한 질의응답 서비스입니다. Azure OpenAI와 MongoDB Atlas Vector Search를 사용하여 문서 기반의 정확한 답변을 제공합니다.

## 🚀 주요 기능

- **RAG 기반 질의응답**: MongoDB에 저장된 문서를 벡터 검색으로 찾아 정확한 답변 생성
- **FastAPI 웹 서버**: RESTful API를 통한 질의응답 서비스
- **Docker 컨테이너**: 쉽고 빠른 배포 및 확장
- **Azure Key Vault 연동**: 보안이 중요한 설정값들을 안전하게 관리
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
                       │ Azure Key Vault │    │ MongoDB Atlas   │
                       │ (Secrets)       │    │ Vector Search   │
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

`env.example` 파일을 참고하여 `.env` 파일을 생성하거나 Azure Key Vault를 설정하세요.

```bash
# Azure Key Vault 사용 시
AZURE_KEY_VAULT_URL=https://your-keyvault-name.vault.azure.net/

# 로컬 개발 환경 시
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2025-01-01-preview
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
docker build -t ai-qa-service .

# 컨테이너 실행
docker run -p 8000:8000 ai-qa-service

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
./deploy.sh your-docker-username v1.0.0
```

## ☁️ Azure App Services 배포

자세한 배포 방법은 [AZURE_DEPLOYMENT_GUIDE.md](AZURE_DEPLOYMENT_GUIDE.md)를 참조하세요.

### 주요 단계:

1. **Azure Key Vault 설정**
2. **Docker 이미지 빌드 및 푸시**
3. **App Service 생성 및 설정**
4. **관리 ID 및 권한 설정**
5. **환경 변수 구성**

## 🔧 개발

### 프로젝트 구조

```
project03_model/
├── model.py              # LangChain RAG 모델 (수정하지 않음)
├── main.py               # FastAPI 웹 서버
├── azure_keyvault.py     # Azure Key Vault 연동
├── requirements.txt       # Python 의존성
├── Dockerfile            # Docker 이미지 정의
├── docker-compose.yml    # 로컬 개발용 Docker Compose
├── deploy.sh             # 배포 스크립트
├── AZURE_DEPLOYMENT_GUIDE.md  # Azure 배포 가이드
└── README.md             # 프로젝트 문서
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
az webapp log tail --name myAppService --resource-group myResourceGroup
```

## 🔒 보안

- **Azure Key Vault**: API 키, 엔드포인트 등 민감한 정보 보호
- **관리 ID**: Azure 서비스 간 안전한 인증
- **환경 변수**: 프로덕션 환경에서의 설정값 분리

## 🚨 문제 해결

### 일반적인 문제들

1. **Key Vault 접근 권한 오류**
   - 관리 ID 설정 확인
   - Key Vault 액세스 정책 확인

2. **MongoDB 연결 오류**
   - IP 화이트리스트 확인
   - 연결 문자열 검증

3. **Azure OpenAI API 오류**
   - API 키 및 엔드포인트 확인
   - 배포명 및 지역 설정 확인

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🤝 기여

버그 리포트나 기능 제안은 이슈를 통해 제출해 주세요.

## 📞 지원

기술적 지원이 필요한 경우 프로젝트 이슈를 통해 문의해 주세요.