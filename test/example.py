import time
from pathlib import Path


from easylog import setup_logging, get_logger, get_log_path


def main():
    # 示例1: 使用默认配置初始化日志系统
    print("=== 使用默认配置 ===")
    setup_logging()

    # 获取日志器
    logger = get_logger("default logger")

    # 输出不同级别的日志
    logger.debug("这是一条调试信息")
    logger.info("这是一条普通信息")
    logger.warning("这是一条警告信息")
    logger.error("这是一条错误信息")
    logger.critical("这是一条严重错误信息")

    # 查看日志文件位置
    print(f"默认日志文件位置: {get_log_path()}")
    print()

    # 示例2: 使用自定义配置
    print("=== 使用自定义配置 ===")
    custom_config = {
        # 日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL
        "log_level": "DEBUG",
        # 日志文件名
        "log_filename": "my_app.log",
        # 日志目录(可以是相对路径或绝对路径)
        "log_dir": Path(__file__).parent / "app_logs",
        # 单个日志文件最大大小(字节)
        "max_bytes": 10 * 1024 * 1024,  # 10MB
        # 保留的备份日志文件数量
        "backup_count": 5,
        # 是否同时输出到控制台
        "log_to_console": True
    }

    # 应用自定义配置
    setup_logging(custom_config)

    # 获取新的日志器
    app_logger = get_logger("my_application")

    # 输出日志
    app_logger.info("应用程序启动")
    app_logger.debug("配置参数: %s", custom_config)

    try:
        result = 10 / 0
    except ZeroDivisionError:
        app_logger.error("发生除零错误", exc_info=True)  # 记录异常信息

    # 查看自定义日志文件位置
    print(f"自定义日志文件位置: {get_log_path()}")
    print()

    # 示例3: 在不同模块中使用
    print("=== 多模块使用示例 ===")
    module_a()
    module_b()


def module_a():
    # 在模块A中获取日志器
    logger = get_logger("module.a")
    logger.info("模块A: 执行任务A")


def module_b():
    # 在模块B中获取日志器
    logger = get_logger("module.b")
    logger.info("模块B: 执行任务B")
    logger.warning("模块B: 资源即将耗尽")


if __name__ == "__main__":
    main()
    # 等待日志写入完成
    time.sleep(0.1)
