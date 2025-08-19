#!/bin/bash

# 배포 스크립트
# 사용법: ./deploy.sh [DOCKER_USERNAME] [IMAGE_TAG]

set -e

# 기본값 설정
DOCKER_USERNAME=${1:-"your-docker-username"}
IMAGE_TAG=${2:-"latest"}
IMAGE_NAME="ai-qa-service"

echo "🚀 AI Q&A Service 배포 시작..."

# Docker Hub 로그인 확인
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker가 실행되지 않았습니다. Docker를 시작해주세요."
    exit 1
fi

# Docker Hub 로그인 상태 확인
if ! docker system info | grep -q "Username"; then
    echo "⚠️  Docker Hub에 로그인되지 않았습니다."
    echo "docker login 명령어로 로그인해주세요."
    exit 1
fi

echo "📦 Docker 이미지 빌드 중..."
docker build -t ${DOCKER_USERNAME}/${IMAGE_NAME}:${IMAGE_TAG} .

if [ $? -eq 0 ]; then
    echo "✅ 이미지 빌드 성공!"
else
    echo "❌ 이미지 빌드 실패!"
    exit 1
fi

echo "🚀 Docker Hub에 푸시 중..."
docker push ${DOCKER_USERNAME}/${IMAGE_NAME}:${IMAGE_TAG}

if [ $? -eq 0 ]; then
    echo "✅ Docker Hub 푸시 성공!"
    echo ""
    echo "🎉 배포 완료!"
    echo "이미지: ${DOCKER_USERNAME}/${IMAGE_NAME}:${IMAGE_TAG}"
    echo ""
    echo "Azure App Services에서 다음 이미지를 사용하세요:"
    echo "Container Registry: ${DOCKER_USERNAME}/${IMAGE_NAME}"
    echo "Tag: ${IMAGE_TAG}"
else
    echo "❌ Docker Hub 푸시 실패!"
    exit 1
fi
