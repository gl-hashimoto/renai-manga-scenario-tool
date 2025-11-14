import streamlit as st
import anthropic
import os
from datetime import datetime
import json
from dotenv import load_dotenv, set_key

# バージョン情報
VERSION = "1.1.0"

# ページ設定
st.set_page_config(
    page_title="恋愛漫画シナリオ生成ツール | 愛カツ",
    page_icon="💘",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #FF69B4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #FF69B4;
        color: white;
        font-size: 1.2rem;
        font-weight: bold;
        padding: 0.75rem;
        border-radius: 10px;
    }
    .output-section {
        background-color: #FFF0F5;
        padding: 1.5rem;
        border-radius: 10px;
        margin-top: 1rem;
    }
    .scenario-title {
        font-size: 1.5rem;
        font-weight: bold;
        color: #FF1493;
        margin-bottom: 0.5rem;
    }
    /* バージョン表示 */
    .version-badge {
        display: inline-block;
        background-color: #e0e0e0;
        color: #555;
        font-size: 0.9rem;
        font-weight: normal;
        padding: 0.2rem 0.6rem;
        border-radius: 12px;
        margin-left: 1rem;
        vertical-align: middle;
    }
    /* 履歴リンクのスタイル */
    [data-testid="stSidebar"] button[kind="secondary"] {
        background-color: white !important;
        color: #333 !important;
        border: none !important;
        text-align: left !important;
        padding: 0.5rem 0.75rem !important;
        font-size: 0.9rem !important;
        font-weight: normal !important;
        border-radius: 4px !important;
        margin-bottom: 0.25rem !important;
    }
    [data-testid="stSidebar"] button[kind="secondary"]:hover {
        background-color: #f0f0f0 !important;
    }
</style>
""", unsafe_allow_html=True)

# マスタープロンプトを読み込む
def load_master_prompt():
    prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "恋愛漫画マスタープロンプト.md")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()

# シナリオの現実性チェック＆修正関数
def check_and_fix_scenario(api_key, scenario_draft):
    """
    生成されたシナリオの現実性をチェックし、問題があれば修正する
    """
    client = anthropic.Anthropic(api_key=api_key)

    check_prompt = f"""
あなたは恋愛漫画のシナリオ監修者です。以下の生成されたシナリオを評価し、必要に応じて修正してください。

【生成されたシナリオ】
{scenario_draft}

以下の観点でチェックし、問題があれば修正してください：

1. **現実性**: 実際にありえる状況か？（完全なファンタジーは避ける）
2. **共感性**: 読者が感情移入できるか？
3. **法的・倫理的問題**: 法律や倫理に反する内容ではないか？
4. **表現の適切性**: 過激すぎる・不適切な要素はないか？
5. **ストーリー展開の論理性**: 物語として成立するか？矛盾はないか？
6. **登場人物名**: A子、B男などの記号的な名前が使われているか？

【指示】
- 問題がない場合：元のシナリオをそのまま出力してください
- 問題がある場合：修正したシナリオを出力してください
- 修正理由や判定結果は出力しないでください
- シナリオの形式・構成は維持してください
- 修正は必要最小限に留めてください

【出力】
修正済みのシナリオをそのまま出力してください。
"""

    try:
        # チェック工程はHaikuモデルを使用してコスト削減
        message = client.messages.create(
            model="claude-haiku-3-5-20250313",
            max_tokens=8000,
            temperature=0.3,
            messages=[
                {"role": "user", "content": check_prompt}
            ]
        )

        return message.content[0].text
    except Exception as e:
        # エラーの場合は元のシナリオを返す
        return scenario_draft

# シナリオ生成関数
def generate_scenario(api_key, theme, story_format, tone, additional_notes=""):
    """
    Claude APIを使用してシナリオを生成
    """
    client = anthropic.Anthropic(api_key=api_key)

    master_prompt = load_master_prompt()

    # ユーザー入力を構造化
    user_prompt = f"""
以下の条件で恋愛漫画のシナリオを生成してください。

【形式】
{story_format}

【テーマ/ネタ】
{theme}

【トーン/雰囲気】
{tone}

【追加の要望】
{additional_notes if additional_notes else "特になし"}

上記の【シナリオ生成のための統合ナレッジ】と【出力形式】に従って、バズる恋愛漫画のシナリオを生成してください。
"""

    try:
        # プロンプトキャッシュを使用してコスト削減
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=8000,
            temperature=1.0,
            system=[
                {
                    "type": "text",
                    "text": master_prompt,
                    "cache_control": {"type": "ephemeral"}
                }
            ],
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )

        return message.content[0].text
    except Exception as e:
        return f"エラーが発生しました: {str(e)}"

# 履歴を保存
def save_history(theme, story_format, tone, result, additional_notes="", feasibility_check=""):
    history_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(history_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"scenario_{timestamp}.json"
    filepath = os.path.join(history_dir, filename)

    data = {
        "timestamp": datetime.now().isoformat(),
        "theme": theme,
        "story_format": story_format,
        "tone": tone,
        "additional_notes": additional_notes,
        "feasibility_check": feasibility_check,
        "result": result
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return filepath

# 履歴を読み込む
def load_history():
    history_dir = os.path.join(os.path.dirname(__file__), "output")
    if not os.path.exists(history_dir):
        return []

    history_files = sorted(
        [f for f in os.listdir(history_dir) if f.endswith('.json')],
        reverse=True
    )

    histories = []
    for filename in history_files[:10]:  # 最新10件
        filepath = os.path.join(history_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            histories.append(data)

    return histories

# APIキーを保存
def save_api_key(api_key):
    """
    APIキーを.envファイルに保存する
    """
    env_path = os.path.join(os.path.dirname(__file__), ".env")

    try:
        # .envファイルが存在しない場合は作成
        if not os.path.exists(env_path):
            with open(env_path, "w", encoding="utf-8") as f:
                f.write(f"ANTHROPIC_API_KEY={api_key}\n")
        else:
            # 既存の.envファイルを更新
            set_key(env_path, "ANTHROPIC_API_KEY", api_key)

        return True
    except Exception as e:
        st.error(f"APIキーの保存に失敗しました: {str(e)}")
        return False

# メイン画面
def main():
    # .envファイルを読み込む
    load_dotenv()

    # ヘッダー
    st.markdown(f'<div class="main-header">💘 恋愛漫画シナリオ生成ツール <span class="version-badge">v{VERSION}</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">バズる恋愛漫画を1日10本生成！｜愛カツ専用ツール</div>', unsafe_allow_html=True)

    # サイドバー設定
    with st.sidebar:
        st.header("⚙️ 設定")

        # APIキー設定
        api_key = st.text_input(
            "Anthropic API Key",
            type="password",
            value=os.getenv("ANTHROPIC_API_KEY", ""),
            help="Claude APIキーを入力してください"
        )

        # APIキー保存ボタン
        if api_key:
            if st.button("💾 APIキーを保存", help="APIキーを.envファイルに保存します"):
                if save_api_key(api_key):
                    st.success("✅ APIキーを保存しました！")
                    st.info("次回起動時から自動的に読み込まれます")

        st.divider()

        # 形式選択
        st.subheader("📖 漫画の形式")
        story_format = st.selectbox(
            "形式を選択",
            [
                "1話完結（10ページ）",
                "前後編2話完結（各10ページ＝計20ページ）",
                "10話連載（各10ページ＝計100ページ）"
            ]
        )

        # トーン選択
        st.subheader("🎭 トーン/雰囲気")
        tone = st.selectbox(
            "雰囲気を選択",
            [
                "甘々・胸キュン全開",
                "切ない・号泣系",
                "コメディ・笑える恋愛",
                "ドロドロ・三角関係",
                "純愛・初恋系",
                "大人の恋愛・切実",
                "すれ違い・じれったい",
                "逆転・スカッと系"
            ]
        )

        st.divider()

        # 履歴表示
        st.subheader("📚 生成履歴")
        if st.button("履歴を更新", type="primary"):
            st.rerun()

        histories = load_history()
        if histories:
            for i, hist in enumerate(histories, 1):
                # テキストリンク形式で表示（20文字制限）
                theme_preview = hist['theme'][:20]
                if st.button(theme_preview, key=f"hist_link_{i}", type="secondary", use_container_width=False):
                    st.session_state.selected_history = hist
                    st.session_state.selected_history_index = i
                    st.rerun()
        else:
            st.info("まだ生成履歴がありません")

    # メインコンテンツ
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("✍️ テーマ/ネタを入力")
        theme = st.text_area(
            "作りたい漫画のテーマやネタ、シチュエーションなどを自由に入力してください",
            height=200,
            placeholder="例：\n・冷たい上司が私にだけ優しい理由\n・10年ぶりに再会した初恋の人\n・幼馴染に突然告白されたけど...\n・婚約破棄されたのに逆にモテ始めた\n・片思いの相手が実は...",
            help="具体的であればあるほど、良いシナリオが生成されます"
        )

        additional_notes = st.text_area(
            "追加の要望（オプション）",
            height=100,
            placeholder="例：\n・主人公は25歳のOL\n・相手役はクール系の年上上司\n・壁ドンシーンを入れてほしい\n・最後はハッピーエンドで"
        )

    with col2:
        st.header("💡 テーマのヒント")
        st.info("""
**人気のテーマ例：**

🏢 **職場恋愛**
- 上司×部下
- 同期の仲間
- ライバル関係

🏫 **学園恋愛**
- 先輩×後輩
- 幼馴染
- クラスメイト

💔 **切ない系**
- 再会
- すれ違い
- 片思い

✨ **王道胸キュン**
- 一目惚れ
- 偽装恋愛
- 三角関係
        """)

    # 生成ボタン
    st.divider()

    if not api_key:
        st.warning("⚠️ サイドバーでAnthropic API Keyを入力してください")
    elif not theme:
        st.warning("⚠️ テーマ/ネタを入力してください")
    else:
        if st.button("🎬 シナリオを生成する", type="primary"):
            with st.spinner("シナリオを生成中... 少々お待ちください💭"):
                # ステップ1: シナリオ生成
                with st.spinner("📝 シナリオを作成中..."):
                    draft_scenario = generate_scenario(api_key, theme, story_format, tone, additional_notes)

                # ステップ2: 現実性チェック＆修正（内部処理、ユーザーには見せない）
                with st.spinner("🔍 シナリオを検証・最適化中..."):
                    final_scenario = check_and_fix_scenario(api_key, draft_scenario)

                # セッションステートに保存
                st.session_state.result = final_scenario
                st.session_state.theme = theme
                st.session_state.story_format = story_format
                st.session_state.tone = tone

                # 履歴に保存（現実性チェックは内部処理なので保存しない）
                save_history(
                    theme,
                    story_format,
                    tone,
                    final_scenario,
                    additional_notes=additional_notes,
                    feasibility_check=""  # 空文字列にする
                )

                st.rerun()

    # 右カラム: 結果表示（新規生成 or 履歴選択）
    if "selected_history" in st.session_state:
        # 履歴が選択された場合
        st.divider()
        hist = st.session_state.selected_history
        st.header(f"📝 履歴 #{st.session_state.selected_history_index}")

        # 履歴情報の表示
        st.info(f"""
**テーマ**: {hist['theme']}
**形式**: {hist['story_format']}
**トーン**: {hist['tone']}
**日時**: {hist['timestamp'][:19]}
        """)

        if hist.get('additional_notes'):
            with st.expander("📌 追加の要望"):
                st.write(hist['additional_notes'])

        # シナリオ表示
        st.markdown('<div class="output-section">', unsafe_allow_html=True)
        st.markdown(hist['result'])
        st.markdown('</div>', unsafe_allow_html=True)

        # ダウンロードボタン
        col1, col2, col3 = st.columns([1, 1, 2])

        timestamp_str = hist['timestamp'][:19].replace(":", "").replace("-", "").replace(" ", "_")

        # 完全な内容を作成
        full_content = f"""# 恋愛漫画シナリオ

## 生成情報
- 日時: {hist['timestamp'][:19]}
- 形式: {hist['story_format']}
- トーン: {hist['tone']}

## テーマ
{hist['theme']}

"""
        if hist.get('additional_notes'):
            full_content += f"""## 追加の要望
{hist['additional_notes']}

"""

        full_content += f"""## 生成されたシナリオ

{hist['result']}
"""

        with col1:
            st.download_button(
                label="📄 TXT",
                data=full_content,
                file_name=f"scenario_{timestamp_str}.txt",
                mime="text/plain",
                key="hist_txt_dl"
            )

        with col2:
            st.download_button(
                label="📋 MD",
                data=full_content,
                file_name=f"scenario_{timestamp_str}.md",
                mime="text/markdown",
                key="hist_md_dl"
            )

        with col3:
            if st.button("✖️ 閉じる"):
                del st.session_state.selected_history
                del st.session_state.selected_history_index
                st.rerun()

    elif "result" in st.session_state:
        # 新規生成された場合
        st.divider()
        st.header("📝 生成されたシナリオ")

        # 結果表示エリア
        st.markdown('<div class="output-section">', unsafe_allow_html=True)
        st.markdown(st.session_state.result)
        st.markdown('</div>', unsafe_allow_html=True)

        # ダウンロードボタン
        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            # テキストファイルダウンロード
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"scenario_{timestamp}.txt"

            st.download_button(
                label="📄 テキストでダウンロード",
                data=st.session_state.result,
                file_name=filename,
                mime="text/plain"
            )

        with col2:
            # Markdownファイルダウンロード
            md_filename = f"scenario_{timestamp}.md"

            st.download_button(
                label="📋 Markdownでダウンロード",
                data=st.session_state.result,
                file_name=md_filename,
                mime="text/markdown"
            )

        with col3:
            if st.button("🔄 新しいシナリオを生成"):
                del st.session_state.result
                st.rerun()

if __name__ == "__main__":
    main()
