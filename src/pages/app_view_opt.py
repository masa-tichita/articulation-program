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
def display_dynamic_layout_ui(layout_data, style: str, rows: int, cols: int, dock_size: int):
    # (この関数は変更なし)
    num_main_locations = rows * cols
    main_screen_items = ""
    for loc_id in range(1, num_main_locations + 1):
        item = layout_data.get(loc_id)
        if item:
            emoji = "📱"
            if any(x in item.name for x in ["カメラ", "写真"]): emoji = "🖼️"
            if any(x in item.name for x in ["Maps", "乗換"]): emoji = "🗺️"
            main_screen_items += f'<div class="app-icon" style="background-color: {item.color};"><span>{emoji}</span>{item.name}</div>'
        else:
            main_screen_items += '<div class="empty-slot"></div>'

    dock_items = ""
    for loc_id in range(num_main_locations + 1, num_main_locations + dock_size + 1):
        item = layout_data.get(loc_id)
        if item:
            emoji = "📱"
            if any(x in item.name for x in ["LINE", "Discord", "Slack"]): emoji = "💬"
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

# --- データ処理関数 ---
def load_and_validate_df(uploader_key, required_cols, dtype_map=None):
    uploaded_file = st.file_uploader(
        "CSV/Excel", type=["csv", "xlsx", "xls"], key=uploader_key, label_visibility="collapsed"
    )
    if uploaded_file is None:
        return None
    
    try:
        if uploaded_file.name.endswith('.csv'):
            try:
                df = pd.read_csv(uploaded_file, encoding='utf-8')
            except UnicodeDecodeError:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding='cp932')
        else:
            df = pd.read_excel(uploaded_file)

        if not all(col in df.columns for col in required_cols):
            st.error(f"ファイルのカラムが不正です。必須: {required_cols}, 検出: {list(df.columns)}")
            return None
        
        if dtype_map:
            df = df.astype(dtype_map)
        return df[required_cols]

    except Exception as e:
        st.error(f"ファイル読み込みエラー: {e}")
        return None

# --- 状態管理 ---
def update_weights_based_on_layout():
    rows, cols, dock = st.session_state.layout_rows, st.session_state.layout_cols, st.session_state.dock_size
    total_locations = rows * cols + dock
    
    current_weights_size = len(st.session_state.get("weights_df", []))
    if total_locations != current_weights_size:
        new_weights = {i: 10 for i in range(1, total_locations + 1)}
        st.session_state.weights_df = pd.DataFrame([{'location': k, 'weight': v} for k, v in new_weights.items()])

def initialize_session_state():
    if "current_time" not in st.session_state: st.session_state.current_time = datetime.now().strftime("%-H:%M")
    if "layout_rows" not in st.session_state: st.session_state.layout_rows = 4
    if "layout_cols" not in st.session_state: st.session_state.layout_cols = 8
    if "dock_size" not in st.session_state: st.session_state.dock_size = 6

    if "apps_df" not in st.session_state:
        st.session_state.apps_df = AppData.to_df(AppData.from_mapping(INITIAL_APPS_DATA))

    if "weights_df" not in st.session_state:
        update_weights_based_on_layout()

# --- サイドバーUI ---
def setup_sidebar():
    st.sidebar.header("設定")

    with st.sidebar.expander("📐 レイアウト設定", expanded=True):
        st.number_input("行数", 1, 10, key="layout_rows", on_change=update_weights_based_on_layout)
        st.number_input("列数", 1, 12, key="layout_cols", on_change=update_weights_based_on_layout)
        st.number_input("Dock数", 1, 15, key="dock_size", on_change=update_weights_based_on_layout)

    color_penalty = st.sidebar.slider("色のペナルティ", 0, 100, 0)

    with st.sidebar.expander("📋 アプリ一覧", expanded=False):
        st.markdown("**手動編集**")
        edited_apps_df = st.data_editor(
            st.session_state.apps_df, num_rows="dynamic", key="apps_editor",
            column_config={"name": "アプリ名", "usage": "使用回数", "color": "色"}
        )
        if st.button("手動編集を反映"):
            st.session_state.apps_df = edited_apps_df
            st.success("アプリ一覧を更新しました。")

        st.markdown("**ファイルから読込**")
        new_apps_df = load_and_validate_df("apps_uploader", ["name", "usage", "color"])
        if new_apps_df is not None and st.button("ファイル内容を反映", key="apply_apps_file"):
            st.session_state.apps_df = new_apps_df
            st.success("アプリ一覧をファイルから更新しました。")
            st.rerun()

    with st.sidebar.expander("🏋️ 重み", expanded=False):
        st.markdown("**手動編集**")
        editor_key = f"weights_editor_{len(st.session_state.weights_df)}"
        edited_weights_df = st.data_editor(
            st.session_state.weights_df, num_rows="dynamic", key=editor_key,
            column_config={"location": "ロケーション番号", "weight": "重み"}
        )
        if st.button("手動編集を反映", key="apply_weights_manual"):
            st.session_state.weights_df = edited_weights_df
            st.success("重みを更新しました。")

        st.markdown("**ファイルから読込**")
        new_weights_df = load_and_validate_df(
            "weights_uploader", ["location", "weight"], {"location": int, "weight": int}
        )
        if new_weights_df is not None and st.button("ファイル内容を反映", key="apply_weights_file"):
            st.session_state.weights_df = new_weights_df
            st.success("重みをファイルから更新しました。")
            st.rerun()
            
    return color_penalty

# --- メイン処理 ---
def app_view_optimize():
    st.set_page_config(page_title="アプリ配置最適化", layout="wide")
    titles_en_to_ja()
    st.title("📱 アプリ配置最適化")
    
    initialize_session_state()
    color_penalty_input = setup_sidebar()

    if st.sidebar.button("最適化を実行", type="primary"):
        try:
            # nameが空(NA)の行を削除し、データを検証・変換する
            valid_apps_df = st.session_state.apps_df.dropna(subset=['name'])
            app_records = valid_apps_df.to_dict('records')
            apps_models = [AppData.model_validate(rec) for rec in app_records]

            # 重みデータも同様に検証
            valid_weights_df = st.session_state.weights_df.dropna()
            weights_dict = valid_weights_df.set_index('location')['weight'].to_dict()

            if not apps_models:
                st.warning("最適化対象のアプリがありません。アプリ一覧を確認してください。")
                st.stop()

            # アプリ数が配置場所の数を超えていないかチェック
            total_locations = st.session_state.layout_rows * st.session_state.layout_cols + st.session_state.dock_size
            if len(apps_models) > total_locations:
                st.error(f"アプリの数({len(apps_models)})が配置場所の数({total_locations})を超えています。レイアウト設定を調整するか、アプリの数を減らしてください。")
                st.stop()

        except Exception as e:
            st.error(f"データ検証エラー: {e}")
            st.stop()
        
        with st.spinner("最適配置を計算中..."):
            layout, status = solve_layout(
                apps=apps_models, weights=weights_dict,
                rows=st.session_state.layout_rows, cols=st.session_state.layout_cols,
                dock_size=st.session_state.dock_size, color_penalty_val=color_penalty_input,
            )

        if status == "Optimal":
            st.success("最適配置が完了しました！")
            layout_css = Path(f"{get_src_root()}/assets/layout.css").read_text(encoding="utf-8")
            display_dynamic_layout_ui(
                layout, layout_css, st.session_state.layout_rows, 
                st.session_state.layout_cols, st.session_state.dock_size
            )
        else:
            st.error(f"最適解が見つかりませんでした (ステータス: {status})。")
    else:
        st.info("サイドバーでパラメータを調整し、「最適化を実行」ボタンを押してください。")

if __name__ == "__main__":
    app_view_optimize()