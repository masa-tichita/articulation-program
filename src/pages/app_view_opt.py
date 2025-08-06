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
INITIAL_APPS_DATA = {
    "LINE": {"usage": 46, "genre": "SNS", "color": "green"},
    "X": {"usage": 26, "genre": "SNS", "color": "black"},
    "YouTube": {"usage": 21, "genre": "Entertainment", "color": "red"},
    "Instagram": {"usage": 18, "genre": "SNS", "color": "red"},
    "Slack": {"usage": 18, "genre": "Work", "color": "purple"},
    "Chrome": {"usage": 14, "genre": "Utility", "color": "blue"},
    "カメラ": {"usage": 11, "genre": "Utility", "color": "grey"},
    "Google Maps": {"usage": 7, "genre": "Utility", "color": "red"},
    "時計": {"usage": 5, "genre": "Utility", "color": "black"},
    "Teams": {"usage": 5, "genre": "Work", "color": "blue"},
    "乗換案内": {"usage": 5, "genre": "Utility", "color": "green"},
    "ゆうちょ通帳": {"usage": 5, "genre": "Finance", "color": "green"},
    "PayPay": {"usage": 5, "genre": "Finance", "color": "red"},
    "Gmail": {"usage": 4, "genre": "Work", "color": "red"},
    "写真": {"usage": 3, "genre": "Utility", "color": "blue"},
    "Google": {"usage": 3, "genre": "Utility", "color": "blue"},
    "Notion": {"usage": 3, "genre": "Work", "color": "black"},
    "Google カレンダー": {"usage": 2, "genre": "Work", "color": "blue"},
    "BAND": {"usage": 2, "genre": "SNS", "color": "green"},
    "ウォレット": {"usage": 1, "genre": "Finance", "color": "blue"},
    "Facebook": {"usage": 1, "genre": "SNS", "color": "blue"},
    "Discord": {"usage": 1, "genre": "SNS", "color": "blue"},
    "NewsPicks": {"usage": 1, "genre": "News", "color": "black"},
}

INITIAL_WEIGHTS_DATA = {
    1: 50, 2: 55, 3: 55, 4: 50, 5: 45, 6: 45, 7: 45, 8: 45,
    9: 35, 10: 25, 11: 25, 12: 35, 13: 25, 14: 60, 15: 60, 16: 25,
    17: 25, 18: 60, 19: 60, 20: 25, 21: 35, 22: 25, 23: 25, 24: 35,
    25: 45, 26: 40, 27: 40, 28: 45,
}



def display_rich_smartphone_ui(layout_data, style: str):
    """独自CSSでスマホUIを作成する関数"""
    main_screen_items = ""
    for loc_id in range(1, 25):
        item = layout_data.get(loc_id)
        item_html = ""
        if item:
            emoji = "📱"
            if any(x in item.name for x in ["カメラ", "写真"]):
                emoji = "🖼️"
            if any(x in item.name for x in ["Maps", "乗換"]):
                emoji = "🗺️"
            item_html = f'<div class="app-icon" style="background-color: {item.color}; color: white;"><span>{emoji}</span>{item.name}</div>'
        else:
            item_html = '<div class="empty-slot"></div>'
        main_screen_items += item_html

    dock_items = ""
    for loc_id in range(25, 29):
        item = layout_data.get(loc_id)
        if item:
            emoji = "📱"
            if any(x in item.name for x in ["LINE", "Discord", "Slack"]):
                emoji = "💬"
            dock_items += f'<div class="app-icon" style="background-color: {item.color}; color: white;"><span>{emoji}</span>{item.name}</div>'
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
    color_penalty_input = st.sidebar.slider(
        "色のペナルティ", 0, 100, 0, help="値が大きいほど同色アプリが離れて配置されます。"
    )

    # 初期モデル/DFを用意
    base_models = AppData.from_mapping(INITIAL_APPS_DATA)  # -> list[AppData]
    base_df = AppData.to_df(base_models)  # -> DataFrame
    base_weights_df = pd.DataFrame(
        list(INITIAL_WEIGHTS_DATA.items()), columns=["location", "weight"]
    )

    # state 初期化
    if "apps_df" not in st.session_state:
        st.session_state.apps_df = base_df
    if "apps_models" not in st.session_state:
        st.session_state.apps_models = base_models
    if "weights_df" not in st.session_state:
        st.session_state.weights_df = base_weights_df

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
                "color": st.column_config.TextColumn("色"),
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
                    st.success("アプリ一覧を反映しました。")

        with c2:
            if st.button("リセット", use_container_width=True):
                st.session_state.apps_df = base_df
                st.session_state.apps_models = base_models
                st.info("初期値に戻しました。")

    with st.sidebar.expander("🏋️ 重み（場所の価値）", expanded=False):
        edited_weights_df = st.data_editor(
            st.session_state.weights_df,
            hide_index=True,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "location": st.column_config.NumberColumn("ロケーション番号", required=True, min_value=1, max_value=28),
                "weight": st.column_config.NumberColumn("重み", min_value=0, step=1),
            },
            key="weights_editor",
        )

        c1, c2 = st.columns(2)
        with c1:
            if st.button("重みを反映", use_container_width=True):
                st.session_state.weights_df = edited_weights_df
                st.success("重みを反映しました。")
        with c2:
            if st.button("重みをリセット", use_container_width=True):
                st.session_state.weights_df = base_weights_df
                st.info("重みを初期値に戻しました。")

    if st.sidebar.button("最適化を実行", type="primary"):
        # DataFrameをdictに変換して渡す
        weights_dict = st.session_state.weights_df.set_index('location')['weight'].to_dict()
        with st.spinner("最適配置を計算中..."):
            layout, status = solve_layout(
                st.session_state.apps_models,
                weights=weights_dict,
                color_penalty_val=color_penalty_input,
            )

        if status == "Optimal":
            st.success("最適配置が完了しました！")
            smartphone_raw_css = Path(f"{get_src_root()}/assets/smartphone.css")
            smartphone_style = smartphone_raw_css.read_text(encoding="utf-8")
            display_rich_smartphone_ui(layout, smartphone_style)
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
