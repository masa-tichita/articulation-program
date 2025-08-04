import streamlit as st
from loguru import logger

from utils.en_to_ja import titles_en_to_ja
from utils.logging import setup_logger


def main():
    setup_logger(log_level="INFO")
    logger.info("start app")

    # streamlit settings
    st.set_page_config(
        page_title="最適化アプリケーション",
        page_icon="🔧",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    titles_en_to_ja()

    # メインページ
    st.title("日立北1,2班 最適化アプリケーション 2025年高大連携")
    st.markdown("---")
    # フッター
    st.markdown("*Powered by PuLP + Streamlit + Pydantic*")


if __name__ == "__main__":
    main()
