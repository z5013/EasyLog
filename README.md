# EasyLog - 简化易用的Python日志库

[![PyPI](https://img.shields.io/pypi/v/easylog)](https://pypi.org/project/easylog/)
[![Python Version](https://img.shields.io/pypi/pyversions/easylog)](https://pypi.org/project/easylog/)
[![License](https://img.shields.io/pypi/l/easylog)](https://github.com/your-username/easylog/blob/main/LICENSE)

EasyLog 是一个简化易用的 Python 日志管理模块，提供统一、开箱即用的日志服务。支持多级别日志、文件轮转、控制台输出，并具有完善的错误处理机制。

## 特性

- 🚀 开箱即用，无需复杂配置
- 📝 支持日志分级（DEBUG/INFO/WARNING/ERROR/CRITICAL）
- 🔄 自动日志文件轮转，防止单个文件过大
- 🖥️ 同时支持文件日志和控制台输出
- 🛡️ 完善的错误处理和目录自动创建
- 🌐 支持 Uvicorn 日志集成，适合 FastAPI 等 web 框架
- 🔒 单例模式设计，确保全局日志配置一致

## 安装

```bash
pip install easylog
```

## 快速开始

### 基本使用

```python
from easylog import get_logger

# 获取日志器（首次调用会自动初始化日志系统）
logger = get_logger("my_module")

# 输出不同级别日志
logger.debug("这是调试信息")
logger.info("这是普通信息")
logger.warning("这是警告信息")
logger.error("这是错误信息")
logger.critical("这是严重错误信息")
```

### 自定义配置

```python
from easylog import setup_logging, get_logger

# 显式配置日志系统
setup_logging({
    "log_level": "DEBUG",          # 日志级别
    "log_dir": "/path/to/logs",    # 日志目录
    "log_filename": "app.log",     # 日志文件名
    "max_bytes": 5 * 1024 * 1024,  # 单个日志文件最大大小(5MB)
    "backup_count": 5,             # 保留的备份日志数量
    "console_output": True         # 是否输出到控制台
})

# 使用配置好的日志器
logger = get_logger("my_app")
logger.info("应用启动")
```

## Uvicorn 集成

在 FastAPI 等使用 Uvicorn 的框架中，确保日志格式统一：

```python
from fastapi import FastAPI
import uvicorn
from easylog import setup_logging, get_uvicorn_log_config, get_logger

# 配置日志
setup_logging({
    "log_level": "INFO",
    "console_output": True,
    "configure_uvicorn_logging_runtime": True
})

app = FastAPI()
logger = get_logger("fastapi_app")

@app.get("/")
async def root():
    logger.info("收到请求")
    return {"message": "Hello World"}

if __name__ == "__main__":
    # 使用 EasyLog 的配置来运行 Uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_config=get_uvicorn_log_config()  # 使用统一日志配置
    )
```

## 许可证

MIT License. 详细信息请查看 [LICENSE](LICENSE) 文件。

## 贡献

欢迎提交 Issue 和 Pull Request 来帮助改进这个项目。