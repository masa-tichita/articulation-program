import streamlit as st


def titles_en_to_ja():
    return st.markdown(
        """
    <style>
 :root {
  --text-color: #808495; /* Light text color */
  --bg-color: transparent; /* Dark background color */
 }
 a[href$="/"] span:first-child {
    z-index: 1;
    color: transparent;
 }
 a[href$="/"] span:first-child::before {
    content: "ホーム";
    left: 0;
    z-index: 2;
    color: var(--text-color);
    background-color: var(--bg-color);
 }
  a[href$="/app_view_opt"] span:first-child {
    z-index: 1;
    color: transparent;
 }
 a[href$="/app_view_opt"] span:first-child::before {
    content: "アプリ配置最適化";
    left: 0;
    z-index: 2;
    color: var(--text-color);
    background-color: var(--bg-color);
 }
 </style>
    """,
        unsafe_allow_html=True,
    )
