#!/usr/bin/env python3
"""
AI Q&A Service API 테스트 스크립트
"""

import requests
import json
import time

# 서버 설정
# BASE_URL = "http://localhost:8000"  # 로컬 테스트용
BASE_URL = "https://rag-qna-service-d0evbkbmbxeaf7at.koreacentral-01.azurewebsites.net"  # Azure 배포 후


def test_health_check():
    """헬스체크 엔드포인트 테스트"""
    print("🔍 헬스체크 테스트...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 헬스체크 실패: {e}")
        return False

def test_root_endpoint():
    """루트 엔드포인트 테스트"""
    print("\n🔍 루트 엔드포인트 테스트...")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 루트 엔드포인트 테스트 실패: {e}")
        return False

def test_qna_endpoint(question):
    """QnA 엔드포인트 테스트"""
    print(f"\n🔍 QnA 엔드포인트 테스트: {question}")
    
    payload = {
        "input_message": question
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/qna",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 성공!")
            print(f"AI 답변: {result['messages'][1]['AIMessage']}")
            print(f"인용문헌: {result['citations']}")
            return True
        else:
            print(f"❌ 실패: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ QnA 테스트 실패: {e}")
        return False

def test_invalid_request():
    """잘못된 요청 테스트 (422 에러)"""
    print("\n🔍 잘못된 요청 테스트...")
    
    # 잘못된 JSON 형식
    try:
        response = requests.post(
            f"{BASE_URL}/qna",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 422:
            print("✅ 422 에러 정상 처리")
            return True
        else:
            print(f"❌ 예상과 다른 상태 코드: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 잘못된 요청 테스트 실패: {e}")
        return False

def test_missing_field():
    """필수 필드 누락 테스트"""
    print("\n🔍 필수 필드 누락 테스트...")
    
    payload = {}  # input_message 필드 누락
    
    try:
        response = requests.post(
            f"{BASE_URL}/qna",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 422:
            print("✅ 422 에러 정상 처리")
            return True
        else:
            print(f"❌ 예상과 다른 상태 코드: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 필수 필드 누락 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🚀 AI Q&A Service API 테스트 시작")
    print("=" * 50)
    
    tests = [
        ("헬스체크", test_health_check),
        ("루트 엔드포인트", test_root_endpoint),
        ("QnA 정상 요청", lambda: test_qna_endpoint("자동차보험료 계산 방법 알려줘")),
        ("잘못된 요청", test_invalid_request),
        ("필수 필드 누락", test_missing_field),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name} 테스트")
        print("-" * 30)
        
        if test_func():
            passed += 1
            print(f"✅ {test_name} 통과")
        else:
            print(f"❌ {test_name} 실패")
        
        time.sleep(1)  # API 호출 간격 조절
    
    print("\n" + "=" * 50)
    print(f"🎯 테스트 결과: {passed}/{total} 통과")
    
    if passed == total:
        print("🎉 모든 테스트 통과!")
    else:
        print("⚠️  일부 테스트 실패")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
