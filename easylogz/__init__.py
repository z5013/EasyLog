"""
简化易用的日志管理模块：提供统一、开箱即用的日志服务。
支持多级别日志、文件轮转、控制台输出，并具有完善的错误处理机制。
用户只需调用 get_logger 即可获得已配置好的 logger，无需手动初始化。
现在也支持配置 Uvicorn 的日志格式。
"""

from .logger_module import (
    setup_logging,
    get_logger,
    get_log_path,
    get_uvicorn_log_config,
    LoggerManager,
)

__version__ = "0.1.0"
__all__ = [
    "setup_logging",
    "get_logger",
    "get_log_path",
    "get_uvicorn_log_config",
    "LoggerManager",
]