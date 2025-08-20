# Azure Key Vault 없이 간단하게 배포하기

이 가이드는 조직 관리자가 아니어서 Service Principal을 생성할 수 없는 경우에도 Azure에 CI/CD를 할 수 있는 방법을 설명합니다.

## 🚀 빠른 시작 (가장 간단한 방법)

### 1단계: GitHub Secrets 설정

GitHub 저장소의 **Settings > Secrets and variables > Actions**에서 다음 secrets를 추가하세요:

#### 필수 Secrets
```bash
# Azure OpenAI 설정
AZURE_OPENAI_API_KEY=your-actual-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2025-01-01-preview

# MongoDB 설정
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
MONGO_DB=insurance
MONGO_COLL=documents

# Azure OpenAI 배포 설정
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4.1-mini
AZURE_OPENAI_EMB_DEPLOYMENT=text-embedding-3-small

# MongoDB 인덱스 설정
MONGO_VECTOR_INDEX=vector_index
MONGO_TEXT_INDEX=text_index

# Azure App Service 정보
AZURE_WEBAPP_NAME=rag-qna-service
AZURE_RESOURCE_GROUP=ragQnaResourceGroup
AZURE_SUBSCRIPTION_ID=your-subscription-id

# Docker Hub 설정
DOCKERHUB_USERNAME=your-dockerhub-username
DOCKERHUB_TOKEN=your-dockerhub-access-token

# Azure 배포 설정
AZURE_WEBAPP_PUBLISH_PROFILE=your-publish-profile-content
```

### 2단계: GitHub Actions 워크플로우 사용

프로젝트에 이미 `.github/workflows/deploy-simple.yml` 파일이 포함되어 있습니다. 이 파일은:

- Docker 이미지를 빌드하고 Docker Hub에 푸시
- Azure App Service에 자동 배포
- GitHub Secrets에서 환경 변수를 자동으로 설정
- 헬스체크를 통한 배포 확인

### 3단계: 자동 배포

`main` 브랜치에 코드를 푸시하면 자동으로 배포가 시작됩니다!

## 🔧 수동 배포 방법

### 방법 1: Azure CLI 사용

#### 1.1 Azure CLI 설치 및 로그인
```bash
# Azure CLI 설치 (Windows)
winget install Microsoft.AzureCLI

# Azure CLI 설치 (macOS)
brew install azure-cli

# Azure CLI 설치 (Linux)
curl -sL https://aka.ms/InstallAzureCLIDeb | bash

# 로그인
az login
```

#### 1.2 환경 변수 설정
`.env` 파일을 생성하고 필요한 값들을 설정하세요:

```bash
# .env 파일 예시
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
AZURE_WEBAPP_NAME=rag-qna-service
AZURE_RESOURCE_GROUP=ragQnaResourceGroup
AZURE_SUBSCRIPTION_ID=your-subscription-id
```

#### 1.3 배포 스크립트 실행

**Linux/Mac:**
```bash
chmod +x deploy-manual.sh
source .env && ./deploy-manual.sh
```

**Windows:**
```cmd
deploy-manual.bat
```

### 방법 2: Azure Portal에서 직접 설정

#### 2.1 App Service 환경 변수 설정
1. Azure Portal에서 App Service로 이동
2. **"설정"** → **"구성"** 클릭
3. **"애플리케이션 설정"** 탭에서 다음 추가:

```
AZURE_OPENAI_API_KEY = your-api-key
AZURE_OPENAI_ENDPOINT = https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION = 2025-01-01-preview
MONGODB_URI = mongodb+srv://username:password@cluster.mongodb.net/
MONGO_DB = insurance
MONGO_COLL = documents
AZURE_OPENAI_CHAT_DEPLOYMENT = gpt-4.1-mini
AZURE_OPENAI_EMB_DEPLOYMENT = text-embedding-3-small
MONGO_VECTOR_INDEX = vector_index
MONGO_TEXT_INDEX = text_index
```

#### 2.2 Docker 이미지 설정
1. **"설정"** → **"컨테이너 설정"** 클릭
2. **"이미지 원본"**을 **"Docker Hub"**로 설정
3. **"이미지 및 태그"**에 `hadonas/rag-qna-service:latest` 입력
4. **"저장"** 클릭

## 📋 필요한 Azure 리소스

### 1. App Service Plan
```bash
# App Service Plan 생성
az appservice plan create \
  --name ragQnaServicePlan \
  --resource-group ragQnaResourceGroup \
  --sku B1 \
  --is-linux
```

### 2. App Service
```bash
# App Service 생성
az webapp create \
  --resource-group ragQnaResourceGroup \
  --plan ragQnaServicePlan \
  --name rag-qna-service \
  --deployment-container-image-name hadonas/rag-qna-service:latest
```

### 3. 환경 변수 설정
```bash
# 환경 변수 설정
az webapp config appsettings set \
  --resource-group ragQnaResourceGroup \
  --name rag-qna-service \
  --settings \
    AZURE_OPENAI_API_KEY="your-api-key" \
    AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/" \
    MONGODB_URI="mongodb+srv://username:password@cluster.mongodb.net/"
```

## 🔍 배포 확인

### 1. 헬스체크
```bash
curl https://your-app-name.azurewebsites.net/health
```

### 2. API 문서
브라우저에서 다음 URL 접속:
```
https://your-app-name.azurewebsites.net/docs
```

### 3. Azure Portal에서 확인
- App Service 상태
- 로그 스트림
- 메트릭

## 🚨 문제 해결

### 일반적인 문제들

#### 1. 환경 변수 오류
- 모든 필수 환경 변수가 설정되었는지 확인
- 환경 변수 이름이 정확한지 확인 (대소문자 구분)

#### 2. Docker 이미지 오류
- Docker Hub에 이미지가 업로드되었는지 확인
- 이미지 이름과 태그가 정확한지 확인

#### 3. MongoDB 연결 오류
- MongoDB Atlas의 IP 화이트리스트에 Azure App Service IP 추가
- 연결 문자열이 올바른지 확인

#### 4. Azure OpenAI API 오류
- API 키가 올바른지 확인
- 배포명이 올바른지 확인
- 리소스 지역이 올바른지 확인

## 📚 추가 리소스

- [Azure App Service 공식 문서](https://docs.microsoft.com/azure/app-service/)
- [GitHub Actions 공식 문서](https://docs.github.com/en/actions)
- [Docker Hub 공식 문서](https://docs.docker.com/docker-hub/)

## 🎯 다음 단계

1. **자동화**: GitHub Actions를 통한 자동 배포 설정
2. **모니터링**: Azure Application Insights 추가
3. **보안**: Azure Key Vault 사용 (관리자 권한이 있는 경우)
4. **확장**: 여러 환경 (스테이징/프로덕션) 설정

이제 Azure Key Vault 없이도 성공적으로 Azure에 배포할 수 있습니다! 🚀
