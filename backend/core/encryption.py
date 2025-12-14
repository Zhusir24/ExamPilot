"""加密工具模块 - 用于加密敏感数据如API密钥"""
from cryptography.fernet import Fernet, InvalidToken
from typing import Optional
import os
import base64
from pathlib import Path
from backend.core.logger import log


class EncryptionService:
    """加密服务类"""

    _instance = None
    _key: Optional[bytes] = None
    _cipher: Optional[Fernet] = None

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化加密服务"""
        if self._key is None:
            self._load_or_generate_key()

    def _load_or_generate_key(self):
        """加载或生成加密密钥"""
        # 密钥文件路径
        key_file = Path(__file__).parent.parent.parent / "data" / ".encryption_key"

        try:
            if key_file.exists():
                # 加载现有密钥
                with open(key_file, "rb") as f:
                    self._key = f.read()
                log.info("加载现有加密密钥")
            else:
                # 生成新密钥
                self._key = Fernet.generate_key()

                # 确保目录存在
                key_file.parent.mkdir(parents=True, exist_ok=True)

                # 保存密钥（仅所有者可读写）
                with open(key_file, "wb") as f:
                    f.write(self._key)

                # 设置文件权限（仅所有者可读写）
                os.chmod(key_file, 0o600)

                log.info(f"生成并保存新的加密密钥: {key_file}")
                log.warning("请备份加密密钥文件，否则无法解密已加密的数据！")

            # 创建加密器
            self._cipher = Fernet(self._key)

        except Exception as e:
            log.error(f"初始化加密服务失败: {e}")
            raise

    def encrypt(self, plain_text: str) -> Optional[str]:
        """
        加密字符串

        Args:
            plain_text: 明文字符串

        Returns:
            加密后的base64编码字符串，失败返回None
        """
        if not plain_text:
            return None

        try:
            # 加密
            encrypted_bytes = self._cipher.encrypt(plain_text.encode('utf-8'))
            # 转换为base64字符串便于存储
            return base64.b64encode(encrypted_bytes).decode('utf-8')
        except Exception as e:
            log.error(f"加密失败: {e}")
            return None

    def decrypt(self, encrypted_text: str) -> Optional[str]:
        """
        解密字符串（兼容明文）

        Args:
            encrypted_text: 加密的base64编码字符串或明文字符串

        Returns:
            解密后的明文字符串，失败返回原始值
        """
        if not encrypted_text:
            return None

        try:
            # 从base64解码
            encrypted_bytes = base64.b64decode(encrypted_text.encode('utf-8'))
            # 解密
            decrypted_bytes = self._cipher.decrypt(encrypted_bytes)
            log.debug("成功解密API密钥")
            return decrypted_bytes.decode('utf-8')
        except InvalidToken:
            # 解密失败，可能是明文数据（兼容旧数据）
            log.warning(f"⚠️ API密钥解密失败，将作为明文使用（建议迁移到加密存储）")
            return encrypted_text  # 返回原始值作为明文
        except Exception as e:
            # Base64解码失败或其他错误，也当作明文处理
            log.warning(f"⚠️ API密钥处理失败: {e}，将作为明文使用")
            return encrypted_text  # 返回原始值作为明文

    def is_encrypted(self, text: str) -> bool:
        """
        检查字符串是否已加密

        Args:
            text: 待检查的字符串

        Returns:
            True表示已加密，False表示未加密
        """
        if not text:
            return False

        try:
            # 尝试base64解码
            decoded = base64.b64decode(text.encode('utf-8'))
            # 尝试解密
            self._cipher.decrypt(decoded)
            return True
        except Exception:
            return False


# 全局加密服务实例
encryption_service = EncryptionService()
