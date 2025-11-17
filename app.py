import streamlit as st
import anthropic
import os
from datetime import datetime
import json
import re
from dotenv import load_dotenv, set_key

# バージョン情報
VERSION = "2.0.0"
PROMPT_VERSION = "2.0"  # プロンプトバージョン（最適化版：639行→415行に削減）

# 文字数カウント関数
def count_characters(text):
    """
    シナリオの文字数を正確にカウント
    改行、記号（※、「」、『』、■など）、かぎ括弧を除いた純粋なテキスト文字のみカウント
    """
    # 改行を削除
    text = text.replace('\n', '').replace('\r', '')

    # 除外する記号・括弧を削除
    text = re.sub(r'[※「」『』■\(\)（）…！？!?〜～\s]', '', text)

    # 残った文字数をカウント
    return len(text)

# ページ設定
st.set_page_config(
    page_title="恋愛漫画シナリオ生成ツールv2 | 愛カツ",
    page_icon="💙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E90FF;
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
        background-color: #1E90FF;
        color: white;
        font-size: 1.2rem;
        font-weight: bold;
        padding: 0.75rem;
        border-radius: 10px;
    }
    .output-section {
        background-color: #E6F2FF;
        padding: 1.5rem;
        border-radius: 10px;
        margin-top: 1rem;
    }
    .scenario-title {
        font-size: 1.5rem;
        font-weight: bold;
        color: #1E90FF;
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

# プロンプトバージョン管理関数
def save_prompt_version(version, description=""):
    """現在のプロンプトを新しいバージョンとして保存"""
    versions_dir = os.path.join(os.path.dirname(__file__), "prompts", "versions")
    os.makedirs(versions_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    version_filename = f"v{version}_{timestamp}.md"
    version_path = os.path.join(versions_dir, version_filename)

    # 現在のプロンプトをコピー
    current_prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "恋愛漫画マスタープロンプト.md")
    with open(current_prompt_path, "r", encoding="utf-8") as f:
        prompt_content = f.read()

    # バージョン情報を先頭に追加
    version_info = f"""# プロンプトバージョン: v{version}
# 保存日時: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
# 説明: {description if description else "バージョン保存"}

---

{prompt_content}
"""

    with open(version_path, "w", encoding="utf-8") as f:
        f.write(version_info)

    return version_filename

def get_available_prompt_versions():
    """利用可能なプロンプトバージョン一覧を取得"""
    versions_dir = os.path.join(os.path.dirname(__file__), "prompts", "versions")
    if not os.path.exists(versions_dir):
        return []

    version_files = [f for f in os.listdir(versions_dir) if f.endswith('.md')]
    version_files.sort(reverse=True)  # 新しい順
    return version_files

def load_prompt_version(version_filename):
    """指定したバージョンのプロンプトを読み込む"""
    version_path = os.path.join(os.path.dirname(__file__), "prompts", "versions", version_filename)
    with open(version_path, "r", encoding="utf-8") as f:
        content = f.read()

    # バージョン情報部分を除去（---以降が実際のプロンプト）
    if "---" in content:
        return content.split("---", 1)[1].strip()
    return content

def restore_prompt_version(version_filename):
    """指定したバージョンのプロンプトを現在のプロンプトとして復元"""
    prompt_content = load_prompt_version(version_filename)
    current_prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "恋愛漫画マスタープロンプト.md")

    with open(current_prompt_path, "w", encoding="utf-8") as f:
        f.write(prompt_content)

    return True

# マスタープロンプトを読み込む
def load_master_prompt():
    prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "恋愛漫画マスタープロンプト.md")
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()

# シナリオ自動チェック＆リライト関数
def check_and_fix_scenario(api_key, scenario_draft):
    """
    生成されたシナリオを自動でチェックし、品質向上のためにリライトする
    """
    client = anthropic.Anthropic(api_key=api_key)

    rewrite_prompt = f"""
以下のシナリオを、チェック基準に基づいて 客観的に自己評価 → 問題点抽出 → 最適な形にリライト してください。
トーンは漫画のネーム用のシナリオとして、テンポよく、読者にとって理解しやすく、感情移入しやすい形に整えてください。

【元のシナリオ】
{scenario_draft}

【ステップ1：問題点の抽出】※内部処理のみ、出力不要

以下のチェック基準に照らして、改善すべき点を把握：

▼ チェック基準
1. ストーリーのつじつま
   - 設定の矛盾はないか
   - 行動の必然性はあるか
   - 状況説明は明瞭か
   - 現実味はあるか（倫理観、違法行為、NG描写）

2. セリフと感情の自然さ
   - 会話の流れは自然か
   - 年齢・性格に合った話し方か
   - ポエム調・文学調を避けているか
   - 共感を生む感情描写になっているか

3. 話のまとまり・伏線回収
   - 伏線の貼り方と回収
   - 展開テンポ
   - ラストの納得感

4. 追加基準
   - 冒頭5コマで「何の話か」理解できるか
   - 主人公の魅力が一言で言えるか
   - 感情のアップダウンが設計されているか
   - ラストに読後の"ご褒美"があるか

【ステップ2：シナリオの完全リライト版を生成】

以下の条件を守って、最適化したシナリオを出力してください。

▼ リライト条件
- 1話10〜14Pのショート漫画を想定（前後編形式）
- テンポの良いネーム用シナリオ
- **【最重要】前後編でそれぞれ完結しつつ、後編を絶対に読みたくなる構造**
  - 前編 = 問題提示 + 小解決（満足度60%）
  - 後編 = 真相 + 本質的解決（満足度100%）
  - 前編ラストに必ず「強烈な引き」を入れる（裏の事実／新キャラ登場／本当の問題／味方の違和感／深刻な予兆）
  - 前編最後に後編タイトルを表示（例：`後編『〜』`）
- **1ページ=ひとつの感情変化**を基本にする
- キャラの行動と感情が自然
- 読者（30〜45歳女性）が共感
- セリフは短く、説明過多を避ける
- ナレーション/モノローグ/描写のメリハリ
- クライマックスに向けて段階的に盛り上げる
- 伏線は自然に回収
- 後編ラストは爽快感・解放感（ポエム調禁止）
- NG描写（鬱・殺人・宗教・差別・過度な暴力）なし
- **文字数制限【厳守】**：
  - 前編：最大600文字以内（推奨400〜600文字）
  - 後編：最大600文字以内（推奨400〜600文字）
  - 合計：最大1200文字以内（推奨800〜1200文字）
  - 絶対に上限を超えないこと
- カウント方法：改行、※、「」、『』、■、（）、…、！、？、〜、スペースを除く
- **制限内で面白さ最大化**：冗長な表現を削り、簡潔かつインパクトのある表現に

【重要】出力はリライトしたシナリオのみ。分析や評価コメントは不要です。
元のシナリオのフォーマット（【登場人物】から始まる形式）を維持してください。
"""

    try:
        # リライト工程もHaikuで実施（コスト削減）
        message = client.messages.create(
            model="claude-haiku-3-5-20250313",
            max_tokens=8000,
            temperature=0.5,
            messages=[
                {"role": "user", "content": rewrite_prompt}
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
    # 文字数ガイドライン設定
    if "前後編" in story_format:
        char_limit = """
【必須】文字数制限：
- **前編：最大600文字以内（推奨400〜600文字）**
- **後編：最大600文字以内（推奨400〜600文字）**
- **合計：最大1200文字以内（推奨800〜1200文字）**
- **絶対に上限を超えないこと**

【厳密】文字数カウント方法：
- 改行、記号（※、「」、『』、■、（）、…、！、？、〜など）、スペースを除いた純粋なテキスト文字のみカウント
- 登場人物セクションは文字数に含めない（シナリオ本文のみカウント）
- カウント例：
  - `A子「こんにちは」※笑顔` → カウント「A子こんにちは笑顔」= 9文字
  - `※夜、仕事から帰宅したA子` → カウント「夜仕事から帰宅したA子」= 12文字

【重要】面白さと制限のバランス：
- 制限内で最高の面白さを実現すること
- 冗長な表現は徹底的に削る
- ストーリーの面白さ、キャラクターの魅力、感情の盛り上がりを大切に
- 簡潔かつインパクトのある表現を心がける

【必須】シナリオ出力時の文字数表記：
- シナリオ本文の最後に、必ず以下の形式で実際の文字数を明記してください
- 例：`文字数：前編482文字 / 後編518文字 / 合計1000文字`
- 出力前に必ず文字数を実測し、制限内に収めること
"""
    else:
        char_limit = ""

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
{char_limit}
上記の【シナリオ生成のための統合ナレッジ】と【出力形式】に従って、バズる恋愛漫画のシナリオを生成してください。
"""

    try:
        # プロンプトキャッシュを使用してコスト削減
        # temperature: 文字数制限など具体的な制約がある場合は低めに設定
        message = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=8000,
            temperature=0.7,  # 1.0から0.7に変更（より指示に従いやすく）
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
def save_history(theme, story_format, tone, result, additional_notes="", feasibility_check="", prompt_version=""):
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
        "prompt_version": prompt_version,  # プロンプトバージョンを追加
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
    st.markdown(f'<div class="main-header">💙 恋愛漫画シナリオ生成ツールv2 <span class="version-badge">v{VERSION}</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="sub-header">前後編完全最適化版（プロンプトv{PROMPT_VERSION}）｜愛カツ専用ツール</div>', unsafe_allow_html=True)

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

        # 形式は前後編のみに固定（プロンプトv2.0に対応）
        story_format = "前後編2話完結（前編5〜7ページ・後編5〜7ページ）"
        st.info(f"📖 **形式**: {story_format}")

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

        st.divider()

        # プロンプトバージョン管理
        st.subheader("🔧 プロンプトバージョン管理")
        st.caption(f"現在のバージョン: v{PROMPT_VERSION}")

        # 利用可能なバージョン一覧
        available_versions = get_available_prompt_versions()

        if available_versions:
            with st.expander("保存されたバージョン一覧"):
                for version_file in available_versions:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.text(version_file.replace('.md', ''))
                    with col2:
                        if st.button("復元", key=f"restore_{version_file}"):
                            restore_prompt_version(version_file)
                            st.success(f"✅ {version_file}に復元しました！")
                            st.info("アプリを再起動すると反映されます")
                            st.rerun()
        else:
            st.info("保存されたバージョンはありません")

        st.divider()

        # ツール情報
        with st.expander("ℹ️ ツール情報"):
            st.markdown(f"""
**バージョン情報**
- アプリバージョン: v{VERSION}
- プロンプトバージョン: v{PROMPT_VERSION}

**v2.0の主な変更点**
- ✅ 前後編構成に完全最適化
- ✅ プロンプト35%削減（639行→415行）
- ✅ 文字数制限の厳格化（最大600/600/1200文字）
- ✅ 不要な形式（1話完結・10話連載）を削除
- ✅ バズる要素と胸キュンに集中
- ✅ 自動文字数カウント機能追加

**生成時間**
- 初稿生成：約30〜60秒
- 自動リライト：約20〜40秒
- 合計：約1〜2分
            """)

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
                with st.spinner("📝 シナリオ初稿を作成中..."):
                    draft_scenario = generate_scenario(api_key, theme, story_format, tone, additional_notes)

                # ステップ2: 自動チェック＆リライト
                with st.spinner("✨ 品質チェック＆自動リライト中..."):
                    final_scenario = check_and_fix_scenario(api_key, draft_scenario)

                # セッションステートに保存
                st.session_state.result = final_scenario
                st.session_state.theme = theme
                st.session_state.story_format = story_format
                st.session_state.tone = tone

                # 履歴に保存（プロンプトバージョンも記録）
                save_history(
                    theme,
                    story_format,
                    tone,
                    final_scenario,
                    additional_notes=additional_notes,
                    feasibility_check="",  # 空文字列にする
                    prompt_version=PROMPT_VERSION  # プロンプトバージョンを記録
                )

                st.rerun()

    # 右カラム: 結果表示（新規生成 or 履歴選択）
    if "selected_history" in st.session_state:
        # 履歴が選択された場合
        st.divider()
        hist = st.session_state.selected_history
        st.header(f"📝 履歴 #{st.session_state.selected_history_index}")

        # 履歴情報の表示
        prompt_ver = hist.get('prompt_version', '不明')
        st.info(f"""
**テーマ**: {hist['theme']}
**形式**: {hist['story_format']}
**トーン**: {hist['tone']}
**日時**: {hist['timestamp'][:19]}
**プロンプトバージョン**: v{prompt_ver}
        """)

        if hist.get('additional_notes'):
            with st.expander("📌 追加の要望"):
                st.write(hist['additional_notes'])

        # シナリオ表示
        st.markdown('<div class="output-section">', unsafe_allow_html=True)
        st.markdown(hist['result'])
        st.markdown('</div>', unsafe_allow_html=True)

        # 文字数カウント表示（前後編の場合）
        if "前後編" in hist['story_format']:
            scenario_text = hist['result']
            # 登場人物セクションを除外
            if "■前編" in scenario_text:
                scenario_only = scenario_text.split("■前編", 1)[1] if "■前編" in scenario_text else scenario_text

                # 前編と後編を分割
                if "■後編" in scenario_only:
                    parts = scenario_only.split("■後編")
                    zenpen_text = parts[0]
                    kohen_text = parts[1] if len(parts) > 1 else ""

                    zenpen_count = count_characters(zenpen_text)
                    kohen_count = count_characters(kohen_text)
                    total_count = zenpen_count + kohen_count

                    # 文字数表示
                    st.info(f"""
**📊 実測文字数**（改行・記号・括弧を除く）
前編: {zenpen_count}文字 / 後編: {kohen_count}文字 / 合計: {total_count}文字
                    """)

                    # 文字数オーバーの警告
                    if zenpen_count > 600 or kohen_count > 600 or total_count > 1200:
                        st.warning("⚠️ 文字数が制限を超えています")
                    elif total_count < 800:
                        st.info("ℹ️ 推奨文字数（800-1200文字）より少なめです")

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

        # 文字数カウント表示（前後編の場合）
        if "前後編" in st.session_state.story_format:
            scenario_text = st.session_state.result
            # 登場人物セクションを除外
            if "■前編" in scenario_text:
                scenario_only = scenario_text.split("■前編", 1)[1] if "■前編" in scenario_text else scenario_text

                # 前編と後編を分割
                if "■後編" in scenario_only:
                    parts = scenario_only.split("■後編")
                    zenpen_text = parts[0]
                    kohen_text = parts[1] if len(parts) > 1 else ""

                    zenpen_count = count_characters(zenpen_text)
                    kohen_count = count_characters(kohen_text)
                    total_count = zenpen_count + kohen_count

                    # 文字数表示
                    st.info(f"""
**📊 実測文字数**（改行・記号・括弧を除く）
前編: {zenpen_count}文字 / 後編: {kohen_count}文字 / 合計: {total_count}文字
                    """)

                    # 文字数オーバーの警告
                    if zenpen_count > 600 or kohen_count > 600 or total_count > 1200:
                        st.warning("⚠️ 文字数が制限を超えています")
                    elif total_count < 800:
                        st.info("ℹ️ 推奨文字数（800-1200文字）より少なめです")

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
