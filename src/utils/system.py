import time

from functools import wraps
from pathlib import Path
from typing import Callable, Any, TypeVar, ParamSpec
from loguru import logger


def get_project_root() -> Path:
    """プロジェクトルートディレクトリを取得する"""
    current_file = Path(__file__).resolve()
    return current_file.parent.parent.parent


def get_src_root() -> Path:
    """srcディレクトリのルートを取得する"""
    return get_project_root() / "src"


P = ParamSpec("P")
R = TypeVar("R")


def timer(func: Callable[P, R]) -> Callable[P, R]:
    """関数の実行時間を計測するデコレータ"""

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        t0 = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            dt = time.perf_counter() - t0
            logger.opt(depth=1).info("{} 実行時間: {:.4f}秒", func.__name__, dt)

    return wrapper


class TimingContext:
    """with文で使用する実行時間計測クラス"""

    def __init__(self, name: str):
        self.name = name
        self.start_time: float = 0

    def __enter__(self) -> "TimingContext":
        self.start_time = time.perf_counter()
        logger.debug(f"{self.name} 開始")
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        end_time = time.perf_counter()
        execution_time = end_time - self.start_time
        if exc_type is None:
            logger.info(f"{self.name} 完了: {execution_time:.4f}秒")
        else:
            logger.error(f"{self.name} エラー終了: {execution_time:.4f}秒")
