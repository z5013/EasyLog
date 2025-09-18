from easylog import setup_logging

# 自定义日志保存路径
setup_logging({
    "log_dir": "./logss",  # 显式指定日志保存目录
    "log_filename": "my_app.log"      # 日志文件名（可选，默认是 app.log）
})