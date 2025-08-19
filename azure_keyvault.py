import os
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class AzureKeyVaultManager:
    """Azure Key Vault에서 시크릿을 가져오는 매니저 클래스"""
    
    def __init__(self, vault_url: Optional[str] = None):
        """
        Azure Key Vault 매니저 초기화
        
        Args:
            vault_url: Key Vault URL (기본값: 환경변수 AZURE_KEY_VAULT_URL에서 가져옴)
        """
        self.vault_url = vault_url or os.getenv("AZURE_KEY_VAULT_URL")
        if not self.vault_url:
            raise ValueError("AZURE_KEY_VAULT_URL 환경변수가 설정되지 않았습니다.")
        
        try:
            # Azure 자격 증명 가져오기 (관리 ID, 서비스 주체, 또는 Azure CLI)
            self.credential = DefaultAzureCredential()
            self.client = SecretClient(vault_url=self.vault_url, credential=self.credential)
            logger.info(f"Azure Key Vault 연결 성공: {self.vault_url}")
        except Exception as e:
            logger.error(f"Azure Key Vault 연결 실패: {str(e)}")
            raise
    
    def get_secret(self, secret_name: str) -> Optional[str]:
        """
        Key Vault에서 시크릿 값을 가져옴
        
        Args:
            secret_name: 시크릿 이름
            
        Returns:
            시크릿 값 또는 None (실패 시)
        """
        try:
            secret = self.client.get_secret(secret_name)
            logger.info(f"시크릿 '{secret_name}' 가져오기 성공")
            return secret.value
        except Exception as e:
            logger.error(f"시크릿 '{secret_name}' 가져오기 실패: {str(e)}")
            return None
    
    def get_required_secrets(self, secret_names: list) -> dict:
        """
        필수 시크릿들을 한 번에 가져옴
        
        Args:
            secret_names: 필요한 시크릿 이름 리스트
            
        Returns:
            시크릿 이름과 값의 딕셔너리
        """
        secrets = {}
        missing_secrets = []
        
        for secret_name in secret_names:
            secret_value = self.get_secret(secret_name)
            if secret_value:
                secrets[secret_name] = secret_value
            else:
                missing_secrets.append(secret_name)
        
        if missing_secrets:
            raise ValueError(f"필수 시크릿을 가져올 수 없습니다: {missing_secrets}")
        
        return secrets

def load_env_from_keyvault():
    """
    Azure Key Vault에서 환경 변수를 로드하여 os.environ에 설정
    """
    try:
        # 환경변수에서 Key Vault URL 가져오기
        vault_url = os.getenv("AZURE_KEY_VAULT_URL")
        if not vault_url:
            logger.warning("AZURE_KEY_VAULT_URL이 설정되지 않아 Key Vault를 사용하지 않습니다.")
            return
        
        # Key Vault 매니저 생성
        kv_manager = AzureKeyVaultManager(vault_url)
        
        # 필요한 시크릿들 가져오기
        required_secrets = [
            "AZURE-OPENAI-API-KEY",
            "AZURE-OPENAI-ENDPOINT", 
            "AZURE-OPENAI-API-VERSION",
            "MONGODB-URI"
        ]
        
        secrets = kv_manager.get_required_secrets(required_secrets)
        
        # 환경변수에 설정
        env_mapping = {
            "AZURE-OPENAI-API-KEY": "AZURE_OPENAI_API_KEY",
            "AZURE-OPENAI-ENDPOINT": "AZURE_OPENAI_ENDPOINT",
            "AZURE-OPENAI-API-VERSION": "AZURE_OPENAI_API_VERSION",
            "MONGODB-URI": "MONGODB_URI"
        }
        
        for kv_name, env_name in env_mapping.items():
            if kv_name in secrets:
                os.environ[env_name] = secrets[kv_name]
                logger.info(f"환경변수 {env_name} 설정 완료")
        
        logger.info("Azure Key Vault에서 환경변수 로드 완료")
        
    except Exception as e:
        logger.error(f"Azure Key Vault에서 환경변수 로드 실패: {str(e)}")
        # Key Vault 실패 시 기존 환경변수 사용 (로컬 개발 환경)
        logger.info("기존 환경변수를 사용합니다.")

# 모듈 로드 시 자동으로 Key Vault에서 환경변수 로드
if __name__ != "__main__":
    load_env_from_keyvault()
