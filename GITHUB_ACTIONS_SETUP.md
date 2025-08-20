# GitHub Actions CI/CD 설정 가이드

이 가이드는 RAG Q&A Service를 위한 GitHub Actions CI/CD 파이프라인 설정 방법을 설명합니다.

## 🚀 개요

GitHub Actions를 통해 다음과 같은 자동화를 구현합니다:
- 코드 품질 검사 (테스트, 린팅)
- Docker 이미지 빌드 및 Docker Hub 푸시
- Azure App Service 자동 배포 (스테이징/프로덕션)

## 📋 사전 준비사항

1. **GitHub 저장소**가 설정되어 있어야 합니다
2. **Docker Hub 계정**이 필요합니다
3. **Azure App Service**가 생성되어 있어야 합니다
4. **Azure CLI**가 설치되어 있어야 합니다

## 1단계: GitHub Secrets 설정

### 1.1 Docker Hub Secrets

GitHub 저장소의 **Settings > Secrets and variables > Actions**에서 다음 secrets를 추가하세요:

```bash
DOCKER_USERNAME=your-docker-hub-username
DOCKER_PASSWORD=your-docker-hub-access-token
```

**Docker Hub Access Token 생성 방법:**
1. Docker Hub에 로그인
2. Account Settings > Security > New Access Token
3. 토큰 이름 입력 (예: "github-actions")
4. 토큰 생성 후 복사하여 GitHub Secrets에 저장

### 1.2 Azure App Service Publish Profile

Azure App Service에서 publish profile을 다운로드하여 GitHub Secrets에 추가하세요:

```bash
# 프로덕션 환경
AZURE_WEBAPP_PUBLISH_PROFILE=your-production-publish-profile-content

# 스테이징 환경 (선택사항)
AZURE_WEBAPP_PUBLISH_PROFILE_STAGING=your-staging-publish-profile-content
```

**Publish Profile 다운로드 방법:**
1. Azure Portal에서 App Service로 이동
2. **Get publish profile** 클릭
3. 다운로드된 파일 내용을 복사하여 GitHub Secrets에 저장

## 2단계: GitHub Environments 설정

### 2.1 Staging Environment

1. GitHub 저장소의 **Settings > Environments**에서 **New environment** 클릭
2. Environment name: `staging`
3. **Protection rules** 설정 (선택사항):
   - **Required reviewers**: 코드 리뷰어 지정
   - **Wait timer**: 자동 배포 전 대기 시간 설정

### 2.2 Production Environment

1. **New environment** 클릭
2. Environment name: `production`
3. **Protection rules** 설정 (권장):
   - **Required reviewers**: 반드시 승인해야 하는 리뷰어 지정
   - **Wait timer**: 5분 이상 설정 권장
   - **Deployment branches**: `main` 브랜치만 허용

## 3단계: 브랜치 전략 설정

### 3.1 브랜치 보호 규칙

**Settings > Branches**에서 main 브랜치 보호 규칙을 설정하세요:

```bash
# main 브랜치 보호 규칙
✓ Require a pull request before merging
✓ Require approvals (최소 1명 이상)
✓ Require status checks to pass before merging
✓ Require branches to be up to date before merging
✓ Include administrators
```

### 3.2 브랜치 전략

```bash
main          # 프로덕션 배포 (자동)
├── develop   # 스테이징 배포 (자동)
└── feature/* # 기능 개발 브랜치
```

## 4단계: 워크플로우 파일 배치

`.github/workflows/deploy.yml` 파일이 저장소에 있는지 확인하세요.

## 5단계: CI/CD 파이프라인 테스트

### 5.1 첫 번째 배포 테스트

1. `develop` 브랜치에 코드 푸시:
```bash
git checkout -b develop
git add .
git commit -m "Initial CI/CD setup"
git push origin develop
```

2. GitHub Actions 탭에서 워크플로우 실행 확인

### 5.2 프로덕션 배포 테스트

1. `develop`에서 `main`으로 Pull Request 생성
2. 코드 리뷰 및 승인
3. `main` 브랜치로 머지
4. 자동 배포 확인

## 🔧 워크플로우 커스터마이징

### 6.1 환경별 배포 조건 수정

```yaml
# 스테이징 배포 조건
if: github.ref == 'refs/heads/develop' || github.event.inputs.environment == 'staging'

# 프로덕션 배포 조건
if: github.ref == 'refs/heads/main' || github.event.inputs.environment == 'production'
```

### 6.2 수동 배포 트리거

GitHub 저장소의 **Actions** 탭에서 **Run workflow** 버튼을 클릭하여 수동으로 배포할 수 있습니다.

## 🚨 문제 해결

### 일반적인 문제들

1. **Docker Hub 로그인 실패**
   - `DOCKER_USERNAME`과 `DOCKER_PASSWORD` secrets 확인
   - Docker Hub Access Token이 올바른지 확인

2. **Azure 배포 실패**
   - `AZURE_WEBAPP_PUBLISH_PROFILE` secret 확인
   - App Service 이름이 올바른지 확인
   - Azure 구독 권한 확인

3. **환경 보호 규칙 오류**
   - Environment 설정에서 protection rules 확인
   - Required reviewers가 올바르게 설정되었는지 확인

### 로그 확인

GitHub Actions 탭에서 각 job의 로그를 확인하여 문제를 진단할 수 있습니다.

## 📊 모니터링

### 7.1 워크플로우 상태 모니터링

- **GitHub Actions 탭**: 모든 워크플로우 실행 상태 확인
- **Environments 탭**: 각 환경의 배포 상태 확인
- **Notifications**: 워크플로우 실패 시 알림 설정

### 7.2 성능 최적화

- **Docker Layer Caching**: `cache-from`과 `cache-to` 사용
- **Parallel Jobs**: 독립적인 job들을 병렬로 실행
- **Conditional Steps**: 필요한 경우에만 특정 단계 실행

## 🔒 보안 고려사항

1. **Secrets 관리**: 민감한 정보는 반드시 GitHub Secrets에 저장
2. **브랜치 보호**: main 브랜치에 대한 보호 규칙 필수
3. **환경 보호**: 프로덕션 환경에 대한 승인 절차 필수
4. **토큰 순환**: Docker Hub Access Token을 정기적으로 갱신

## 📝 다음 단계

CI/CD 파이프라인이 설정된 후:

1. **자동화 테스트**: 새로운 기능 추가 시 자동 테스트 실행
2. **배포 전략**: Blue-Green 배포, Canary 배포 등 고급 전략 고려
3. **모니터링**: Application Insights, 로그 분석 등 추가 모니터링 설정
4. **보안 스캔**: 코드 보안 취약점 자동 스캔 추가
