"""ログ設定モジュール"""

from loguru import logger
import sys


def setup_logger(log_level: str = "INFO") -> None:
    """ログ設定を初期化する
    Args:
        log_level: ログレベル（DEBUG, INFO, WARNING, ERROR, CRITICAL）
    """
    # 既存のハンドラーを削除
    logger.remove()
    # コンソール出力の設定
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )
