# Azure Key Vault와 CI/CD 통합 가이드

이 가이드는 Azure Key Vault를 활용하여 CI/CD 파이프라인에서 보안을 강화하는 방법을 설명합니다.

## 🚀 개요

Azure Key Vault를 CI/CD 파이프라인과 통합하여:
- 민감한 정보를 안전하게 관리
- 환경별 설정값 자동 로드
- 보안 강화된 자동 배포

## 📋 사전 준비사항

1. **Azure 구독**이 필요합니다
2. **Azure Key Vault**가 생성되어 있어야 합니다
3. **GitHub Actions**가 설정되어 있어야 합니다
4. **Azure CLI**가 설치되어 있어야 합니다

## 1단계: Azure Key Vault 설정

### 1.1 Key Vault 생성

```bash
# 리소스 그룹 생성 (아직 없는 경우)
az group create --name ragQnaResourceGroup --location koreacentral

# Key Vault 생성
az keyvault create \
  --name ragQnaKeyVault \
  --resource-group ragQnaResourceGroup \
  --location koreacentral \
  --sku standard \
  --enable-rbac-authorization true
```

### 1.2 시크릿 추가

```bash
# Azure OpenAI 설정
az keyvault secret set \
  --vault-name ragQnaKeyVault \
  --name "AZURE-OPENAI-API-KEY" \
  --value "your-actual-api-key"

az keyvault secret set \
  --vault-name ragQnaKeyVault \
  --name "AZURE-OPENAI-ENDPOINT" \
  --value "https://your-resource.openai.azure.com/"

az keyvault secret set \
  --vault-name ragQnaKeyVault \
  --name "AZURE-OPENAI-API-VERSION" \
  --value "2025-01-01-preview"

# MongoDB 설정
az keyvault secret set \
  --vault-name ragQnaKeyVault \
  --name "MONGODB-URI" \
  --value "mongodb+srv://username:password@cluster.mongodb.net/"

# 기타 설정
az keyvault secret set \
  --vault-name ragQnaKeyVault \
  --name "MONGO-DB" \
  --value "insurance"

az keyvault secret set \
  --vault-name ragQnaKeyVault \
  --name "MONGO-COLL" \
  --value "documents"

az keyvault secret set \
  --vault-name ragQnaKeyVault \
  --name "AZURE-OPENAI-CHAT-DEPLOYMENT" \
  --value "gpt-4.1-mini"

az keyvault secret set \
  --vault-name ragQnaKeyVault \
  --name "AZURE-OPENAI-EMB-DEPLOYMENT" \
  --value "text-embedding-3-small"

az keyvault secret set \
  --vault-name ragQnaKeyVault \
  --name "MONGO-VECTOR-INDEX" \
  --value "vector_index"

az keyvault secret set \
  --vault-name ragQnaKeyVault \
  --name "MONGO-TEXT-INDEX" \
  --value "text_index"
```

## 2단계: Azure App Service 관리 ID 설정

### 2.1 App Service 생성 (아직 없는 경우)

```bash
# App Service Plan 생성
az appservice plan create \
  --name ragQnaServicePlan \
  --resource-group ragQnaResourceGroup \
  --sku B1 \
  --is-linux

# Web App 생성
az webapp create \
  --resource-group ragQnaResourceGroup \
  --plan ragQnaServicePlan \
  --name rag-qna-service \
  --deployment-container-image-name hadonas/rag-qna-service:latest
```

### 2.2 관리 ID 활성화

```bash
# 관리 ID 활성화
az webapp identity assign \
  --name rag-qna-service \
  --resource-group ragQnaResourceGroup

# 관리 ID의 Object ID 가져오기
MANAGED_IDENTITY_OBJECT_ID=$(az webapp identity show \
  --name rag-qna-service \
  --resource-group ragQnaResourceGroup \
  --query principalId --output tsv)

echo "Managed Identity Object ID: $MANAGED_IDENTITY_OBJECT_ID"
```

### 2.3 Key Vault 접근 권한 부여

```bash
# Key Vault에 App Service의 관리 ID 접근 권한 부여
az keyvault set-policy \
  --name ragQnaKeyVault \
  --object-id $MANAGED_IDENTITY_OBJECT_ID \
  --secret-permissions get list
```

## 3단계: GitHub Actions에 Azure 인증 추가

### 3.1 Azure Service Principal 생성

```bash
# Service Principal 생성
az ad sp create-for-rbac \
  --name "github-actions-rag-qna" \
  --role contributor \
  --scopes /subscriptions/your-subscription-id/resourceGroups/ragQnaResourceGroup \
  --sdk-auth

# 출력된 JSON을 GitHub Secrets에 저장
```

### 3.2 GitHub Secrets 설정

GitHub 저장소의 **Settings > Secrets and variables > Actions**에서 다음 secrets를 추가하세요:

```bash
# Azure 인증 정보
AZURE_CREDENTIALS=위에서_생성된_JSON_내용

# Key Vault URL
AZURE_KEY_VAULT_URL=https://ragQnaKeyVault.vault.azure.net/

# App Service 정보
AZURE_WEBAPP_NAME=rag-qna-service
AZURE_RESOURCE_GROUP=ragQnaResourceGroup
```

## 4단계: GitHub Actions 워크플로우 업데이트

### 4.1 Azure 인증 단계 추가

`.github/workflows/deploy.yml` 파일에 Azure 인증 단계를 추가하세요:

```yaml
- name: Azure Login
  uses: azure/login@v1
  with:
    creds: ${{ secrets.AZURE_CREDENTIALS }}

- name: Set Key Vault URL
  run: |
    echo "AZURE_KEY_VAULT_URL=${{ secrets.AZURE_KEY_VAULT_URL }}" >> $GITHUB_ENV
```

### 4.2 환경 변수 설정 단계 추가

```yaml
- name: Set App Service Environment Variables
  run: |
    # Key Vault에서 시크릿 가져오기
    az keyvault secret show --vault-name ragQnaKeyVault --name "AZURE-OPENAI-API-KEY" --query value -o tsv | \
    az webapp config appsettings set \
      --resource-group ${{ secrets.AZURE_RESOURCE_GROUP }} \
      --name ${{ secrets.AZURE_WEBAPP_NAME }} \
      --settings AZURE_OPENAI_API_KEY="@-"
    
    # 다른 시크릿들도 동일하게 설정
    # ... (모든 필요한 환경 변수 설정)
```

## 5단계: 환경별 설정 관리

### 5.1 스테이징 환경 설정

```bash
# 스테이징용 App Service 생성
az webapp create \
  --resource-group ragQnaResourceGroup \
  --plan ragQnaServicePlan \
  --name rag-qna-service-staging \
  --deployment-container-image-name hadonas/rag-qna-service:latest

# 스테이징용 관리 ID 설정
az webapp identity assign \
  --name rag-qna-service-staging \
  --resource-group ragQnaResourceGroup

# 스테이징용 Key Vault 권한 설정
STAGING_MANAGED_ID=$(az webapp identity show \
  --name rag-qna-service-staging \
  --resource-group ragQnaResourceGroup \
  --query principalId --output tsv)

az keyvault set-policy \
  --name ragQnaKeyVault \
  --object-id $STAGING_MANAGED_ID \
  --secret-permissions get list
```

### 5.2 환경별 시크릿 관리

```bash
# 환경별 시크릿 생성 (필요한 경우)
az keyvault secret set \
  --vault-name ragQnaKeyVault \
  --name "STAGING-MONGO-DB" \
  --value "insurance-staging"

az keyvault secret set \
  --vault-name ragQnaKeyVault \
  --name "PRODUCTION-MONGO-DB" \
  --value "insurance-production"
```

## 6단계: CI/CD 파이프라인 테스트

### 6.1 워크플로우 실행 테스트

1. `develop` 브랜치에 코드 푸시
2. GitHub Actions에서 Azure 인증 및 Key Vault 접근 확인
3. 환경 변수 설정 단계 성공 확인

### 6.2 배포 테스트

1. 스테이징 환경 배포 확인
2. 프로덕션 환경 배포 확인
3. Key Vault에서 환경 변수 로드 확인

## 🔒 보안 고려사항

### 7.1 접근 권한 최소화

```bash
# 필요한 최소 권한만 부여
az keyvault set-policy \
  --name ragQnaKeyVault \
  --object-id $MANAGED_IDENTITY_OBJECT_ID \
  --secret-permissions get list \
  --certificate-permissions get list \
  --key-permissions get list
```

### 7.2 네트워크 보안

```bash
# Key Vault 방화벽 설정 (필요한 경우)
az keyvault network-rule add \
  --name ragQnaKeyVault \
  --resource-group ragQnaResourceGroup \
  --subnet /subscriptions/your-subscription-id/resourceGroups/your-vnet-rg/providers/Microsoft.Network/virtualNetworks/your-vnet/subnets/your-subnet
```

### 7.3 감사 및 모니터링

```bash
# Key Vault 진단 설정
az monitor diagnostic-settings create \
  --resource /subscriptions/your-subscription-id/resourceGroups/ragQnaResourceGroup/providers/Microsoft.KeyVault/vaults/ragQnaKeyVault \
  --name keyvault-diagnostics \
  --storage-account your-storage-account-id \
  --logs '[{"category": "AuditEvent", "enabled": true}]'
```

## 🚨 문제 해결

### 일반적인 문제들

1. **Key Vault 접근 권한 오류**
   - 관리 ID가 올바르게 설정되었는지 확인
   - Key Vault 액세스 정책이 올바르게 설정되었는지 확인

2. **GitHub Actions Azure 인증 오류**
   - `AZURE_CREDENTIALS` secret이 올바른지 확인
   - Service Principal에 적절한 권한이 부여되었는지 확인

3. **환경 변수 설정 실패**
   - App Service 이름과 리소스 그룹이 올바른지 확인
   - Key Vault 시크릿 이름이 올바른지 확인

### 로그 확인

```bash
# App Service 로그 확인
az webapp log tail \
  --name rag-qna-service \
  --resource-group ragQnaResourceGroup

# Key Vault 감사 로그 확인
az monitor activity-log list \
  --resource-id /subscriptions/your-subscription-id/resourceGroups/ragQnaResourceGroup/providers/Microsoft.KeyVault/vaults/ragQnaKeyVault
```

## 📊 모니터링 및 알림

### 8.1 Key Vault 모니터링

- **Azure Monitor**: Key Vault 메트릭 및 로그 수집
- **Application Insights**: App Service 성능 모니터링
- **Log Analytics**: 중앙화된 로그 분석

### 8.2 알림 설정

```bash
# Key Vault 비정상 접근 알림 설정
az monitor metrics alert create \
  --name "keyvault-access-alert" \
  --resource-group ragQnaResourceGroup \
  --scopes /subscriptions/your-subscription-id/resourceGroups/ragQnaResourceGroup/providers/Microsoft.KeyVault/vaults/ragQnaKeyVault \
  --condition "total requests > 1000" \
  --description "Key Vault 접근 횟수 증가 알림"
```

## 📝 다음 단계

Key Vault와 CI/CD 통합이 완료된 후:

1. **자동화된 보안 스캔**: 코드 보안 취약점 자동 검사
2. **시크릿 순환**: 정기적인 API 키 및 토큰 갱신
3. **백업 및 복구**: Key Vault 데이터 백업 전략 수립
4. **규정 준수**: SOC, PCI DSS 등 규정 준수 모니터링
