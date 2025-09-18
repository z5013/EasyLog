"""
简化易用的日志管理模块：提供统一、开箱即用的日志服务。
支持多级别日志、文件轮转、控制台输出，并具有完善的错误处理机制。
用户只需调用 get_logger 即可获得已配置好的 logger，无需手动初始化。
现在也支持配置 Uvicorn 的日志格式。
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional, Union, Dict, Any
import threading
import tempfile
import atexit

# 定义日志级别映射
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}

# 默认配置
DEFAULT_CONFIG = {
    "log_level": "INFO",
    "max_bytes": 10 * 1024 * 1024,  # 10MB
    "backup_count": 5,
    "console_output": True,
    "log_filename": "app.log",
    "project_root": None,  # 将在初始化时动态确定
    "log_dir": None,  # 将在初始化时动态确定
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "date_format": "%Y-%m-%d %H:%M:%S",
    # Uvicorn 集成配置 (用于运行时配置，非启动时)
    "configure_uvicorn_logging_runtime": False,  # 是否在运行时（worker进程）配置 Uvicorn 日志
    "uvicorn_log_level_runtime": "INFO",  # Uvicorn 日志级别 (运行时)
}


class LoggerManager:
    """
    日志管理器单例类。
    负责初始化和配置整个应用程序的日志系统。
    支持显式初始化和首次使用时的自动初始化。
    """

    _instance = None
    _lock = threading.Lock()  # 用于线程安全的锁
    _initialized = False
    _final_config = None  # 保存最终使用的配置

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                # Double-checked locking pattern
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(self, config: Optional[Dict[str, Any]] = None, **kwargs):
        """
        显式初始化日志系统。如果已初始化，则跳过。

        Args:
            config (dict, optional): 配置字典。
            **kwargs: 其他配置项，会覆盖 config 字典中的同名项。
        """
        if self._initialized:
            self._get_root_logger().warning("日志系统已经初始化过，跳过重复初始化")
            return

        # 合并配置
        final_config = DEFAULT_CONFIG.copy()
        if config:
            final_config.update(config)
        final_config.update(kwargs)
        self._final_config = final_config  # 保存配置供后续使用

        self._setup_logging_internal(final_config)
        self._initialized = True
        self._get_root_logger().info(
            f"✅ 日志系统已显式初始化，日志目录: {self.log_dir}"
        )
        # 如果配置要求，则在运行时配置 Uvicorn 日志 (worker进程)
        # 注意：这主要影响 worker 进程中的 Uvicorn 日志，对主进程 reload 日志影响有限
        if final_config.get("configure_uvicorn_logging_runtime", False):
            self._configure_uvicorn_logging_runtime()

    def _ensure_initialized(self):
        """确保日志系统已初始化（懒加载/自动初始化）"""
        if not self._initialized:
            with self._lock:
                if not self._initialized:  # Double-check inside lock
                    # 使用默认配置自动初始化
                    self._setup_logging_internal(DEFAULT_CONFIG.copy())
                    self._initialized = True
                    self._get_root_logger().debug(
                        "🔍 日志系统已自动初始化（使用默认配置）"
                    )

    def _setup_logging_internal(self, config: Dict[str, Any]):
        """内部实际执行日志设置的函数"""
        log_level_str = config.get("log_level", "INFO")
        log_level = self._get_log_level(log_level_str)

        # 确定项目根目录
        project_root = self._resolve_project_root(config.get("project_root"))
        config["project_root"] = project_root  # 更新 config 供后续使用

        # 确定日志目录
        log_dir = self._resolve_log_dir(config.get("log_dir"), project_root)
        self.log_dir = self._create_log_directory(log_dir, project_root)

        # 获取并配置根记录器
        root_logger = self._get_root_logger()
        root_logger.setLevel(log_level)
        # 清除现有处理器
        self._clear_handlers(root_logger)

        self._formatter = logging.Formatter(  # 保存 formatter 实例供后续使用
            fmt=config.get("format", DEFAULT_CONFIG["format"]),
            datefmt=config.get("date_format", DEFAULT_CONFIG["date_format"]),
        )

        # 添加文件处理器
        if config.get("log_filename"):
            self._add_file_handler(
                root_logger,
                self._formatter,
                log_level,
                self.log_dir / config["log_filename"],
                config["max_bytes"],
                config["backup_count"],
            )

        # 添加控制台处理器
        if config.get("console_output", True):
            self._add_console_handler(root_logger, self._formatter, log_level)

    def _get_log_level(self, level_str: str) -> int:
        """获取 logging 级别常量"""
        level = LOG_LEVELS.get(level_str.upper())
        if level is None:
            print(f"⚠️ 未知日志级别: {level_str}，使用默认 INFO")
            return logging.INFO
        return level

    def _resolve_project_root(self, project_root: Optional[Union[str, Path]]) -> Path:
        """解析项目根目录"""
        if project_root is None:
            # 默认：假设此文件在项目根目录下的core文件夹中
            try:
                return Path(__file__).parent.parent.resolve()
            except Exception:
                # Fallback to current working directory if path resolution fails
                return Path.cwd()
        return Path(project_root).resolve()

    def _resolve_log_dir(
        self, log_dir: Optional[Union[str, Path]], project_root: Path
    ) -> Path:
        """解析日志目录路径"""
        if log_dir is None:
            # 默认日志目录：项目根目录下的 logs
            return project_root / "logs"
        log_dir_path = Path(log_dir)
        if not log_dir_path.is_absolute():
            return project_root / log_dir_path
        return log_dir_path

    def _create_log_directory(self, log_dir: Path, project_root: Path) -> Path:
        """创建日志目录，包含 fallback 机制"""
        dirs_to_try = [
            log_dir,
            project_root / "logs",  # 再次确保项目内 logs 目录是首选
            Path.home() / ".logs" / project_root.name,
            Path(tempfile.gettempdir()) / project_root.name / "logs",
        ]

        for dir_path in dirs_to_try:
            try:
                dir_path.mkdir(exist_ok=True, parents=True)
                print(f"📁 日志目录已创建或已存在: {dir_path}")
                return dir_path.resolve()
            except (PermissionError, OSError) as e:
                print(f"📁 尝试创建日志目录失败 {dir_path}: {e}")

        # 如果所有目录都失败，则使用临时目录并记录警告
        fallback_temp = Path(tempfile.gettempdir()) / "app_logs"
        try:
            fallback_temp.mkdir(exist_ok=True, parents=True)
            print(f"⚠️ 所有常规日志目录均不可用，使用临时目录: {fallback_temp}")
            return fallback_temp.resolve()
        except Exception as e:
            print(f"❌ 无法创建最终备用日志目录 {fallback_temp}: {e}")
            raise RuntimeError(
                f"无法创建任何日志目录。已尝试: {[str(d) for d in dirs_to_try]} 和 {fallback_temp}"
            ) from e

    def _get_root_logger(self) -> logging.Logger:
        """获取根记录器"""
        return logging.getLogger()

    def _clear_handlers(self, logger: logging.Logger):
        """清除记录器的所有处理器"""
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()

    def _add_file_handler(
        self,
        logger: logging.Logger,
        formatter: logging.Formatter,
        level: int,
        log_file: Path,
        max_bytes: int,
        backup_count: int,
    ):
        """添加文件处理器"""
        try:
            file_handler = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except (PermissionError, OSError) as e:
            print(f"❌ 无法写入主日志文件 {log_file}: {e}")
            # Fallback to a temporary file in the determined log dir
            import time

            temp_log_file = self.log_dir / f"{log_file.stem}.{int(time.time())}.tmp.log"
            try:
                file_handler = logging.handlers.RotatingFileHandler(
                    temp_log_file,
                    maxBytes=max_bytes,
                    backupCount=backup_count,
                    encoding="utf-8",
                )
                file_handler.setLevel(level)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
                print(f"📝 使用临时日志文件: {temp_log_file}")
            except Exception as e2:
                print(f"❌ 也无法写入临时日志文件 {temp_log_file}: {e2}")
                print("⚠️ 文件日志不可用")

    def _add_console_handler(
        self, logger: logging.Logger, formatter: logging.Formatter, level: int
    ):
        """添加控制台处理器"""
        try:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        except Exception as e:
            print(f"❌ 添加控制台日志处理器失败: {e}")

    def _configure_uvicorn_logging_runtime(self):
        """在运行时（worker进程）配置 Uvicorn 使用与主应用相同的日志格式和处理器"""
        # 这个方法主要用于 worker 进程，对主进程的 reload 日志影响不大
        if not self._final_config or not self._formatter:
            self._get_root_logger().warning(
                "无法在运行时配置 Uvicorn 日志：LoggerManager 未初始化配置或 formatter 丢失"
            )
            return

        try:
            # 导入 uvicorn 日志模块
            import uvicorn.logging
            import logging as uvicorn_root_logging

            # Uvicorn 的关键 Logger 名称
            uvicorn_loggers = [
                uvicorn_root_logging.getLogger("uvicorn"),
                uvicorn_root_logging.getLogger("uvicorn.error"),
                uvicorn_root_logging.getLogger("uvicorn.access"),
            ]

            uvicorn_log_level_str = self._final_config.get(
                "uvicorn_log_level_runtime", "INFO"
            )
            uvicorn_log_level = self._get_log_level(uvicorn_log_level_str)

            # 配置每个 Uvicorn Logger
            for logger in uvicorn_loggers:
                # 清除 Uvicorn 默认的 Handlers
                self._clear_handlers(logger)
                logger.setLevel(uvicorn_log_level)

                # 如果主应用配置了控制台输出，则 Uvicorn 也添加控制台 Handler
                if self._final_config.get("console_output", True):
                    console_handler = logging.StreamHandler(sys.stdout)
                    console_handler.setLevel(uvicorn_log_level)
                    console_handler.setFormatter(
                        self._formatter
                    )  # 使用主应用的 formatter
                    logger.addHandler(console_handler)

                # 如果主应用配置了文件输出，则 Uvicorn 也添加文件 Handler
                if self._final_config.get("log_filename"):
                    try:
                        uvicorn_log_file = (
                            self.log_dir / self._final_config["log_filename"]
                        )
                        uvicorn_file_handler = logging.handlers.RotatingFileHandler(
                            uvicorn_log_file,
                            maxBytes=self._final_config["max_bytes"],
                            backupCount=self._final_config["backup_count"],
                            encoding="utf-8",
                        )
                        uvicorn_file_handler.setLevel(uvicorn_log_level)
                        uvicorn_file_handler.setFormatter(
                            self._formatter
                        )  # 使用主应用的 formatter
                        logger.addHandler(uvicorn_file_handler)
                    except Exception as e:
                        self._get_root_logger().warning(
                            f"为 Uvicorn 配置文件日志处理器时出错: {e}"
                        )

                # 确保日志向上传播到根 logger
                logger.propagate = True

            self._get_root_logger().debug(
                "🔍 Uvicorn 日志系统已在运行时配置（worker进程）。"
            )

        except ImportError:
            self._get_root_logger().warning(
                "无法导入 uvicorn 模块，跳过运行时 Uvicorn 日志配置。"
            )
        except Exception as e:
            self._get_root_logger().error(
                f"在运行时配置 Uvicorn 日志时发生未预期错误: {e}"
            )

    def get_logger(self, name: str) -> logging.Logger:
        """
        获取指定名称的日志记录器。
        如果日志系统尚未初始化，会自动使用默认配置进行初始化。
        """
        self._ensure_initialized()  # 关键：自动初始化
        return logging.getLogger(name)

    @property
    def is_initialized(self) -> bool:
        """检查日志系统是否已初始化"""
        return self._initialized

    def get_log_path(self) -> Path:
        """获取当前日志目录路径"""
        # 确保已初始化以获取正确的路径
        self._ensure_initialized()
        return getattr(self, "log_dir", Path.cwd())  # Fallback

    def get_uvicorn_log_config(self) -> Dict[str, Any]:
        """
        生成一个 Uvicorn 可以使用的 log_config 字典。
        这个字典应该在 uvicorn.run() 中通过 log_config 参数传递。
        这是确保 Uvicorn 主进程（包括 reload 日志）也使用自定义格式的关键。
        """
        self._ensure_initialized()  # 确保 formatter 已创建

        if not hasattr(self, "_formatter") or self._formatter is None:
            # Fallback to default formatter if somehow not available
            formatter = logging.Formatter(
                fmt=DEFAULT_CONFIG["format"],
                datefmt=DEFAULT_CONFIG["date_format"],
            )
        else:
            formatter = self._formatter

        # 构建 Uvicorn 的 log_config 字典
        # 这个配置会告诉 Uvicorn 如何记录日志，包括主进程和子进程
        log_config = {
            "version": 1,
            "disable_existing_loggers": False,  # ⚠️ 关键：不要禁用现有的 logger！
            "formatters": {
                "custom": {  # 定义你的自定义格式器
                    "()": "logging.Formatter",  # 直接使用 Python 的 Formatter
                    "fmt": formatter._fmt,
                    "datefmt": formatter.datefmt,
                },
            },
            "handlers": {
                "default": {
                    "formatter": "custom",  # 使用上面定义的自定义格式器
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stderr",  # Uvicorn 默认使用 stderr
                },
                # 如果你也想让 Uvicorn 的日志写入文件，可以添加一个文件 handler
                # 注意：这会与你主应用的文件日志叠加
                # "file": {
                #     "formatter": "custom",
                #     "class": "logging.handlers.RotatingFileHandler",
                #     "filename": str(self.get_log_path() / (self._final_config.get("log_filename", "app.log") if self._final_config else "app.log")),
                #     "maxBytes": self._final_config.get("max_bytes", DEFAULT_CONFIG["max_bytes"]) if self._final_config else DEFAULT_CONFIG["max_bytes"],
                #     "backupCount": self._final_config.get("backup_count", DEFAULT_CONFIG["backup_count"]) if self._final_config else DEFAULT_CONFIG["backup_count"],
                #     "encoding": "utf-8",
                # },
            },
            "loggers": {
                "": {"handlers": ["default"], "level": "INFO"},  # 根 logger
                "uvicorn": {
                    "handlers": ["default"],  # 使用 default handler (带自定义格式)
                    # "handlers": ["default", "file"], # 如果启用了文件 handler
                    "level": "INFO",
                    "propagate": False,  # 通常设为 False，避免重复输出到根 logger
                },
                "uvicorn.error": {
                    "level": "INFO",
                    "handlers": ["default"],  # 同样使用 default handler
                    # "handlers": ["default", "file"],
                    "propagate": False,  # 关键！设为 False 避免默认 handler 和 propagate 双重输出
                },
                "uvicorn.access": {
                    "handlers": ["default"],
                    # "handlers": ["default", "file"],
                    "level": "INFO",
                    "propagate": False,  # 让访问日志也使用自定义 handler，避免向上传播
                },
                # 可以根据需要添加更多特定的 uvicorn 子 logger
            },
        }
        return log_config


# 全局单例实例
_logger_manager = LoggerManager()


# --- 快捷函数 ---
def setup_logging(config: Optional[Dict[str, Any]] = None, **kwargs):
    """
    显式设置日志系统配置 (快捷方式)。
    应在程序启动早期调用，以覆盖默认配置。
    要启用运行时 Uvicorn 日志适配，请在 config 中设置 'configure_uvicorn_logging_runtime': True

    Args:
        config (dict, optional): 配置字典。
        **kwargs: 其他配置项，优先级高于 config。
    """
    _logger_manager.initialize(config, **kwargs)


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志记录器 (主要快捷方式)。
    如果日志系统尚未初始化，会自动使用默认配置进行初始化。

    Args:
        name (str): 记录器名称。

    Returns:
        logging.Logger: 对应名称的日志记录器。
    """
    return _logger_manager.get_logger(name)


def get_log_path() -> Path:
    """
    获取当前日志目录路径 (快捷方式)。

    Returns:
        Path: 日志目录路径。
    """
    return _logger_manager.get_log_path()


def get_uvicorn_log_config() -> Dict[str, Any]:
    """
    获取用于 Uvicorn 的 log_config 字典 (快捷方式)。
    这个字典应该在 uvicorn.run() 中通过 log_config 参数传递。
    """
    return _logger_manager.get_uvicorn_log_config()


# --- 自动清理 ---
# 确保在程序退出时，所有 handlers 都被正确关闭，尤其是文件 handlers
def _shutdown_logging():
    logging.shutdown()


atexit.register(_shutdown_logging)