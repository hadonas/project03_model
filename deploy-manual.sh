#!/bin/bash

# Azure CLI를 통한 수동 배포 스크립트
# 사용법: ./deploy-manual.sh

set -e

echo "🚀 Azure App Service 수동 배포 시작"

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 환경 변수 확인
check_env_vars() {
    echo "🔍 환경 변수 확인 중..."
    
    required_vars=(
        "AZURE_OPENAI_API_KEY"
        "AZURE_OPENAI_ENDPOINT"
        "MONGODB_URI"
        "AZURE_WEBAPP_NAME"
        "AZURE_RESOURCE_GROUP"
        "AZURE_SUBSCRIPTION_ID"
    )
    
    missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        echo -e "${RED}❌ 다음 환경 변수가 설정되지 않았습니다:${NC}"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        echo ""
        echo "다음 방법으로 설정하세요:"
        echo "1. .env 파일 생성"
        echo "2. export 명령어 사용"
        echo "3. 스크립트 실행 전에 설정"
        exit 1
    fi
    
    echo -e "${GREEN}✅ 모든 필수 환경 변수가 설정되었습니다${NC}"
}

# Azure CLI 로그인 확인
check_azure_login() {
    echo "🔐 Azure CLI 로그인 상태 확인 중..."
    
    if ! az account show > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Azure CLI에 로그인되지 않았습니다.${NC}"
        echo "로그인을 진행합니다..."
        az login
        
        if [ $? -ne 0 ]; then
            echo -e "${RED}❌ Azure 로그인에 실패했습니다.${NC}"
            exit 1
        fi
    fi
    
    echo -e "${GREEN}✅ Azure CLI 로그인 완료${NC}"
    
    # 구독 설정
    echo "📋 구독 설정 중: $AZURE_SUBSCRIPTION_ID"
    az account set --subscription "$AZURE_SUBSCRIPTION_ID"
    
    # 현재 구독 정보 출력
    echo "현재 구독 정보:"
    az account show --query "{name:name, id:id, tenantId:tenantId}" --output table
}

# App Service 환경 변수 설정
update_app_settings() {
    echo "⚙️  App Service 환경 변수 설정 중..."
    
    az webapp config appsettings set \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --name "$AZURE_WEBAPP_NAME" \
        --settings \
            AZURE_OPENAI_API_KEY="$AZURE_OPENAI_API_KEY" \
            AZURE_OPENAI_ENDPOINT="$AZURE_OPENAI_ENDPOINT" \
            AZURE_OPENAI_API_VERSION="${AZURE_OPENAI_API_VERSION:-2025-01-01-preview}" \
            MONGODB_URI="$MONGODB_URI" \
            MONGO_DB="${MONGO_DB:-insurance}" \
            MONGO_COLL="${MONGO_COLL:-documents}" \
            AZURE_OPENAI_CHAT_DEPLOYMENT="${AZURE_OPENAI_CHAT_DEPLOYMENT:-gpt-4.1-mini}" \
            AZURE_OPENAI_EMB_DEPLOYMENT="${AZURE_OPENAI_EMB_DEPLOYMENT:-text-embedding-3-small}" \
            MONGO_VECTOR_INDEX="${MONGO_VECTOR_INDEX:-vector_index}" \
            MONGO_TEXT_INDEX="${MONGO_TEXT_INDEX:-text_index}"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 환경 변수 설정 완료${NC}"
    else
        echo -e "${RED}❌ 환경 변수 설정 실패${NC}"
        exit 1
    fi
}

# Docker 이미지 업데이트
update_docker_image() {
    echo "🐳 Docker 이미지 업데이트 중..."
    
    # Docker Hub에서 최신 이미지 가져오기
    echo "Docker Hub에서 이미지 가져오는 중..."
    docker pull hadonas/rag-qna-service:latest
    
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}⚠️  Docker Hub에서 이미지를 가져올 수 없습니다.${NC}"
        echo "로컬에서 빌드하시겠습니까? (y/n)"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            echo "로컬에서 Docker 이미지 빌드 중..."
            docker build -t hadonas/rag-qna-service:latest .
        else
            echo "이미지 업데이트를 건너뜁니다."
            return 0
        fi
    fi
    
    # App Service에서 Docker 이미지 사용하도록 설정
    az webapp config container set \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --name "$AZURE_WEBAPP_NAME" \
        --docker-custom-image-name hadonas/rag-qna-service:latest
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Docker 이미지 업데이트 완료${NC}"
    else
        echo -e "${RED}❌ Docker 이미지 업데이트 실패${NC}"
        exit 1
    fi
}

# App Service 재시작
restart_app_service() {
    echo "🔄 App Service 재시작 중..."
    
    az webapp restart \
        --resource-group "$AZURE_RESOURCE_GROUP" \
        --name "$AZURE_WEBAPP_NAME"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ App Service 재시작 완료${NC}"
    else
        echo -e "${RED}❌ App Service 재시작 실패${NC}"
        exit 1
    fi
}

# 헬스체크
health_check() {
    echo "🏥 헬스체크 시작..."
    
    # App Service URL 구성
    APP_URL="https://$AZURE_WEBAPP_NAME.azurewebsites.net"
    echo "앱 URL: $APP_URL"
    
    # 재시작 후 대기
    echo "앱이 시작될 때까지 대기 중... (30초)"
    sleep 30
    
    # 헬스체크 시도
    echo "헬스체크 시도 중..."
    for i in {1..5}; do
        echo "시도 $i/5..."
        
        if curl -f "$APP_URL/health" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ 앱이 정상적으로 실행되고 있습니다!${NC}"
            echo "헬스체크 URL: $APP_URL/health"
            echo "메인 API URL: $APP_URL/docs"
            return 0
        else
            echo -e "${YELLOW}⏳ 시도 $i: 앱이 아직 준비되지 않았습니다.${NC}"
            if [ $i -lt 5 ]; then
                echo "10초 후 재시도..."
                sleep 10
            fi
        fi
    done
    
    echo -e "${RED}❌ 헬스체크 실패. 앱이 정상적으로 시작되지 않았습니다.${NC}"
    echo "Azure Portal에서 App Service 상태를 확인해주세요."
    return 1
}

# 메인 실행
main() {
    echo "=================================="
    echo "Azure App Service 수동 배포 스크립트"
    echo "=================================="
    echo ""
    
    # 환경 변수 확인
    check_env_vars
    
    # Azure CLI 로그인 확인
    check_azure_login
    
    # App Service 환경 변수 설정
    update_app_settings
    
    # Docker 이미지 업데이트
    update_docker_image
    
    # App Service 재시작
    restart_app_service
    
    # 헬스체크
    health_check
    
    echo ""
    echo -e "${GREEN}🎉 배포가 완료되었습니다!${NC}"
    echo "Azure Portal에서 App Service 상태를 확인할 수 있습니다."
}

# 스크립트 실행
main "$@"
