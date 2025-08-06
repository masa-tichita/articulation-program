import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import streamlit.components.v1 as components
from datetime import datetime

from modules.const import AppData
from utils.en_to_ja import titles_en_to_ja
from utils.system import get_src_root

sys.path.append(str(Path(__file__).parent.parent.parent))
from apps.opt_apps_layout import solve_layout

# --- 初期データ ---
INITIAL_APPS_DATA = {
    "LINE": {"usage": 46, "color": "green"},
    "X": {"usage": 26, "color": "black"},
    "YouTube": {"usage": 21, "color": "red"},
    "Instagram": {"usage": 18, "color": "red"},
    "Slack": {"usage": 18, "color": "purple"},
    "Chrome": {"usage": 14, "color": "blue"},
    "カメラ": {"usage": 11, "color": "grey"},
    "Google Maps": {"usage": 7, "color": "red"},
}


# --- UI描画関数 ---
def display_dynamic_layout_ui(
    layout_data, style: str, rows: int, cols: int, dock_size: int
):
    """動的なグリッドレイアウトでUIを作成する関数"""
    num_main_locations = rows * cols
    main_screen_items = ""
    for loc_id in range(1, num_main_locations + 1):
        item = layout_data.get(loc_id)
        if item:
            emoji = "📱"
            if any(x in item.name for x in ["カメラ", "写真"]):
                emoji = "🖼️"
            if any(x in item.name for x in ["Maps", "乗換"]):
                emoji = "🗺️"
            main_screen_items += f'<div class="app-icon" style="background-color: {item.color};"><span>{emoji}</span>{item.name}</div>'
        else:
            main_screen_items += '<div class="empty-slot"></div>'

    dock_items = ""
    for loc_id in range(num_main_locations + 1, num_main_locations + dock_size + 1):
        item = layout_data.get(loc_id)
        if item:
            emoji = "📱"
            if any(x in item.name for x in ["LINE", "Discord", "Slack"]):
                emoji = "💬"
            dock_items += f'<div class="app-icon" style="background-color: {item.color};"><span>{emoji}</span>{item.name}</div>'
        else:
            dock_items += '<div class="empty-slot"></div>'

    final_html = f"""
    <style>
        {style}
        .main-content {{ grid-template-columns: repeat({cols}, 1fr); }}
        .dock {{ grid-template-columns: repeat({dock_size}, 1fr); }}
    </style>
    <div class="device-container">
        <div class="status-bar">
            <span>{st.session_state.current_time}</span>
            <span>📶 🔋</span>
        </div>
        <div class="main-content">{main_screen_items}</div>
        <div class="dock">{dock_items}</div>
    </div>
    """
    components.html(final_html, height=120 + rows * 85)


# --- 状態管理 ---
def update_weights_based_on_layout():
    """レイアウト設定の変更に応じて重みデータを更新する"""
    rows = st.session_state.layout_rows
    cols = st.session_state.layout_cols
    dock = st.session_state.dock_size
    total_locations = rows * cols + dock

    # 現在の重みデータとサイズが異なれば、新しいデフォルト値で再生成
    current_weights_size = len(st.session_state.get("weights_df", []))
    if total_locations != current_weights_size:
        new_weights = {i: 10 for i in range(1, total_locations + 1)}
        new_weights_list = [
            {"location": k, "weight": v} for k, v in new_weights.items()
        ]
        st.session_state.weights_df = pd.DataFrame(new_weights_list)


def initialize_session_state():
    """セッション状態を初期化する"""
    if "current_time" not in st.session_state:
        st.session_state.current_time = datetime.now().strftime("%-H:%M")

    # レイアウト設定の初期化
    if "layout_rows" not in st.session_state:
        st.session_state.layout_rows = 4
    if "layout_cols" not in st.session_state:
        st.session_state.layout_cols = 8
    if "dock_size" not in st.session_state:
        st.session_state.dock_size = 6

    # アプリデータ
    if "apps_df" not in st.session_state:
        base_models = AppData.from_mapping(INITIAL_APPS_DATA)
        st.session_state.apps_df = AppData.to_df(base_models)
        st.session_state.apps_models = base_models

    # 重みデータ（初回のみ、またはレイアウト変更時に更新）
    if "weights_df" not in st.session_state:
        update_weights_based_on_layout()


# --- サイドバーUI ---
def setup_sidebar():
    """サイドバーのUI要素を配置・管理する"""
    st.sidebar.header("設定")

    with st.sidebar.expander("📐 レイアウト設定", expanded=True):
        st.number_input(
            "行数", 1, 10, key="layout_rows", on_change=update_weights_based_on_layout
        )
        st.number_input(
            "列数", 1, 12, key="layout_cols", on_change=update_weights_based_on_layout
        )
        st.number_input(
            "Dockアプリアイコン数",
            1,
            15,
            key="dock_size",
            on_change=update_weights_based_on_layout,
        )

    color_penalty = st.sidebar.slider(
        "色のペナルティ",
        0,
        100,
        0,
        help="値が大きいほど同色アプリが離れて配置されます。",
    )

    with st.sidebar.expander("📋 アプリ一覧（編集可）", expanded=False):
        edited_df = st.data_editor(
            st.session_state.apps_df,
            hide_index=True,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "name": st.column_config.TextColumn("アプリ名", required=True),
                "usage": st.column_config.NumberColumn("使用回数", min_value=0, step=1),
                "color": st.column_config.TextColumn("色"),
            },
        )
        if st.button("アプリ一覧を反映"):
            # (省略) validationロジックは元のまま
            st.session_state.apps_df = edited_df
            # (省略) modelの更新ロジックも元のまま
            st.success("アプリ一覧を反映しました。")

    with st.sidebar.expander("🏋️ 重み（場所の価値）", expanded=False):
        # `key` を動的にして、レイアウト変更時にdata_editorを再生成させる
        editor_key = f"weights_editor_{st.session_state.layout_rows}_{st.session_state.layout_cols}_{st.session_state.dock_size}"
        edited_weights_df = st.data_editor(
            st.session_state.weights_df,
            hide_index=True,
            num_rows="dynamic",
            use_container_width=True,
            key=editor_key,
            column_config={
                "location": st.column_config.NumberColumn(
                    "ロケーション番号", required=True, min_value=1
                ),
                "weight": st.column_config.NumberColumn("重み", min_value=0, step=1),
            },
        )
        if st.button("重みを反映"):
            st.session_state.weights_df = edited_weights_df
            st.success("重みを反映しました。")

    return color_penalty


# --- メイン処理 ---
def app_view_optimize():
    titles_en_to_ja()
    st.title("📱 アプリ配置最適化")

    initialize_session_state()
    color_penalty_input = setup_sidebar()

    if st.sidebar.button("最適化を実行", type="primary"):
        weights_dict = st.session_state.weights_df.set_index("location")[
            "weight"
        ].to_dict()

        with st.spinner("最適配置を計算中..."):
            layout, status = solve_layout(
                apps=st.session_state.apps_models,
                weights=weights_dict,
                rows=st.session_state.layout_rows,
                cols=st.session_state.layout_cols,
                dock_size=st.session_state.dock_size,
                color_penalty_val=color_penalty_input,
            )

        if status == "Optimal":
            st.success("最適配置が完了しました！")
            layout_css = Path(f"{get_src_root()}/assets/layout.css").read_text(
                encoding="utf-8"
            )
            display_dynamic_layout_ui(
                layout,
                layout_css,
                st.session_state.layout_rows,
                st.session_state.layout_cols,
                st.session_state.dock_size,
            )
        else:
            st.error(f"最適解が見つかりませんでした (ステータス: {status})。")
    else:
        st.info(
            "サイドバーでパラメータを調整し、「最適化を実行」ボタンを押してください。"
        )


if __name__ == "__main__":
    app_view_optimize()
