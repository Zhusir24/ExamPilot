"""平台适配器模块"""
from backend.services.platforms.base import BasePlatform, PlatformType
from backend.services.platforms.wenjuanxing import WenjuanxingPlatform

__all__ = ["BasePlatform", "PlatformType", "WenjuanxingPlatform"]


# 平台注册表
PLATFORM_REGISTRY = {
    PlatformType.WENJUANXING: WenjuanxingPlatform,
}


def get_platform(url: str) -> BasePlatform:
    """根据URL获取平台适配器"""
    # 问卷星的多个域名
    wjx_domains = ["wjx.cn", "wjx.top", "wenjuan.com", "sojump.com", "wenjuan.in"]
    if any(domain in url for domain in wjx_domains):
        return WenjuanxingPlatform()
    
    raise ValueError(f"不支持的问卷平台: {url}")

