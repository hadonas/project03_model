# Azure App Services 간단 배포 가이드 (Key Vault 없음)

이 가이드는 Azure Key Vault 없이 AI Q&A Service를 Azure App Services에 Docker 컨테이너로 배포하는 방법을 설명합니다.

## 🚨 주의사항

**이 방식은 보안상 권장되지 않습니다.** 프로덕션 환경에서는 Azure Key Vault 사용을 강력히 권장합니다.

## 사전 준비사항

1. **Azure 구독**이 필요합니다.
2. **Docker Hub 계정**이 필요합니다.
3. **Azure CLI**가 설치되어 있어야 합니다.

## 1단계: Docker 이미지 빌드 및 푸시

### 1.1 Docker Hub 로그인

```bash
docker login
```

### 1.2 이미지 빌드 및 푸시

```bash
# 실행 권한 부여
chmod +x deploy.sh

# 배포 실행
./deploy.sh hadonas v1.0.0
```

## 2단계: Azure App Service 생성

### 2.1 리소스 그룹 생성

```bash
az group create --name ragQnaResourceGroup --location koreacentral
```

### 2.2 App Service Plan 생성

```bash
az appservice plan create \
  --name ragQnaServicePlan \
  --resource-group ragQnaResourceGroup \
  --sku B1 \
  --is-linux
```

### 2.3 Web App 생성 (Docker 컨테이너)

```bash
az webapp create \
  --resource-group ragQnaResourceGroup \
  --plan ragQnaServicePlan \
  --name rag-qna-service \
  --deployment-container-image-name hadonas/rag-qna-service:v1.0.0
```

## 3단계: 환경 변수 설정

### 3.1 필수 환경 변수 설정

```bash
# Azure OpenAI 설정
az webapp config appsettings set \
  --resource-group ragQnaResourceGroup \
  --name rag-qna-service \
  --settings AZURE_OPENAI_API_KEY="your-actual-api-key-here"

az webapp config appsettings set \
  --resource-group ragQnaResourceGroup \
  --name rag-qna-service \
  --settings AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"

az webapp config appsettings set \
  --resource-group ragQnaResourceGroup \
  --name rag-qna-service \
  --settings AZURE_OPENAI_API_VERSION="2025-01-01-preview"

# MongoDB 설정
az webapp config appsettings set \
  --resource-group ragQnaResourceGroup \
  --name rag-qna-service \
  --settings MONGODB_URI="mongodb+srv://username:password@cluster.mongodb.net/"

# 기타 설정
az webapp config appsettings set \
  --resource-group ragQnaResourceGroup \
  --name rag-qna-service \
  --settings MONGO_DB="insurance"

az webapp config appsettings set \
  --resource-group ragQnaResourceGroup \
  --name rag-qna-service \
  --settings MONGO_COLL="documents"

az webapp config appsettings set \
  --resource-group ragQnaResourceGroup \
  --name rag-qna-service \
  --settings AZURE_OPENAI_CHAT_DEPLOYMENT="gpt-4.1-mini"

az webapp config appsettings set \
  --resource-group ragQnaResourceGroup \
  --name rag-qna-service \
  --settings AZURE_OPENAI_EMB_DEPLOYMENT="text-embedding-3-small"

az webapp config appsettings set \
  --resource-group ragQnaResourceGroup \
  --name rag-qna-service \
  --settings MONGO_VECTOR_INDEX="vector_index"

az webapp config appsettings set \
  --resource-group ragQnaResourceGroup \
  --name rag-qna-service \
  --settings MONGO_TEXT_INDEX="text_index"
```

### 3.2 환경 변수 확인

```bash
az webapp config appsettings list \
  --resource-group ragQnaResourceGroup \
  --name rag-qna-service \
  --output table
```

## 4단계: 애플리케이션 테스트

### 4.1 서비스 상태 확인

```bash
# App Service URL 확인
az webapp show \
  --name rag-qna-service \
  --resource-group ragQnaResourceGroup \
  --query defaultHostName \
  --output tsv

# 헬스체크
curl https://rag-qna-service.azurewebsites.net/health
```

### 4.2 API 테스트

```bash
# QnA API 테스트
curl -X POST "https://rag-qna-service.azurewebsites.net/qna" \
  -H "Content-Type: application/json" \
  -d '{"input_message": "자동차보험료 계산 방법 알려줘"}'
```

## 5단계: 모니터링 및 로그

### 5.1 로그 스트림 확인

```bash
az webapp log tail \
  --name rag-qna-service \
  --resource-group ragQnaResourceGroup
```

### 5.2 로그 파일 다운로드

```bash
az webapp log download \
  --name rag-qna-service \
  --resource-group ragQnaResourceGroup
```

## 6단계: 자동 배포 설정 (선택사항)

### 6.1 GitHub Actions 설정

`.github/workflows/deploy.yml` 파일을 생성하여 자동 배포를 설정할 수 있습니다.

## 🔒 보안 고려사항

### 현재 방식의 위험성

1. **환경 변수 노출**: Azure Portal에서 환경 변수가 평문으로 표시됨
2. **접근 권한**: App Service에 접근할 수 있는 모든 사용자가 환경 변수 확인 가능
3. **감사 로그**: 환경 변수 변경 이력 추적 어려움

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

### 로그 확인

```bash
# 실시간 로그 확인
az webapp log tail \
  --name rag-qna-service \
  --resource-group ragQnaResourceGroup

# 로그 파일 다운로드
az webapp log download \
  --name rag-qna-service \
  --resource-group ragQnaResourceGroup
```

## 💰 비용 최적화

1. **App Service Plan**: 개발 환경에서는 B1, 프로덕션에서는 P1V2 이상 권장
2. **스케일링**: 트래픽에 따라 자동 스케일링 설정
3. **모니터링**: Application Insights를 통한 성능 모니터링

## 📝 다음 단계

보안을 강화하려면 다음을 고려하세요:

1. **Azure Key Vault 권한 요청**: 관리자에게 Key Vault 접근 권한 요청
2. **관리 ID 설정**: App Service에 관리 ID 활성화
3. **Key Vault 연동**: 환경 변수를 Key Vault에서 가져오도록 설정

## 🔄 업데이트 및 배포

### 새 버전 배포

```bash
# 새 태그로 이미지 빌드 및 푸시
./deploy.sh hadonas v1.1.0

# App Service 업데이트
az webapp config container set \
  --resource-group ragQnaResourceGroup \
  --name rag-qna-service \
  --docker-custom-image-name hadonas/rag-qna-service:v1.1.0
```

### 롤백

```bash
# 이전 버전으로 롤백
az webapp config container set \
  --resource-group ragQnaResourceGroup \
  --name rag-qna-service \
  --docker-custom-image-name hadonas/rag-qna-service:v1.0.0
```
