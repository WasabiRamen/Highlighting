# app/api/v1/core/logging.py
# Requires: settings.py
from loguru import logger
import sys
from pathlib import Path

# Loguru 기본 설정
logger.remove()  # 기본 핸들러 제거

console_format = (
    "<green>{time:YYYY-MM-DDTHH:mm:ss.SSSZZ}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{extra[service]}</cyan> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level> "
    "{extra[request_id]} {extra[user_id]}"
)


def initalize(log_path: str = None, log_level: str = None) -> None:
    Path(log_path).parent.mkdir(exist_ok=True)

    logger.add(
        sys.stdout,
        level=log_level,
        format=console_format,
        colorize=True,
        backtrace=True,
        diagnose=False,
    )

    logger.add(
        log_path,
        level=log_level,
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        serialize=True,
        enqueue=True,
    )