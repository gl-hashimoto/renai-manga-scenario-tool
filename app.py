import streamlit as st
import anthropic
import os
from datetime import datetime
import json
import re
import time
import traceback
from dotenv import load_dotenv, set_key

# バージョン情報
VERSION = "2.2.0"  # 視点変更機能・文字数制限強化版
PROMPT_VERSION = "2.0"  # プロンプトバージョン（最適化版：639行→415行に削減）

# ============================================================================
# 文字数カウント関数
# ============================================================================

def count_characters(text):
    """
    シナリオの文字数を正確にカウント
    
    Args:
        text: カウント対象のテキスト
        
    Returns:
        文字数（改行、記号、括弧を除いた純粋なテキスト文字のみ）
    
    文字数のカウント方法:
    - 改行、記号（※、「」、『』、■など）、かぎ括弧を除いた純粋なテキスト文字のみカウント
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

# カスタムCSS（最小限）
st.markdown("""
<style>
    /* メインヘッダー */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #333;
        text-align: center;
        margin-bottom: 1rem;
        padding: 1rem;
    }
    
    /* サブヘッダー */
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* バージョン表示 */
    .version-badge {
        display: inline-block;
        background: #f0f0f0;
        color: #333;
        font-size: 0.9rem;
        font-weight: normal;
        padding: 0.3rem 0.8rem;
        border-radius: 5px;
        margin-left: 1rem;
        vertical-align: middle;
    }
    
    /* 出力セクション */
    .output-section {
        background: #f9f9f9;
        padding: 1rem;
        margin-top: 1rem;
        border: 1px solid #e0e0e0;
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

# エンディングパターン検出関数
def detect_ending_pattern(scenario_text):
    """
    よくあるエンディングパターンを検出
    
    Returns:
        (is_pattern, pattern_name): パターンに該当するか、パターン名
    """
    # よくあるパターンのリスト
    patterns = [
        (r"夕暮れ.*[歩散]", "夕暮れ散歩パターン"),
        (r"窓.*[光差し込].*[前向き|これから|スタート]", "窓からの光と前向きな言葉パターン"),
        (r"桜.*下.*[告白|会]", "桜の下での告白パターン"),
        (r"雨.*[抱き合|抱く]", "雨の中で抱き合うパターン"),
        (r"海辺.*[シルエット|2人]", "海辺で2人のシルエットパターン"),
        (r"コーヒー.*[再会|会]", "コーヒーショップでの再会パターン"),
    ]
    
    for pattern, name in patterns:
        if re.search(pattern, scenario_text, re.IGNORECASE | re.DOTALL):
            return True, name
    
    return False, None

# シナリオ自動チェック＆リライト関数
def shorten_scenario(api_key, scenario_text, target_chars=1000):
    """
    シナリオを短縮する（文字数制限オーバー時）
    
    Args:
        api_key: Anthropic APIキー
        scenario_text: 短縮するシナリオ
        target_chars: 目標文字数（デフォルト1000文字）
    
    Returns:
        短縮されたシナリオ
    """
    client = anthropic.Anthropic(api_key=api_key)
    
    shorten_prompt = f"""
以下のシナリオの文字数が制限を超えています。
面白さやストーリーの内容を維持しながら、文字数を削減してください。

【目標文字数】
- 前編：最大500文字以内
- 後編：最大500文字以内
- 合計：最大{target_chars}文字以内

【短縮の方法】
- 冗長な表現を削除
- 説明過多な部分を簡潔に
- セリフや演出指示を効果的に使用
- 1ページ=ひとつの感情変化を維持
- ストーリーの面白さ、キャラクターの魅力、感情の盛り上がりは維持

【元のシナリオ】
{scenario_text}

【重要】
- 文字数を削減する際、内容の質を落とさないこと
- 簡潔かつインパクトのある表現に変更すること
- シナリオ本文の最後に、実際の文字数を明記すること（例：`文字数：前編482文字 / 後編518文字 / 合計1000文字`）
- 出力はリライトしたシナリオのみ（分析や評価コメントは不要）
"""
    
    try:
        message = client.messages.create(
            model="claude-haiku-3-5-20250313",
            max_tokens=8000,
            temperature=0.3,  # 短縮は低温度で確実に
            messages=[
                {"role": "user", "content": shorten_prompt}
            ]
        )
        return message.content[0].text
    except Exception as e:
        return scenario_text  # エラー時は元のシナリオを返す

def enforce_char_limit(api_key, scenario_text, max_retries=3):
    """
    文字数制限を強制する（オーバー時は自動短縮）
    
    Args:
        api_key: Anthropic APIキー
        scenario_text: チェックするシナリオ
        max_retries: 最大リトライ回数
    
    Returns:
        文字数制限内に収まったシナリオ
    """
    # 前編と後編を分割
    if "■前編" in scenario_text:
        scenario_only = scenario_text.split("■前編", 1)[1] if "■前編" in scenario_text else scenario_text
        if "■後編" in scenario_only:
            parts = scenario_only.split("■後編")
            zenpen_text = parts[0]
            kohen_text = parts[1] if len(parts) > 1 else ""
            
            zenpen_count = count_characters(zenpen_text)
            kohen_count = count_characters(kohen_text)
            total_count = zenpen_count + kohen_count
            
            # 文字数チェック
            if zenpen_count <= 500 and kohen_count <= 500 and total_count <= 1000:
                return scenario_text  # 制限内ならそのまま返す
            
            # オーバーしている場合、短縮を試行
            for i in range(max_retries):
                scenario_text = shorten_scenario(api_key, scenario_text, target_chars=1000)
                
                # 再チェック
                if "■前編" in scenario_text:
                    scenario_only = scenario_text.split("■前編", 1)[1] if "■前編" in scenario_text else scenario_text
                    if "■後編" in scenario_only:
                        parts = scenario_only.split("■後編")
                        zenpen_text = parts[0]
                        kohen_text = parts[1] if len(parts) > 1 else ""
                        
                        zenpen_count = count_characters(zenpen_text)
                        kohen_count = count_characters(kohen_text)
                        total_count = zenpen_count + kohen_count
                        
                        if zenpen_count <= 500 and kohen_count <= 500 and total_count <= 1000:
                            return scenario_text  # 制限内になったら返す
    
    return scenario_text  # 最大リトライ回数に達した場合も返す

def check_and_fix_scenario(api_key, scenario_draft, viewpoint="主人公目線（デフォルト）"):
    """
    生成されたシナリオを自動でチェックし、品質向上のためにリライトする
    
    Args:
        api_key: Anthropic APIキー
        scenario_draft: リライト前のシナリオ
        viewpoint: 視点の選択（リライト時にも視点を維持するため）
    """
    client = anthropic.Anthropic(api_key=api_key)
    
    # パターン検出
    is_pattern, pattern_name = detect_ending_pattern(scenario_draft)
    
    # 視点維持の指示
    viewpoint_maintain = ""
    if viewpoint != "主人公目線（デフォルト）":
        viewpoint_maintain = f"""
【視点の維持】
リライト時も、「{viewpoint}」の視点を維持してください。
視点が変わらないよう、注意してください。
"""

    # パターン検出時の追加指示
    pattern_warning = ""
    if is_pattern:
        pattern_warning = f"""
⚠️ **パターン検出**: エンディングに「{pattern_name}」が検出されました。
以下の点を必ず守ってリライトしてください：
- このパターンを避け、バリエーションのあるエンディングに変更する
- ただし、面白さ・感動・共感ポイントは維持する
- 感情の回収、印象に残る要素、未来への示唆を含める
- 日常の何気ないシーンで、自然な会話や行動で締める
"""

    rewrite_prompt = f"""
以下のシナリオを、チェック基準に基づいて 客観的に自己評価 → 問題点抽出 → 最適な形にリライト してください。
トーンは漫画のネーム用のシナリオとして、テンポよく、読者にとって理解しやすく、感情移入しやすい形に整えてください。

{pattern_warning}
{viewpoint_maintain}

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

4. エンディングのパターン化チェック【重要】
   - よくあるパターン（夕暮れ散歩、窓からの光など）に該当していないか
   - バリエーションのあるエンディングになっているか
   - 面白さを保ちつつ、パターン化を避けられているか

5. テーマ/ネタへの忠実性【超重要】
   - 入力されたテーマ/ネタに記載されている内容のみを使用しているか
   - テーマに記載されていない設定・情報・要素（警察、裁判所、会社、学校など）を追加していないか
   - テーマから大きく逸脱した展開になっていないか

6. 文字数と簡潔性【超重要】
   - 前編：500文字以内、後編：500文字以内、合計：1000文字以内に収まっているか
   - 物語を不必要に膨らませていないか
   - 簡潔でインパクトのある展開になっているか

7. 追加基準
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
- **エンディングのパターン化回避【重要】**：
  - よくあるパターン（夕暮れ散歩、窓からの光と前向きな言葉、桜の下での告白など）は絶対に避ける
  - 面白さ・感動・共感を保ちつつ、バリエーションのあるエンディングにする
  - 日常の何気ないシーンで、感情の回収、共感ポイント、インパクト、未来への示唆を含める
  - ポエム調・文学調は避け、自然な会話や行動で締める
- 後編ラストは爽快感・解放感（ポエム調禁止）
- NG描写（鬱・殺人・宗教・差別・過度な暴力）なし
- **文字数制限【より厳格に】**：
  - 前編：最大500文字以内（推奨400〜500文字）
  - 後編：最大500文字以内（推奨400〜500文字）
  - 合計：最大1000文字以内（推奨800〜1000文字）
  - 絶対に上限を超えないこと
  - 物語を膨らませすぎず、簡潔でインパクトのある展開を心がけること
- カウント方法：改行、※、「」、『』、■、（）、…、！、？、〜、スペースを除く
- **制限内で面白さ最大化**：冗長な表現を削り、簡潔かつインパクトのある表現に
- **テーマ/ネタへの忠実性【最重要】**：
  - 入力されたテーマ/ネタに記載されている内容のみを使用すること
  - テーマに記載されていない設定・情報・要素（警察、裁判所、会社、学校、病院など）は一切追加しない
  - テーマから大きく逸脱した展開は絶対に避けること

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

        rewritten_scenario = message.content[0].text
        
        # 文字数制限の強制実行
        final_scenario = enforce_char_limit(api_key, rewritten_scenario)
        
        return final_scenario
    except Exception as e:
        # エラーの場合は元のシナリオを返す
        return scenario_draft

# ============================================================================
# シナリオ生成関数
# ============================================================================

def load_viewpoint_prompt():
    """視点変更プロンプトを読み込む"""
    prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "視点変更プロンプト.md")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def generate_viewpoint_instruction(viewpoint, theme):
    """視点に応じたプロンプト指示を生成"""
    if viewpoint == "主人公目線（デフォルト）":
        return ""
    
    # カスタム視点の場合
    if viewpoint not in ["親友・友人目線", "第三者の視点", "体験談から自動変換（親友目線推奨）"]:
        # カスタム入力された視点
        return f"""
【視点変更指示：カスタム視点】
以下のテーマ/ネタを「{viewpoint}」のストーリーに変換してください。

視点変更のポイント：
- 指定された視点「{viewpoint}」でストーリーを語る
- その視点の人物の感情・思考・行動を中心に描写
- その視点から見た他の人物の様子を描写
- その視点の人物がどう感じたか、どう行動したかを明確に
- その視点の人物と他の登場人物の関係を明確に
- なぜその視点の人物が行動するのか、動機を明確に

ストーリーの内容は維持しつつ、視点のみを変更してください。
視点が一貫していること、自然な語り口であることを重視してください。
"""
    
    # 視点変更の指示を生成
    if viewpoint == "親友・友人目線":
        return """
【視点変更指示】
以下のテーマ/ネタを「親友・友人目線」のストーリーに変換してください。

視点変更のポイント：
- 体験談の内容を、親友の視点から語られるストーリーにする
- 語り手は親友・友人で、主人公を「彼女」「彼」などと呼ぶ
- 親友の目線で見た主人公の様子を描写
- 親友が主人公のために行動する動機・感情を明確に
- 親友自身の成長や変化も描写に含める

ストーリーの内容は維持しつつ、視点のみを変更してください。
"""
    elif viewpoint == "第三者の視点":
        return """
【視点変更指示】
以下のテーマ/ネタを「第三者の視点」のストーリーに変換してください。

視点変更のポイント：
- 客観的な視点から物語を見る
- 複数の人物の感情・行動を描く
- ナレーション的な視点

ストーリーの内容は維持しつつ、視点のみを変更してください。
"""
    elif viewpoint == "体験談から自動変換（親友目線推奨）":
        # 体験談かどうかを簡易判定（「私」「僕」「自分」などの一人称が含まれているか）
        if any(word in theme for word in ["私", "僕", "自分", "私の", "僕の"]):
            return """
【視点変更指示：体験談から親友目線への自動変換】
入力されたテーマ/ネタは体験談形式です。これを「親友・友人目線」のストーリーに自動変換してください。

変換のポイント：
- 体験談の主語となっている人物を「親友」に置き換える
- 語り手を「私（親友）」に変更する
- 「私の親友が...」「友人が...」という形式にする
- 体験談の内容は維持するが、語り手を友人に変更
- 友人の目線で見た主人公の様子を描写
- 友人が主人公のために行動する動機・感情を明確に

例：
- 体験談：「夫にモラハラされていた私が、親友の一言で離婚を決意...」
- → 親友目線：「私の親友が夫にモラハラされていた。ある日、私が彼女に伝えた一言が...」

ストーリーの内容は維持しつつ、視点のみを変更してください。
"""
    return ""

def generate_scenario(api_key, theme, story_format, tone, additional_notes="", viewpoint="主人公目線（デフォルト）"):
    """
    Claude APIを使用してシナリオを生成
    
    Args:
        api_key: Anthropic APIキー
        theme: テーマ/ネタ
        story_format: ストーリー形式（前後編など）
        tone: トーン/雰囲気
        additional_notes: 追加の要望
        viewpoint: 視点の選択
        
    Returns:
        生成されたシナリオのテキスト
    """
    client = anthropic.Anthropic(api_key=api_key)

    master_prompt = load_master_prompt()

    # 視点変更の指示を生成
    viewpoint_instruction = generate_viewpoint_instruction(viewpoint, theme)
    
    # ユーザー入力を構造化
    # 文字数ガイドライン設定
    if "前後編" in story_format:
        char_limit = """
【必須】文字数制限【より厳格に】：
- **前編：最大500文字以内（推奨400〜500文字）**
- **後編：最大500文字以内（推奨400〜500文字）**
- **合計：最大1000文字以内（推奨800〜1000文字）**
- **絶対に上限を超えないこと**
- **物語を膨らませすぎず、簡潔でインパクトのある展開を心がけること**

【厳密】文字数カウント方法：
- 改行、記号（※、「」、『』、■、（）、…、！、？、〜など）、スペースを除いた純粋なテキスト文字のみカウント
- 登場人物セクションは文字数に含めない（シナリオ本文のみカウント）
- カウント例：
  - `A子「こんにちは」※笑顔` → カウント「A子こんにちは笑顔」= 9文字
  - `※夜、仕事から帰宅したA子` → カウント「夜仕事から帰宅したA子」= 12文字

【重要】簡潔性と面白さのバランス：
- 制限内で最高の面白さを実現すること
- **冗長な表現は徹底的に削る**
- **文字数を増やすために物語を不必要に膨らませない**
- **簡潔でインパクトのある展開を優先すること**
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

{viewpoint_instruction}

【形式】
{story_format}

【テーマ/ネタ】
{theme}

【トーン/雰囲気】
{tone}

【追加の要望】
{additional_notes if additional_notes else "特になし"}

【最重要】テーマ/ネタに忠実であること：
- 上記のテーマ/ネタに記載されている内容のみを使用すること
- テーマに記載されていない設定・情報・要素（警察、裁判所、会社、学校、病院など）は一切追加しない
- テーマから大きく逸脱した展開は絶対に避けること
- テーマに記載されている登場人物・場所・状況のみを使用すること

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
def save_history(theme, story_format, tone, result, additional_notes="", feasibility_check="", prompt_version="", viewpoint=""):
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
        "viewpoint": viewpoint,  # 視点情報を追加
        "result": result
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return filepath

# 履歴を読み込む
def load_history(limit=10, search_query=""):
    history_dir = os.path.join(os.path.dirname(__file__), "output")
    if not os.path.exists(history_dir):
        return []

    history_files = sorted(
        [f for f in os.listdir(history_dir) if f.endswith('.json')],
        reverse=True
    )

    histories = []
    for filename in history_files:
        filepath = os.path.join(history_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 検索クエリがある場合、フィルタリング
            if search_query:
                if (search_query.lower() in data.get('theme', '').lower() or
                    search_query.lower() in data.get('tone', '').lower() or
                    search_query.lower() in data.get('result', '').lower()):
                    histories.append(data)
            else:
                histories.append(data)
        
        # 制限数に達したら終了
        if len(histories) >= limit:
            break

    return histories

# お気に入り管理
def get_favorites():
    """お気に入りリストを取得"""
    favorites_file = os.path.join(os.path.dirname(__file__), "output", "favorites.json")
    if os.path.exists(favorites_file):
        with open(favorites_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_favorites(favorites):
    """お気に入りリストを保存"""
    favorites_file = os.path.join(os.path.dirname(__file__), "output", "favorites.json")
    with open(favorites_file, "w", encoding="utf-8") as f:
        json.dump(favorites, f, ensure_ascii=False, indent=2)

def toggle_favorite(timestamp):
    """お気に入りの追加/削除を切り替え"""
    favorites = get_favorites()
    if timestamp in favorites:
        favorites.remove(timestamp)
    else:
        favorites.append(timestamp)
    save_favorites(favorites)
    return timestamp in favorites

def is_favorite(timestamp):
    """お気に入りかどうかを確認"""
    favorites = get_favorites()
    return timestamp in favorites

# 統計情報を取得
def get_statistics():
    """生成統計情報を取得"""
    history_dir = os.path.join(os.path.dirname(__file__), "output")
    if not os.path.exists(history_dir):
        return {
            "total_count": 0,
            "by_tone": {},
            "by_date": {}
        }
    
    history_files = [f for f in os.listdir(history_dir) if f.endswith('.json')]
    
    stats = {
        "total_count": len(history_files),
        "by_tone": {},
        "by_date": {}
    }
    
    for filename in history_files:
        filepath = os.path.join(history_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                # トーン別の集計
                tone = data.get('tone', '不明')
                stats["by_tone"][tone] = stats["by_tone"].get(tone, 0) + 1
                
                # 日付別の集計
                if 'timestamp' in data:
                    date = data['timestamp'][:10]  # YYYY-MM-DD形式
                    stats["by_date"][date] = stats["by_date"].get(date, 0) + 1
        except:
            continue
    
    return stats

# シナリオを編集して保存
def update_history(timestamp, updated_result):
    """履歴のシナリオを更新"""
    history_dir = os.path.join(os.path.dirname(__file__), "output")
    history_files = [f for f in os.listdir(history_dir) if f.endswith('.json')]
    
    for filename in history_files:
        filepath = os.path.join(history_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            if data.get('timestamp', '') == timestamp:
                data['result'] = updated_result
                data['updated_at'] = datetime.now().isoformat()
                data['is_edited'] = True
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                return True
    return False

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
        # プロジェクト識別情報（大きく表示）
        st.markdown("""
        <div style="background-color: #FFE5E5; padding: 1rem; border-radius: 10px; margin-bottom: 1rem; border: 2px solid #FF6B6B;">
            <h3 style="color: #FF0000; margin: 0; text-align: center;">⚠️ プロジェクト識別</h3>
            <p style="color: #333; margin: 0.5rem 0; text-align: center; font-weight: bold; font-size: 1.1rem;">
                💙 恋愛漫画シナリオ生成ツールv2<br>
                🔌 ポート: <span style="color: #FF0000; font-size: 1.3rem;">8508</span>
            </p>
            <p style="color: #666; margin: 0; text-align: center; font-size: 0.85rem;">
                ディレクトリ: 恋愛漫画シナリオ生成ツールv2
            </p>
        </div>
        """, unsafe_allow_html=True)
        
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

        # 視点選択
        st.subheader("👁️ 視点の選択")
        viewpoint_option = st.selectbox(
            "ストーリーの視点を選択",
            [
                "主人公目線（デフォルト）",
                "親友・友人目線",
                "第三者の視点",
                "体験談から自動変換（親友目線推奨）",
                "カスタム（自由入力）"
            ],
            help="体験談を入力した場合、「体験談から自動変換」を選択すると親友目線に変換されます。カスタムを選ぶと自由に視点を指定できます。"
        )
        
        # カスタム入力の場合
        viewpoint_custom = ""
        if viewpoint_option == "カスタム（自由入力）":
            viewpoint_custom = st.text_input(
                "視点を自由に入力してください",
                placeholder="例：幼馴染の視点、元カレの視点、担任教師の視点、など",
                help="具体的な視点を入力してください。例：「幼馴染の視点」「元カレの視点」「担任教師の視点」など",
                key="viewpoint_custom_input"
            )
            viewpoint = viewpoint_custom if viewpoint_custom else "主人公目線（デフォルト）"
        else:
            viewpoint = viewpoint_option
        
        # 視点の説明
        if viewpoint_option == "親友・友人目線":
            st.info("💡 体験談の内容を、親友の視点から語られるストーリーに変換します")
        elif viewpoint_option == "第三者の視点":
            st.info("💡 客観的な視点から、複数の人物の感情・行動を描きます")
        elif viewpoint_option == "体験談から自動変換（親友目線推奨）":
            st.info("💡 体験談が入力された場合、自動的に親友目線に変換します")
        elif viewpoint_option == "カスタム（自由入力）":
            if viewpoint_custom:
                st.info(f"💡 視点「{viewpoint_custom}」でストーリーが生成されます")
            else:
                st.warning("⚠️ カスタム視点を入力してください")

        st.divider()

        # 統計情報表示
        st.subheader("📊 統計情報")
        stats = get_statistics()
        if stats["total_count"] > 0:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("総生成数", stats["total_count"])
            with col2:
                favorites_count = len(get_favorites())
                st.metric("お気に入り", favorites_count)
            
            # トーン別の統計
            if stats["by_tone"]:
                with st.expander("📈 トーン別統計"):
                    for tone, count in sorted(stats["by_tone"].items(), key=lambda x: x[1], reverse=True):
                        st.progress(count / stats["total_count"], text=f"{tone}: {count}件")
        else:
            st.info("まだ統計情報がありません")

        st.divider()

        # 履歴表示
        st.subheader("📚 生成履歴")
        
        # 検索機能
        search_query = st.text_input("🔍 検索", placeholder="テーマやトーンで検索...", key="history_search")
        
        # フィルター
        filter_type = st.radio(
            "フィルター",
            ["すべて", "お気に入りのみ"],
            horizontal=True,
            key="history_filter"
        )
        
        if st.button("🔄 履歴を更新", type="primary"):
            st.rerun()

        histories = load_history(limit=20, search_query=search_query)
        
        # お気に入りフィルター
        if filter_type == "お気に入りのみ":
            favorites = get_favorites()
            histories = [h for h in histories if h.get('timestamp', '') in favorites]
        
        if histories:
            st.caption(f"表示中: {len(histories)}件")
            for i, hist in enumerate(histories, 1):
                timestamp = hist.get('timestamp', '')
                theme_preview = hist['theme'][:20]
                is_fav = is_favorite(timestamp) if timestamp else False
                
                col1, col2 = st.columns([5, 1])
                with col1:
                    if st.button(
                        f"{'⭐' if is_fav else '📄'} {theme_preview}",
                        key=f"hist_link_{i}",
                        type="secondary",
                        use_container_width=True
                    ):
                        st.session_state.selected_history = hist
                        st.session_state.selected_history_index = i
                        st.rerun()
                with col2:
                    if timestamp:
                        fav_key = f"fav_{i}_{timestamp}"
                        if st.button("⭐" if is_fav else "☆", key=fav_key, help="お気に入り"):
                            toggle_favorite(timestamp)
                            st.rerun()
        else:
            st.info("まだ生成履歴がありません" if not search_query and filter_type == "すべて" else "検索結果がありません")

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

**v2.2.0の主な変更点（フィードバック対応版）**
- 👁️ 視点変更機能の実装（主人公目線/親友目線/第三者の視点/自動変換/カスタム入力）
- 📏 文字数制限の強化（リライト時に自動チェック＆短縮）
- 🎭 パターン化回避機能（エンディングパターンの多様化）
- 📝 視点情報を履歴に保存

**v2.1.0の主な変更点（ブラッシュアップ版）**
- 🔍 検索機能の追加（テーマ・トーン・内容で検索可能）
- ⭐ お気に入り機能の追加
- ✏️ シナリオ編集機能の追加
- 📊 統計情報の表示（総生成数、トーン別統計）
- 🛡️ エラーハンドリングの強化
- 📈 進捗表示の改善

**v2.0の主な変更点**
- ✅ 前後編構成に完全最適化
- ✅ プロンプト35%削減（639行→415行）
- ✅ 文字数制限の厳格化（最大500/500/1000文字）
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
            try:
                # 進捗表示用のプレースホルダー
                progress_container = st.container()
                
                with progress_container:
                    st.info("🚀 シナリオ生成を開始します...")
                    
                    # ステップ1: シナリオ生成
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.text("📝 ステップ1/2: シナリオ初稿を作成中... (約30-60秒)")
                    progress_bar.progress(25)
                    
                    draft_scenario = generate_scenario(api_key, theme, story_format, tone, additional_notes, viewpoint)
                    
                    # エラーチェック
                    if draft_scenario.startswith("エラーが発生しました"):
                        st.error(f"❌ シナリオ生成中にエラーが発生しました: {draft_scenario}")
                        st.info("💡 解決方法:\n- APIキーが正しいか確認してください\n- インターネット接続を確認してください\n- しばらく待ってから再試行してください")
                    else:
                        progress_bar.progress(50)
                        
                        # ステップ2: 自動チェック＆リライト
                        status_text.text("✨ ステップ2/2: 品質チェック＆自動リライト中... (約20-40秒)")
                        progress_bar.progress(75)
                        
                        final_scenario = check_and_fix_scenario(api_key, draft_scenario, viewpoint)
                        
                        progress_bar.progress(100)
                        status_text.text("✅ シナリオ生成が完了しました！")
                        
                        # セッションステートに保存
                        st.session_state.result = final_scenario
                        st.session_state.theme = theme
                        st.session_state.story_format = story_format
                        st.session_state.tone = tone
                        st.session_state.viewpoint = viewpoint

                        # 履歴に保存（プロンプトバージョンと視点も記録）
                        save_history(
                            theme,
                            story_format,
                            tone,
                            final_scenario,
                            additional_notes=additional_notes,
                            feasibility_check="",  # 空文字列にする
                            prompt_version=PROMPT_VERSION,  # プロンプトバージョンを記録
                            viewpoint=viewpoint  # 視点情報を記録
                        )
                        
                        # 成功メッセージ
                        st.success("🎉 シナリオが生成されました！")
                        st.balloons()
                        
                        # 少し待ってからリロード
                        time.sleep(1)
                        st.rerun()
                        
            except anthropic.APIError as e:
                st.error(f"❌ APIエラーが発生しました: {str(e)}")
                st.info("💡 解決方法:\n- APIキーとクレジット残高を確認してください\n- APIの利用制限を確認してください")
            except Exception as e:
                st.error(f"❌ 予期しないエラーが発生しました: {str(e)}")
                st.info("💡 エラーが続く場合は、開発者にお問い合わせください")
                import traceback
                with st.expander("🔍 詳細なエラー情報"):
                    st.code(traceback.format_exc())

    # 右カラム: 結果表示（新規生成 or 履歴選択）
    if "selected_history" in st.session_state:
        # 履歴が選択された場合
        st.divider()
        hist = st.session_state.selected_history
        st.header(f"📝 履歴 #{st.session_state.selected_history_index}")

        # 履歴情報の表示
        prompt_ver = hist.get('prompt_version', '不明')
        viewpoint_info = hist.get('viewpoint', '不明')
        st.info(f"""
**テーマ**: {hist['theme']}
**形式**: {hist['story_format']}
**トーン**: {hist['tone']}
**視点**: {viewpoint_info}
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
                    if zenpen_count > 500 or kohen_count > 500 or total_count > 1000:
                        st.warning("⚠️ 文字数が制限を超えています")
                    elif total_count < 800:
                        st.info("ℹ️ 推奨文字数（800-1000文字）より少なめです")

        # 編集機能
        with st.expander("✏️ シナリオを編集", expanded=False):
            edited_scenario = st.text_area(
                "シナリオを編集してください",
                value=hist['result'],
                height=400,
                key=f"edit_{hist.get('timestamp', '')}"
            )
            
            col_edit1, col_edit2 = st.columns(2)
            with col_edit1:
                if st.button("💾 保存", key=f"save_edit_{hist.get('timestamp', '')}"):
                    if update_history(hist.get('timestamp', ''), edited_scenario):
                        st.success("✅ シナリオを更新しました！")
                        # 履歴を再読み込み
                        hist['result'] = edited_scenario
                        st.session_state.selected_history = hist
                        st.rerun()
                    else:
                        st.error("❌ 保存に失敗しました")
            
            with col_edit2:
                if st.button("↩️ キャンセル", key=f"cancel_edit_{hist.get('timestamp', '')}"):
                    st.rerun()

        # アクションボタン
        col1, col2, col3, col4 = st.columns(4)
        
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
            # お気に入りボタン
            timestamp = hist.get('timestamp', '')
            is_fav = is_favorite(timestamp) if timestamp else False
            if st.button("⭐ お気に入り" if is_fav else "☆ お気に入り", key=f"fav_detail_{timestamp}"):
                toggle_favorite(timestamp)
                st.rerun()
        
        with col4:
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
                    if zenpen_count > 500 or kohen_count > 500 or total_count > 1000:
                        st.warning("⚠️ 文字数が制限を超えています")
                    elif total_count < 800:
                        st.info("ℹ️ 推奨文字数（800-1000文字）より少なめです")

        # 編集機能
        with st.expander("✏️ シナリオを編集", expanded=False):
            edited_scenario_new = st.text_area(
                "シナリオを編集してください",
                value=st.session_state.result,
                height=400,
                key="edit_new_scenario"
            )
            
            col_edit1, col_edit2 = st.columns(2)
            with col_edit1:
                if st.button("💾 保存", key="save_edit_new"):
                    # セッションステートを更新
                    st.session_state.result = edited_scenario_new
                    st.success("✅ シナリオを更新しました！")
                    st.rerun()
            
            with col_edit2:
                if st.button("↩️ キャンセル", key="cancel_edit_new"):
                    st.rerun()

        # アクションボタン
        col1, col2, col3, col4 = st.columns(4)

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
            # お気に入りボタン（新規生成の場合は履歴に保存後にお気に入り可能）
            st.info("💡 履歴に保存されるとお気に入り機能が利用できます")
        
        with col4:
            if st.button("🔄 新しいシナリオを生成"):
                del st.session_state.result
                if "theme" in st.session_state:
                    del st.session_state.theme
                if "story_format" in st.session_state:
                    del st.session_state.story_format
                if "tone" in st.session_state:
                    del st.session_state.tone
                st.rerun()

if __name__ == "__main__":
    main()
