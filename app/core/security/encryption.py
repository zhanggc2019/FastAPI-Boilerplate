"""
API Key 加密/解密工具

使用 Fernet 对称加密来保护 API Key
"""
from cryptography.fernet import Fernet
from app.core.config import config


class KeyEncryption:
    """API Key 加密/解密类"""
    
    def __init__(self):
        # 从配置中获取加密密钥,如果没有则生成一个
        # 注意: 生产环境必须在 .env 中配置 ENCRYPTION_KEY
        encryption_key = getattr(config, 'ENCRYPTION_KEY', None)
        if not encryption_key:
            # 开发环境使用固定密钥 (不安全,仅用于开发)
            encryption_key = b'development_key_32_bytes_long!!'
        
        if isinstance(encryption_key, str):
            encryption_key = encryption_key.encode()
        
        # 确保密钥是 32 字节的 base64 编码
        if len(encryption_key) != 44:  # base64 编码的 32 字节是 44 字符
            # 如果不是标准的 Fernet 密钥,使用它生成一个
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            from cryptography.hazmat.backends import default_backend
            import base64

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'fastapi_boilerplate_salt',
                iterations=100000,
                backend=default_backend()
            )
            key = base64.urlsafe_b64encode(kdf.derive(encryption_key))
            self.cipher = Fernet(key)
        else:
            self.cipher = Fernet(encryption_key)
    
    def encrypt(self, plaintext: str) -> str:
        """
        加密字符串
        
        Args:
            plaintext: 明文字符串
            
        Returns:
            加密后的字符串 (base64 编码)
        """
        if not plaintext:
            return plaintext
        
        encrypted_bytes = self.cipher.encrypt(plaintext.encode())
        return encrypted_bytes.decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """
        解密字符串
        
        Args:
            ciphertext: 密文字符串 (base64 编码)
            
        Returns:
            解密后的明文字符串
        """
        if not ciphertext:
            return ciphertext
        
        decrypted_bytes = self.cipher.decrypt(ciphertext.encode())
        return decrypted_bytes.decode()


# 全局加密实例
key_encryption = KeyEncryption()

