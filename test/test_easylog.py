import os
import sys
import tempfile
import shutil
from pathlib import Path
import logging
import threading
import time
from unittest.mock import patch, MagicMock

import pytest


from easylogz import (
    LoggerManager,
    setup_logging,
    get_logger,
    get_log_path,
    get_uvicorn_log_config,
)


class TestLoggerManager:
    """Test cases for LoggerManager class"""

    def setup_method(self):
        """Setup method to run before each test method."""
        # Reset singleton instance for each test
        LoggerManager._instance = None
        LoggerManager._initialized = False
        LoggerManager._final_config = None

        # 确保所有日志处理器被关闭
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            handler.close()
            root_logger.removeHandler(handler)

    def test_singleton_instance(self):
        """Test that LoggerManager follows singleton pattern"""
        manager1 = LoggerManager()
        manager2 = LoggerManager()
        assert manager1 is manager2

    def test_singleton_thread_safety(self):
        """Test that LoggerManager is thread-safe"""
        instances = []

        def create_instance():
            instances.append(LoggerManager())

        threads = []
        for _ in range(10):
            thread = threading.Thread(target=create_instance)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All instances should be the same
        assert all(instance is instances[0] for instance in instances)

    def test_default_initialization(self):
        """Test default initialization"""
        manager = LoggerManager()
        manager.initialize()

        assert manager.is_initialized == True
        assert manager.get_log_path().exists()

    def test_custom_config_initialization(self):
        """Test initialization with custom configuration"""
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_config = {
                "log_level": "DEBUG",
                "log_filename": "test.log",
                "log_dir": temp_dir,
                "max_bytes": 5 * 1024 * 1024,  # 5MB
                "backup_count": 3
            }

            manager = LoggerManager()
            manager.initialize(custom_config)

            assert manager.is_initialized == True
            assert str(manager.get_log_path()) == str(Path(temp_dir).resolve())

            # 关闭日志处理器以释放文件锁
            root_logger = logging.getLogger()
            for handler in root_logger.handlers:
                handler.close()

    def test_duplicate_initialization_warning(self, capsys):
        """Test that duplicate initialization shows warning"""
        manager = LoggerManager()
        manager.initialize()
        manager.initialize()  # Try to initialize again

        captured = capsys.readouterr()
        assert "日志系统已经初始化过，跳过重复初始化" in captured.out or \
               "日志系统已经初始化过，跳过重复初始化" in captured.err

    def test_get_logger(self):
        """Test getting a logger instance"""
        manager = LoggerManager()
        logger = manager.get_logger("test.module")

        assert isinstance(logger, logging.Logger)
        assert logger.name == "test.module"
        # Should be initialized automatically
        assert manager.is_initialized == True

    def test_get_log_path(self):
        """Test getting log path"""
        manager = LoggerManager()
        path = manager.get_log_path()

        # Should be initialized automatically
        assert manager.is_initialized == True
        assert isinstance(path, Path)
        assert path.exists()

    @pytest.mark.parametrize("level_str,expected", [
        ("DEBUG", logging.DEBUG),
        ("INFO", logging.INFO),
        ("WARNING", logging.WARNING),
        ("ERROR", logging.ERROR),
        ("CRITICAL", logging.CRITICAL),
        ("invalid", logging.INFO),  # Should default to INFO
    ])
    def test_log_levels(self, level_str, expected):
        """Test different log levels"""
        manager = LoggerManager()
        if level_str == "invalid":
            with patch("builtins.print") as mock_print:
                level = manager._get_log_level(level_str)
                mock_print.assert_called_once()
        else:
            level = manager._get_log_level(level_str)
        assert level == expected


class TestPublicAPI:
    """Test cases for public API functions"""

    def setup_method(self):
        """Reset LoggerManager before each test"""
        LoggerManager._instance = None
        LoggerManager._initialized = False
        LoggerManager._final_config = None

        # 确保所有日志处理器被关闭
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            handler.close()
            root_logger.removeHandler(handler)



    def test_get_logger_function(self):
        """Test get_logger function"""
        logger = get_logger("api.test")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "api.test"

    def test_get_log_path_function(self):
        """Test get_log_path function"""
        path = get_log_path()
        assert isinstance(path, Path)
        assert path.exists()

    def test_get_uvicorn_log_config(self):
        """Test get_uvicorn_log_config function"""
        config = get_uvicorn_log_config()

        # Check that it returns a dict with expected structure
        assert isinstance(config, dict)
        assert "version" in config
        assert "formatters" in config
        assert "handlers" in config
        assert "loggers" in config


class TestLogFunctionality:
    """Test actual logging functionality"""

    def setup_method(self):
        """Setup method to run before each test method."""
        LoggerManager._instance = None
        LoggerManager._initialized = False
        LoggerManager._final_config = None

        # 确保所有日志处理器被关闭
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            handler.close()
            root_logger.removeHandler(handler)



    def test_multiple_loggers(self):
        """Test that multiple loggers can be created"""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2.submodule")

        assert logger1.name == "module1"
        assert logger2.name == "module2.submodule"
        # Both should be instances of logging.Logger
        assert isinstance(logger1, logging.Logger)
        assert isinstance(logger2, logging.Logger)


class TestErrorHandling:
    """Test error handling and fallback mechanisms"""

    def setup_method(self):
        """Reset LoggerManager before each test"""
        LoggerManager._instance = None
        LoggerManager._initialized = False
        LoggerManager._final_config = None

        # 确保所有日志处理器被关闭
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            handler.close()
            root_logger.removeHandler(handler)



if __name__ == "__main__":
    pytest.main([__file__])
