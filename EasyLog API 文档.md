# EasyLog API 文档

EasyLog 是一个简化易用的日志管理模块，提供统一、开箱即用的日志服务。支持多级别日志、文件轮转、控制台输出，并具有完善的错误处理机制。

## 特性

- 开箱即用，无需复杂配置
- 支持日志分级（DEBUG/INFO/WARNING/ERROR/CRITICAL）
- 自动日志文件轮转，防止单个文件过大
- 同时支持文件日志和控制台输出
- 完善的错误处理和目录自动创建
- 支持 Uvicorn 日志集成，适合 FastAPI 等 web 框架
- 单例模式设计，确保全局日志配置一致

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

## 核心 API

### `setup_logging(config=None, **kwargs)`

显式初始化日志系统，可指定自定义配置。如果未调用此函数，首次使用`get_logger`时会自动初始化。

**参数:**
- `config` (dict, 可选): 配置字典，包含日志系统的各项设置
- `** kwargs`: 关键字参数，会覆盖`config`中同名配置

**配置选项:**

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| log_level | str | "INFO" | 日志级别，可选值：DEBUG, INFO, WARNING, ERROR, CRITICAL |
| log_dir | str/Path | 项目根目录/logs | 日志文件保存目录 |
| log_filename | str | "app.log" | 日志文件名 |
| max_bytes | int | 10*1024*1024 (10MB) | 单个日志文件最大大小 |
| backup_count | int | 5 | 日志文件轮转备份数量 |
| console_output | bool | True | 是否在控制台输出日志 |
| format | str | "%(asctime)s - %(name)s - %(levelname)s - %(message)s" | 日志格式 |
| date_format | str | "%Y-%m-%d %H:%M:%S" | 日期时间格式 |
| configure_uvicorn_logging_runtime | bool | False | 是否在运行时配置Uvicorn日志 |
| uvicorn_log_level_runtime | str | "INFO" | Uvicorn运行时日志级别 |

### `get_logger(name)`

获取指定名称的日志记录器。如果日志系统尚未初始化，会自动使用默认配置初始化。

**参数:**
- `name` (str): 日志器名称，通常使用模块名或功能名

**返回:**
- `logging.Logger`: 配置好的日志记录器实例

### `get_log_path()`

获取当前日志文件保存的目录路径。

**返回:**
- `Path`: 日志目录的路径对象

### `get_uvicorn_log_config()`

生成Uvicorn可用的日志配置字典，用于在FastAPI等框架中统一日志格式。

**返回:**
- `dict`: Uvicorn日志配置字典

## 高级用法

### Uvicorn 集成

在FastAPI等使用Uvicorn的框架中，确保日志格式统一：

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
    # 使用EasyLog的配置来运行Uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_config=get_uvicorn_log_config()  # 使用统一日志配置
    )
```

### 多模块日志

在大型项目中，不同模块使用不同名称的日志器，便于日志分类：

```python
# module_a.py
from easylog import get_logger

logger = get_logger("module.a")

def function_a():
    logger.info("执行模块A的功能")

# module_b.py
from easylog import get_logger

logger = get_logger("module.b")

def function_b():
    logger.info("执行模块B的功能")
```

### 异常日志记录

记录异常信息时，使用`exc_info=True`参数捕获堆栈跟踪：

```python
from easylog import get_logger

logger = get_logger("error_handling")

try:
    # 可能出错的代码
    result = 1 / 0
except ZeroDivisionError:
    logger.error("发生除零错误", exc_info=True)  # 记录异常堆栈
```

## 路径处理

日志系统会自动处理目录创建和路径选择：

1. 优先使用`setup_logging`中指定的`log_dir`
2. 若指定目录不可写，会依次尝试：
   - 项目根目录下的`logs`文件夹
   - 用户主目录下的`.logs/项目名`
   - 系统临时目录下的`项目名/logs`
3. 可通过`get_log_path()`获取实际使用的日志目录

```python
from easylog import get_log_path

print(f"日志文件保存路径: {get_log_path()}")
```