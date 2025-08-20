@echo off
REM Azure CLI를 통한 수동 배포 스크립트 (Windows)
REM 사용법: deploy-manual.bat

setlocal enabledelayedexpansion

echo 🚀 Azure App Service 수동 배포 시작 (Windows)
echo.

REM 환경 변수 확인
echo 🔍 환경 변수 확인 중...
set missing_vars=

if "%AZURE_OPENAI_API_KEY%"=="" set missing_vars=!missing_vars! AZURE_OPENAI_API_KEY
if "%AZURE_OPENAI_ENDPOINT%"=="" set missing_vars=!missing_vars! AZURE_OPENAI_ENDPOINT
if "%MONGODB_URI%"=="" set missing_vars=!missing_vars! MONGODB_URI
if "%AZURE_WEBAPP_NAME%"=="" set missing_vars=!missing_vars! AZURE_WEBAPP_NAME
if "%AZURE_RESOURCE_GROUP%"=="" set missing_vars=!missing_vars! AZURE_RESOURCE_GROUP
if "%AZURE_SUBSCRIPTION_ID%"=="" set missing_vars=!missing_vars! AZURE_SUBSCRIPTION_ID

if not "!missing_vars!"=="" (
    echo ❌ 다음 환경 변수가 설정되지 않았습니다:!missing_vars!
    echo.
    echo 다음 방법으로 설정하세요:
    echo 1. .env 파일 생성
    echo 2. set 명령어 사용
    echo 3. 시스템 환경 변수 설정
    pause
    exit /b 1
)

echo ✅ 모든 필수 환경 변수가 설정되었습니다
echo.

REM Azure CLI 로그인 확인
echo 🔐 Azure CLI 로그인 상태 확인 중...
az account show >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Azure CLI에 로그인되지 않았습니다.
    echo 로그인을 진행합니다...
    az login
    if errorlevel 1 (
        echo ❌ Azure 로그인에 실패했습니다.
        pause
        exit /b 1
    )
)

echo ✅ Azure CLI 로그인 완료
echo.

REM 구독 설정
echo 📋 구독 설정 중: %AZURE_SUBSCRIPTION_ID%
az account set --subscription "%AZURE_SUBSCRIPTION_ID%"

REM 현재 구독 정보 출력
echo 현재 구독 정보:
az account show --query "{name:name, id:id, tenantId:tenantId}" --output table
echo.

REM App Service 환경 변수 설정
echo ⚙️  App Service 환경 변수 설정 중...
az webapp config appsettings set ^
    --resource-group "%AZURE_RESOURCE_GROUP%" ^
    --name "%AZURE_WEBAPP_NAME%" ^
    --settings ^
        AZURE_OPENAI_API_KEY="%AZURE_OPENAI_API_KEY%" ^
        AZURE_OPENAI_ENDPOINT="%AZURE_OPENAI_ENDPOINT%" ^
        AZURE_OPENAI_API_VERSION="%AZURE_OPENAI_API_VERSION%" ^
        MONGODB_URI="%MONGODB_URI%" ^
        MONGO_DB="%MONGO_DB%" ^
        MONGO_COLL="%MONGO_COLL%" ^
        AZURE_OPENAI_CHAT_DEPLOYMENT="%AZURE_OPENAI_CHAT_DEPLOYMENT%" ^
        AZURE_OPENAI_EMB_DEPLOYMENT="%AZURE_OPENAI_EMB_DEPLOYMENT%" ^
        MONGO_VECTOR_INDEX="%MONGO_VECTOR_INDEX%" ^
        MONGO_TEXT_INDEX="%MONGO_TEXT_INDEX%"

if errorlevel 1 (
    echo ❌ 환경 변수 설정 실패
    pause
    exit /b 1
)

echo ✅ 환경 변수 설정 완료
echo.

REM Docker 이미지 업데이트
echo 🐳 Docker 이미지 업데이트 중...
echo Docker Hub에서 이미지를 가져오는 중...
docker pull hadonas/rag-qna-service:latest

if errorlevel 1 (
    echo ⚠️  Docker Hub에서 이미지를 가져올 수 없습니다.
    echo 로컬에서 빌드하시겠습니까? (y/n)
    set /p response=
    if /i "!response!"=="y" (
        echo 로컬에서 Docker 이미지 빌드 중...
        docker build -t hadonas/rag-qna-service:latest .
    ) else (
        echo 이미지 업데이트를 건너뜁니다.
        goto :skip_image_update
    )
)

REM App Service에서 Docker 이미지 사용하도록 설정
az webapp config container set ^
    --resource-group "%AZURE_RESOURCE_GROUP%" ^
    --name "%AZURE_WEBAPP_NAME%" ^
    --docker-custom-image-name hadonas/rag-qna-service:latest

if errorlevel 1 (
    echo ❌ Docker 이미지 업데이트 실패
    pause
    exit /b 1
)

echo ✅ Docker 이미지 업데이트 완료
echo.

:skip_image_update

REM App Service 재시작
echo 🔄 App Service 재시작 중...
az webapp restart ^
    --resource-group "%AZURE_RESOURCE_GROUP%" ^
    --name "%AZURE_WEBAPP_NAME%"

if errorlevel 1 (
    echo ❌ App Service 재시작 실패
    pause
    exit /b 1
)

echo ✅ App Service 재시작 완료
echo.

REM 헬스체크
echo 🏥 헬스체크 시작...
set APP_URL=https://%AZURE_WEBAPP_NAME%.azurewebsites.net
echo 앱 URL: !APP_URL!
echo.

REM 재시작 후 대기
echo 앱이 시작될 때까지 대기 중... (30초)
timeout /t 30 /nobreak >nul

REM 헬스체크 시도
echo 헬스체크 시도 중...
for /l %%i in (1,1,5) do (
    echo 시도 %%i/5...
    curl -f "!APP_URL!/health" >nul 2>&1
    if not errorlevel 1 (
        echo ✅ 앱이 정상적으로 실행되고 있습니다!
        echo 헬스체크 URL: !APP_URL!/health
        echo 메인 API URL: !APP_URL!/docs
        goto :success
    ) else (
        if %%i lss 5 (
            echo ⏳ 시도 %%i: 앱이 아직 준비되지 않았습니다.
            echo 10초 후 재시도...
            timeout /t 10 /nobreak >nul
        )
    )
)

echo ❌ 헬스체크 실패. 앱이 정상적으로 시작되지 않았습니다.
echo Azure Portal에서 App Service 상태를 확인해주세요.
pause
exit /b 1

:success
echo.
echo 🎉 배포가 완료되었습니다!
echo Azure Portal에서 App Service 상태를 확인할 수 있습니다.
echo.
pause
