# Azure App Service 설정 가이드

이 가이드는 Azure App Service에서 RAG Q&A Service를 실행하기 위한 설정 방법을 설명합니다.

## 🚀 필수 환경변수 설정

Azure App Service의 **Configuration > Application settings**에서 다음 환경변수들을 설정해야 합니다:

### 1. Azure OpenAI 설정
```bash
AZURE_OPENAI_API_KEY=your-openai-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2025-01-01-preview
AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4.1-mini
AZURE_OPENAI_EMB_DEPLOYMENT=text-embedding-3-small
```

### 2. MongoDB 설정
```bash
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/database?retryWrites=true&w=majority
MONGO_DB=insurance
MONGO_COLL=documents
MONGO_VECTOR_INDEX=vector_index
MONGO_TEXT_INDEX=text_index
```

### 3. Azure Key Vault 설정 (선택사항)
```bash
AZURE_KEY_VAULT_URL=https://your-keyvault-name.vault.azure.net/
```

## 🔧 Azure App Service 설정

### 1. 플랫폼 설정
- **Operating System**: Linux
- **Runtime stack**: Docker
- **Region**: 가까운 지역 선택

### 2. 스케일링 설정
- **Plan type**: Basic 이상 (컨테이너 실행을 위해)
- **Size**: B1 이상 권장 (메모리 1GB 이상)

### 3. 네트워킹 설정
- **HTTPS Only**: Enabled
- **HTTP Version**: 2.0
- **Minimum TLS Version**: 1.2

## 🐳 Docker 컨테이너 설정

### 1. 컨테이너 이미지
- **Image source**: Docker Hub
- **Image and tag**: `index.docker.io/hadonas/rag-qna-service:latest`
- **Important**: `index.docker.io`를 명시적으로 포함해야 합니다!

### 2. 포트 설정
- **Port**: 8000 (Dockerfile에서 EXPOSE된 포트)

### 3. 환경변수 전달
모든 환경변수는 **Configuration > Application settings**에서 설정해야 합니다.

## 📊 모니터링 및 로깅

### 1. Application Insights 활성화
- **Application Insights**: Enabled
- **Connection string**: 자동 생성 또는 기존 사용

### 2. 로그 스트림 확인
- **Log stream**: 실시간 로그 확인 가능
- **Log level**: INFO 이상으로 설정

### 3. 헬스체크 엔드포인트
- **Root endpoint**: `https://your-app.azurewebsites.net/`
- **Health endpoint**: `https://your-app.azurewebsites.net/health`

## 🚨 문제 해결

### 1. Application Error 발생 시
1. **Log stream**에서 에러 로그 확인
2. **Environment variables** 설정 확인
3. **Container logs** 확인

### 2. 일반적인 문제들
- **MongoDB 연결 실패**: MONGODB_URI 확인
- **OpenAI API 오류**: API 키와 엔드포인트 확인
- **포트 바인딩 오류**: 포트 8000 설정 확인
- **이미지 풀 실패**: `index.docker.io` 포함 여부 확인

### 3. 디버깅 방법
```bash
# 로그 스트림 확인
az webapp log tail --name your-app-name --resource-group your-resource-group

# 환경변수 확인
az webapp config appsettings list --name your-app-name --resource-group your-resource-group

# 컨테이너 상태 확인
az webapp show --name your-app-name --resource-group your-resource-group
```

## 🔒 보안 고려사항

### 1. 환경변수 보안
- 민감한 정보는 **Application settings**에 저장
- Key Vault 사용 시 적절한 권한 설정

### 2. 네트워크 보안
- **HTTPS Only** 활성화
- 필요한 경우 **IP restrictions** 설정

### 3. 인증 및 권한
- Azure AD 인증 설정 (필요시)
- 적절한 RBAC 권한 설정

## 📈 성능 최적화

### 1. 스케일링
- **Auto scaling** 설정
- **Instance count** 조정

### 2. 캐싱
- **Redis Cache** 연동 (필요시)
- **CDN** 설정 (정적 파일용)

### 3. 모니터링
- **Application Insights** 대시보드 설정
- **Custom metrics** 설정

## 🚀 배포 후 확인사항

1. **Health endpoint** 접속 확인: `/health`
2. **Root endpoint** 접속 확인: `/`
3. **Log stream**에서 에러 메시지 확인
4. **Application Insights**에서 성능 메트릭 확인

## 📞 지원

문제가 지속되는 경우:
1. Azure Portal의 **Diagnose and solve problems** 사용
2. **Log stream**에서 상세 에러 로그 확인
3. Azure Support에 문의 (필요시)
