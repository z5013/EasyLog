# test_easylogz.py
import easylogz

logger = easylogz.get_logger(__name__)

logger.debug("调试信息")
logger.info("程序正常运行 ✅")
logger.warning("注意：这是一个警告 ⚠️")
logger.error("错误：发生异常！❌")