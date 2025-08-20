#!/usr/bin/env python3
"""
로컬 환경에서 애플리케이션을 테스트하는 스크립트
"""

import requests
import time
import sys
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

def test_health_endpoint(base_url="http://localhost:8000"):
    """헬스체크 엔드포인트 테스트"""
    try:
        print("🔍 Testing health endpoint...")
        response = requests.get(f"{base_url}/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check successful: {data}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Health check error: {e}")
        return False

def test_root_endpoint(base_url="http://localhost:8000"):
    """루트 엔드포인트 테스트"""
    try:
        print("🔍 Testing root endpoint...")
        response = requests.get(f"{base_url}/", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Root endpoint successful: {data}")
            return True
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Root endpoint error: {e}")
        return False

def test_qna_endpoint(base_url="http://localhost:8000"):
    """QnA 엔드포인트 테스트"""
    try:
        print("🔍 Testing QnA endpoint...")
        
        # 간단한 테스트 질문
        test_data = {
            "input_message": "테스트 질문입니다."
        }
        
        response = requests.post(f"{base_url}/qna", json=test_data, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ QnA endpoint successful: {data}")
            return True
        else:
            print(f"❌ QnA endpoint failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ QnA endpoint error: {e}")
        return False

def check_environment_variables():
    """필수 환경변수 확인"""
    print("🔍 Checking environment variables...")
    
    required_vars = [
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "MONGODB_URI"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
        else:
            print(f"✅ {var}: {'*' * 10}")  # 값은 마스킹
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    else:
        print("✅ All required environment variables are set")
        return False

def main():
    """메인 테스트 함수"""
    print("🚀 Starting local application test...")
    print("=" * 50)
    
    # 환경변수 확인
    env_ok = check_environment_variables()
    
    # 애플리케이션이 실행 중인지 확인
    print("\n🔍 Checking if application is running...")
    
    # 헬스체크 테스트
    health_ok = test_health_endpoint()
    
    if health_ok:
        print("\n✅ Application is running and healthy!")
        
        # 루트 엔드포인트 테스트
        root_ok = test_root_endpoint()
        
        # QnA 엔드포인트 테스트
        qna_ok = test_qna_endpoint()
        
        # 결과 요약
        print("\n" + "=" * 50)
        print("📊 Test Results Summary:")
        print(f"Health Endpoint: {'✅ PASS' if health_ok else '❌ FAIL'}")
        print(f"Root Endpoint: {'✅ PASS' if root_ok else '❌ FAIL'}")
        print(f"QnA Endpoint: {'✅ PASS' if qna_ok else '❌ FAIL'}")
        
        if all([health_ok, root_ok, qna_ok]):
            print("\n🎉 All tests passed! Application is working correctly.")
        else:
            print("\n⚠️  Some tests failed. Check the logs above for details.")
            
    else:
        print("\n❌ Application is not responding to health checks.")
        print("Please make sure the application is running:")
        print("1. Check if the container is running: docker ps")
        print("2. Check container logs: docker logs <container_id>")
        print("3. Verify environment variables are set correctly")
        print("4. Check if port 8000 is accessible")

if __name__ == "__main__":
    main()
