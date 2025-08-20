# AI Q&A Service

LangChain과 RAG(Retrieval-Augmented Generation)를 활용한 질의응답 서비스입니다. Azure OpenAI와 MongoDB Atlas Vector Search를 사용하여 문서 기반의 정확한 답변을 제공합니다.

## 🚀 주요 기능

- **RAG 기반 질의응답**: MongoDB에 저장된 문서를 벡터 검색으로 찾아 정확한 답변 생성
- **하이브리드 검색**: 텍스트 검색과 벡터 검색을 결합한 고성능 검색
- **객체 캐싱**: 환경 설정 및 모델 로딩 부하를 최소화하는 효율적인 구조
- **품질 평가**: AI가 생성한 답변의 품질을 자동으로 평가
- **FastAPI 웹 서버**: RESTful API를 통한 질의응답 서비스
- **Docker 컨테이너**: 쉽고 빠른 배포 및 확장
- **CI/CD 파이프라인**: GitHub Actions를 통한 자동화된 배포
- **Azure Key Vault**: 보안이 중요한 설정값들을 안전하게 관리
- **Azure App Services 지원**: 클라우드 환경에서의 원활한 운영

## 🏗️ 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client App    │───▶│   FastAPI       │───▶│   RAGApp        │
│                 │    │   Web Server    │    │   (캐싱된 객체)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                        ┌─────────────────┐    ┌─────────────────┐
                        │ Azure Key Vault │    │ MongoDB Atlas   │
                        │ (Secrets)       │    │ Hybrid Search   │
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
- MongoDB Atlas 계정 (vector_index와 text_index 인덱스 필요)

### 1. 저장소 클론

```bash
git clone <repository-url>
cd project03_model
```

### 2. 환경 변수 설정

`env.example` 파일을 참고하여 `.env` 파일을 생성하세요.

```bash
# Azure Key Vault 설정 (선택사항)
AZURE_KEY_VAULT_URL=https://your-keyvault-name.vault.azure.net/

# Azure OpenAI 설정
AZURE_OPENAI_API_KEY=your-azure-openai-api-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2025-01-01-preview

# MongoDB 설정
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/

# MongoDB 검색 인덱스 (하이브리드 검색용)
MONGO_VECTOR_INDEX=vector_index
MONGO_TEXT_INDEX=text_index
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

## 🚀 CI/CD 및 자동 배포

### GitHub Actions CI/CD

이 프로젝트는 GitHub Actions를 통해 자동화된 CI/CD 파이프라인을 제공합니다:

- **자동 테스트**: 코드 품질 검사 및 테스트 실행
- **Docker 빌드**: 자동 이미지 빌드 및 Docker Hub 푸시
- **자동 배포**: Azure App Service 자동 배포 (스테이징/프로덕션)

**설정 방법**: [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md) 참조

### Azure Key Vault 통합

Azure Key Vault를 활용하여 민감한 정보를 안전하게 관리:

- **자동 환경 변수 로드**: Key Vault에서 시크릿 자동 로드
- **보안 강화**: API 키, 엔드포인트 등 민감 정보 보호
- **CI/CD 통합**: GitHub Actions와 연동하여 보안 강화

**설정 방법**: [AZURE_KEYVAULT_CI_CD.md](AZURE_KEYVAULT_CI_CD.md) 참조

## ☁️ Azure App Services 배포

### 배포 방법

자세한 배포 방법은 다음 가이드를 참조하세요:

- **[AZURE_DEPLOYMENT_SIMPLE.md](AZURE_DEPLOYMENT_SIMPLE.md)** - Azure Key Vault 없이 배포
- **[AZURE_DEPLOYMENT_GUIDE.md](AZURE_DEPLOYMENT_GUIDE.md)** - Azure Key Vault 사용하여 배포 (보안 강화)

### 주요 단계:

1. **Docker 이미지 빌드 및 푸시**
2. **App Service 생성 및 설정**
3. **환경 변수 설정 (Key Vault 또는 직접)**
4. **서비스 테스트 및 모니터링**

## 🔧 개발

### 프로젝트 구조

```
project03_model/
├── .github/workflows/           # GitHub Actions CI/CD 워크플로우
│   └── deploy.yml              # 자동 배포 워크플로우
├── langchain_qa.py             # RAG 모델 (객체 캐싱, 하이브리드 검색)
├── main.py                     # FastAPI 웹 서버
├── azure_keyvault.py           # Azure Key Vault 연동
├── requirements.txt             # Python 의존성
├── Dockerfile                  # Docker 이미지 정의
├── docker-compose.yml          # 로컬 개발용 Docker Compose
├── .dockerignore               # Docker 빌드 제외 파일
├── env.example                 # 환경 변수 템플릿
├── README.md                   # 프로젝트 문서
├── GITHUB_ACTIONS_SETUP.md     # GitHub Actions 설정 가이드
├── AZURE_KEYVAULT_CI_CD.md     # Azure Key Vault CI/CD 통합 가이드
├── AZURE_DEPLOYMENT_SIMPLE.md  # 간단한 Azure 배포 가이드
└── AZURE_DEPLOYMENT_GUIDE.md   # Azure Key Vault 사용 배포 가이드
```

### 새로운 모델의 특징

- **객체 캐싱**: `@lru_cache`를 사용하여 RAGApp 객체를 한 번만 생성
- **하이브리드 검색**: 텍스트 검색과 벡터 검색을 결합한 RRF(Rank Reciprocal Fusion) 방식
- **품질 평가**: AI 답변의 품질을 자동으로 평가하여 success 필드 결정
- **효율적인 초기화**: 환경 설정과 모델 로딩을 한 번만 수행

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

### Azure Key Vault 활용

- **민감 정보 보호**: API 키, 엔드포인트 등 민감한 정보를 Key Vault에 저장
- **자동 로드**: 애플리케이션 시작 시 자동으로 환경 변수 로드
- **접근 제어**: 관리 ID를 통한 안전한 인증

### 보안 강화 방안

1. **IP 제한**: 특정 IP에서만 App Service 접근 허용
2. **HTTPS 강제**: HTTP에서 HTTPS로 리다이렉트 설정
3. **정기적인 키 순환**: API 키를 정기적으로 변경
4. **모니터링**: 비정상적인 접근 패턴 감지

## 🚨 문제 해결

### 일반적인 문제들

1. **환경 변수 오류**
   - 모든 필수 환경 변수가 설정되었는지 확인
   - 환경 변수 이름이 정확한지 확인 (대소문자 구분)

2. **MongoDB 연결 오류**
   - MongoDB Atlas의 IP 화이트리스트에 Azure App Service IP 추가
   - 연결 문자열이 올바른지 확인
   - vector_index와 text_index 인덱스가 생성되었는지 확인

3. **Azure OpenAI API 오류**
   - API 키가 올바른지 확인
   - 배포명이 올바른지 확인
   - 리소스 지역이 올바른지 확인

4. **Key Vault 접근 오류**
   - 관리 ID가 올바르게 설정되었는지 확인
   - Key Vault 액세스 정책이 올바르게 설정되었는지 확인

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.
## 🤝 기여

버그 리포트나 기능 제안은 이슈를 통해 제출해 주세요.

## 📞 지원

기술적 지원이 필요한 경우 프로젝트 이슈를 통해 문의해 주세요.
