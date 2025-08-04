import streamlit as st

import sys
from pathlib import Path

from pydantic import ValidationError

from modules.const import AppData
from utils.en_to_ja import titles_en_to_ja
from datetime import datetime

from utils.system import get_src_root

sys.path.append(str(Path(__file__).parent.parent.parent))
from apps.opt_apps_layout import solve_layout
import pandas as pd
import streamlit.components.v1 as components

# 初期データ(streamlit上で変更・追加可能)
INITIAL_DATA = {
    "LINE": {"usage": 46, "genre": "SNS"},
    "X": {"usage": 26, "genre": "SNS"},
    "YouTube": {"usage": 21, "genre": "Entertainment"},
    "Instagram": {"usage": 18, "genre": "SNS"},
    "Slack": {"usage": 18, "genre": "Work"},
    "Chrome": {"usage": 14, "genre": "Utility"},
    "カメラ": {"usage": 11, "genre": "Utility"},
    "Google Maps": {"usage": 7, "genre": "Utility"},
    "時計": {"usage": 5, "genre": "Utility"},
    "Teams": {"usage": 5, "genre": "Work"},
    "乗換案内": {"usage": 5, "genre": "Utility"},
    "ゆうちょ通帳": {"usage": 5, "genre": "Finance"},
    "PayPay": {"usage": 5, "genre": "Finance"},
    "Gmail": {"usage": 4, "genre": "Work"},
    "写真": {"usage": 3, "genre": "Utility"},
    "Google": {"usage": 3, "genre": "Utility"},
    "Notion": {"usage": 3, "genre": "Work"},
    "Google カレンダー": {"usage": 2, "genre": "Work"},
    "BAND": {"usage": 2, "genre": "SNS"},
    "ウォレット": {"usage": 1, "genre": "Finance"},
    "Facebook": {"usage": 1, "genre": "SNS"},
    "Discord": {"usage": 1, "genre": "SNS"},
    "NewsPicks": {"usage": 1, "genre": "News"},
}


def display_rich_smartphone_ui(layout_data, style: str):
    """独自CSSでスマホUIを作成する関数"""
    main_screen_items = ""
    for loc_id in range(1, 25):
        item = layout_data.get(loc_id, "___(空)___")
        item_html = ""
        if item.startswith("F:"):
            folder_name = item.split(":")[1]
            item_html = f'<div class="folder-icon"><span>📁</span>{folder_name}</div>'
        elif item != "___(空)___":
            emoji = "📱"
            if any(x in item for x in ["カメラ", "写真"]):
                emoji = "🖼️"
            if any(x in item for x in ["Maps", "乗換"]):
                emoji = "🗺️"
            item_html = f'<div class="app-icon"><span>{emoji}</span>{item}</div>'
        else:
            item_html = '<div class="empty-slot"></div>'
        main_screen_items += item_html

    dock_items = ""
    for loc_id in range(25, 29):
        item = layout_data.get(loc_id, "___(空)___")
        if item != "___(空)___" and not item.startswith("F:"):
            emoji = "📱"
            if any(x in item for x in ["LINE", "Discord", "Slack"]):
                emoji = "💬"
            dock_items += f'<div class="app-icon"><span>{emoji}</span>{item}</div>'
        else:
            dock_items += '<div class="empty-slot"></div>'

    final_html = f"""
    <style>{style}</style>
    <div class="smartphone-container">
        <div class="status-bar">
            <span>{st.session_state.current_time}</span>
            <span>📶 🔋</span>
        </div>
        <div class="main-content">
            {main_screen_items}
        </div>
        <div class="page-indicator">
            <span class="active"></span><span></span>
        </div>
        <div class="dock">
            {dock_items}
        </div>
    </div>
    """
    components.html(final_html, height=580)


if "current_time" not in st.session_state:
    st.session_state.current_time = datetime.now().strftime("%-H:%M")


def app_view_optimize():
    titles_en_to_ja()
    st.title("📱 アプリ配置最適化")
    st.sidebar.header("設定")
    folder_penalty_input = st.sidebar.slider(
        "フォルダのペナルティ",
        0,
        50,
        20,
        help="値が大きいほどフォルダ化されにくくなります。",
    )

    # 初期モデル/DFを用意
    base_models = AppData.from_mapping(INITIAL_DATA)  # -> list[AppData]
    base_df = AppData.to_df(base_models)  # -> DataFrame

    # state 初期化
    if "apps_df" not in st.session_state:
        st.session_state.apps_df = base_df
    if "apps_models" not in st.session_state:
        st.session_state.apps_models = base_models
    if "apps_dict" not in st.session_state:
        st.session_state.apps_dict = AppData.to_solver_dict(base_models)

    with st.sidebar.expander("📋 アプリ一覧（編集可）", expanded=True):
        edited_df = st.data_editor(
            st.session_state.apps_df,
            hide_index=True,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "name": st.column_config.TextColumn("アプリ名", required=True),
                "usage": st.column_config.NumberColumn("使用回数", min_value=0, step=1),
                "genre": st.column_config.TextColumn("ジャンル"),
            },
            key="apps_editor",
        )

        c1, c2 = st.columns(2)
        with c1:
            if st.button("反映", use_container_width=True):
                rows = edited_df.replace({pd.NA: None}).to_dict(orient="records")
                models, errors, seen = [], [], set()
                for i, row in enumerate(rows, start=1):
                    try:
                        m = AppData.model_validate(row)
                        if m.name in seen:
                            raise ValueError(f'duplicate name: "{m.name}"')
                        seen.add(m.name)
                        models.append(m)
                    except Exception as e:
                        msg = (
                            "; ".join(err["msg"] for err in e.errors())
                            if isinstance(e, ValidationError)
                            else str(e)
                        )
                        errors.append(f"行{i}（name={row.get('name')}）: {msg}")

                if errors:
                    st.error("入力エラーがあります。修正してください。")
                    for msg in errors:
                        st.markdown(f"- {msg}")
                else:
                    st.session_state.apps_df = edited_df
                    st.session_state.apps_models = models
                    st.session_state.apps_dict = AppData.to_solver_dict(models)
                    st.success("アプリ一覧を反映しました。")

        with c2:
            if st.button("リセット", use_container_width=True):
                st.session_state.apps_df = base_df
                st.session_state.apps_models = base_models
                st.session_state.apps_dict = AppData.to_solver_dict(base_models)
                st.info("初期値に戻しました。")

    if st.sidebar.button("最適化を実行", type="primary"):
        with st.spinner("最適配置を計算中..."):
            layout, folders_content, status = solve_layout(
                st.session_state.apps_dict, folder_penalty_input
            )

        if status == "Optimal":
            st.success("最適配置が完了しました！")
            col1, col2 = st.columns([1, 1.5])
            with col1:
                smartphone_raw_css = Path(f"{get_src_root()}/assets/smartphone.css")
                smartphone_style = smartphone_raw_css.read_text(encoding="utf-8")
                display_rich_smartphone_ui(layout, smartphone_style)
            with col2:
                st.subheader("📁 フォルダの中身")
                if folders_content:
                    for f, app_list in folders_content.items():
                        if app_list:
                            st.markdown(f"**{f}**: `{'`, `'.join(app_list)}`")
                else:
                    st.info("作成されたフォルダはありません。")
        else:
            st.error(
                f"最適解が見つかりませんでした (ステータス: {status})。制約が厳しすぎる可能性があります。"
            )
    else:
        st.info(
            "サイドバーでパラメータを調整し、「最適化を実行」ボタンを押してください。"
        )


if __name__ == "__main__":
    app_view_optimize()
