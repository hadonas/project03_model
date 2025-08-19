# Azure App Services 배포 가이드

이 가이드는 AI Q&A Service를 Azure App Services에 Docker 컨테이너로 배포하는 방법을 설명합니다.

## 사전 준비사항

1. **Azure 구독**이 필요합니다.
2. **Azure Key Vault**가 생성되어 있어야 합니다.
3. **Docker Hub 계정**이 필요합니다.
4. **Azure CLI**가 설치되어 있어야 합니다.

## 1단계: Azure Key Vault 설정

### 1.1 Key Vault 생성 (아직 생성하지 않은 경우)

```bash
# 리소스 그룹 생성
az group create --name myResourceGroup --location eastus

# Key Vault 생성
az keyvault create --name myKeyVault --resource-group myResourceGroup --location eastus

# Key Vault에 시크릿 추가
az keyvault secret set --vault-name myKeyVault --name "AZURE-OPENAI-API-KEY" --value "your-api-key"
az keyvault secret set --vault-name myKeyVault --name "AZURE-OPENAI-ENDPOINT" --value "https://your-resource.openai.azure.com/"
az keyvault secret set --vault-name myKeyVault --name "AZURE-OPENAI-API-VERSION" --value "2025-01-01-preview"
az keyvault secret set --vault-name myKeyVault --name "MONGODB-URI" --value "mongodb+srv://username:password@cluster.mongodb.net/"
```

### 1.2 App Service에 Key Vault 접근 권한 부여

```bash
# App Service의 관리 ID 활성화 (나중에 App Service 생성 후)
az webapp identity assign --name myAppService --resource-group myResourceGroup

# Key Vault 액세스 정책 설정
az keyvault set-policy --name myKeyVault --object-id <managed-identity-object-id> --secret-permissions get list
```

## 2단계: Docker 이미지 빌드 및 푸시

### 2.1 Docker Hub 로그인

```bash
docker login
```

### 2.2 이미지 빌드 및 푸시

```bash
# 배포 스크립트 실행
./deploy.sh your-docker-username v1.0.0

# 또는 수동으로 실행
docker build -t your-docker-username/ai-qa-service:v1.0.0 .
docker push your-docker-username/ai-qa-service:v1.0.0
```

## 3단계: Azure App Service 생성

### 3.1 App Service Plan 생성

```bash
az appservice plan create --name myAppServicePlan --resource-group myResourceGroup --sku B1 --is-linux
```

### 3.2 Web App 생성 (Docker 컨테이너)

```bash
az webapp create --resource-group myResourceGroup --plan myAppServicePlan --name myAppService --deployment-container-image-name your-docker-username/ai-qa-service:v1.0.0
```

### 3.3 환경 변수 설정

```bash
# Key Vault URL 설정
az webapp config appsettings set --resource-group myResourceGroup --name myAppService --settings AZURE_KEY_VAULT_URL="https://myKeyVault.vault.azure.net/"

# 기타 설정
az webapp config appsettings set --resource-group myResourceGroup --name myAppService --settings MONGO_DB="insurance"
az webapp config appsettings set --resource-group myResourceGroup --name myAppService --settings MONGO_COLL="documents"
az webapp config appsettings set --resource-group myResourceGroup --name myAppService --settings AZURE_OPENAI_CHAT_DEPLOYMENT="gpt-4.1-mini"
az webapp config appsettings set --resource-group myResourceGroup --name myAppService --settings AZURE_OPENAI_EMB_DEPLOYMENT="text-embedding-ada-002"
az webapp config appsettings set --resource-group myResourceGroup --name myAppService --settings MONGO_VECTOR_INDEX="vector_idx"
```

### 3.4 관리 ID 활성화 및 Key Vault 권한 부여

```bash
# 관리 ID 활성화
az webapp identity assign --name myAppService --resource-group myResourceGroup

# 관리 ID의 Object ID 가져오기
MANAGED_IDENTITY_OBJECT_ID=$(az webapp identity show --name myAppService --resource-group myResourceGroup --query principalId --output tsv)

# Key Vault 액세스 정책 설정
az keyvault set-policy --name myKeyVault --object-id $MANAGED_IDENTITY_OBJECT_ID --secret-permissions get list
```

## 4단계: 애플리케이션 테스트

### 4.1 서비스 상태 확인

```bash
# App Service URL 확인
az webapp show --name myAppService --resource-group myResourceGroup --query defaultHostName --output tsv

# 헬스체크
curl https://myAppService.azurewebsites.net/health
```

### 4.2 API 테스트

```bash
# QnA API 테스트
curl -X POST "https://myAppService.azurewebsites.net/qna" \
  -H "Content-Type: application/json" \
  -d '{"input_message": "자동차보험료 계산 방법 알려줘"}'
```

## 5단계: 모니터링 및 로그

### 5.1 로그 스트림 확인

```bash
az webapp log tail --name myAppService --resource-group myResourceGroup
```

### 5.2 Application Insights 설정 (선택사항)

```bash
# Application Insights 생성
az monitor app-insights component create --app myAppInsights --location eastus --resource-group myResourceGroup --application-type web

# App Service에 연결
az webapp config appsettings set --resource-group myResourceGroup --name myAppService --settings APPINSIGHTS_INSTRUMENTATIONKEY="<instrumentation-key>"
```

## 6단계: 자동 배포 설정 (선택사항)

### 6.1 GitHub Actions 설정

`.github/workflows/deploy.yml` 파일을 생성하여 자동 배포를 설정할 수 있습니다.

## 문제 해결

### 일반적인 문제들

1. **Key Vault 접근 권한 오류**
   - 관리 ID가 올바르게 설정되었는지 확인
   - Key Vault 액세스 정책이 올바르게 설정되었는지 확인

2. **MongoDB 연결 오류**
   - MongoDB Atlas의 IP 화이트리스트에 Azure App Service IP 추가
   - 연결 문자열이 올바른지 확인

3. **Azure OpenAI API 오류**
   - API 키가 올바른지 확인
   - 배포명이 올바른지 확인
   - 리소스 지역이 올바른지 확인

### 로그 확인

```bash
# 실시간 로그 확인
az webapp log tail --name myAppService --resource-group myResourceGroup

# 로그 파일 다운로드
az webapp log download --name myAppService --resource-group myResourceGroup
```

## 비용 최적화

1. **App Service Plan**: 개발 환경에서는 B1, 프로덕션에서는 P1V2 이상 권장
2. **스케일링**: 트래픽에 따라 자동 스케일링 설정
3. **모니터링**: Application Insights를 통한 성능 모니터링

## 보안 고려사항

1. **HTTPS 강제**: HTTP에서 HTTPS로 리다이렉트 설정
2. **IP 제한**: 필요한 경우 특정 IP에서만 접근 허용
3. **Key Vault**: 민감한 정보는 항상 Key Vault에 저장
4. **관리 ID**: 서비스 주체 대신 관리 ID 사용 권장
