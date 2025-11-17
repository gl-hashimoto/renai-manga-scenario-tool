# 🚀 Streamlit Community Cloudへのデプロイ手順

## ステップ1: Streamlit Community Cloudにアクセス

1. https://share.streamlit.io/ にアクセス
2. GitHubアカウントでサインイン
3. 必要に応じてStreamlitにGitHubへのアクセス権限を付与

## ステップ2: 新しいアプリをデプロイ

1. 「New app」ボタンをクリック
2. 以下の情報を入力：
   - **Repository**: `gl-hashimoto/renai-manga-scenario-tool`
   - **Branch**: `main`
   - **Main file path**: `app.py`
   - **App URL** (カスタマイズ可能): 例 `renai-manga-tool`

3. 「Advanced settings」をクリック（重要！）
4. Python versionを確認: `3.11`

## ステップ3: Secretsの設定（最重要）

**デプロイ前に必ず設定してください！**

「Advanced settings」→「Secrets」タブで以下を入力：

```toml
ANTHROPIC_API_KEY = "sk-ant-api03-あなたの実際のAPIキーをここに入力"
```

**⚠️ 重要な注意事項:**
- APIキーの形式: `sk-ant-api03-...`で始まる文字列
- ダブルクォーテーション（`"`）で囲む
- スペースや改行を入れない
- このキーは絶対に公開しないでください

## ステップ4: デプロイ実行

1. 「Deploy!」ボタンをクリック
2. デプロイが開始されます（通常2〜3分）
3. ログが表示され、進行状況を確認できます

## ステップ5: デプロイ完了後の確認

### ✅ 動作確認チェックリスト

- [ ] アプリが正常に起動する
- [ ] タイトルが「💙 恋愛漫画シナリオ生成ツールv2」と表示される
- [ ] サイドバーのAPIキー入力欄が表示される
- [ ] テーマ入力エリアが表示される
- [ ] 「🎬 シナリオを生成する」ボタンが表示される

### 🧪 機能テスト

1. サイドバーにAPIキーを入力（すでにSecrets設定済みの場合は不要）
2. テーマを入力（例：「冷たい上司が私にだけ優しい」）
3. トーンを選択
4. 「🎬 シナリオを生成する」をクリック
5. シナリオが生成されることを確認
6. 文字数カウントが表示されることを確認

## トラブルシューティング

### ❌ エラー: "ANTHROPIC_API_KEY not found"

**原因**: Secretsが正しく設定されていない

**解決方法**:
1. Streamlit Cloudのダッシュボードに戻る
2. アプリの「Settings」→「Secrets」を開く
3. 以下の形式で再設定:
```toml
ANTHROPIC_API_KEY = "sk-ant-api03-..."
```
4. 「Save」をクリック
5. アプリが自動的に再起動されるまで待つ

### ❌ エラー: "ModuleNotFoundError"

**原因**: 依存パッケージがインストールされていない

**解決方法**:
1. `requirements.txt`が正しくコミットされているか確認
2. requirements.txtの内容:
```
streamlit>=1.32.0
anthropic>=0.34.0
python-dotenv>=1.0.0
```
3. GitHubにプッシュし直す
4. Streamlit Cloudで「Reboot app」をクリック

### ❌ エラー: アプリが起動しない

**原因**: 複数の可能性

**解決方法**:
1. Streamlit Cloudのログを確認
2. Python versionが3.11になっているか確認
3. `app.py`が正しいパスにあるか確認
4. GitHubリポジトリが最新の状態か確認

## デプロイ後の管理

### アプリの再起動
Settings → Reboot app

### ログの確認
Manage app → View logs

### アプリの削除
Settings → Delete app

### URLの変更
Settings → General → App URL

## セキュリティベストプラクティス

✅ **DO（推奨）**:
- Streamlit Cloud SecretsでAPIキーを管理
- .envファイルを.gitignoreに含める
- 定期的にAPIキーをローテーション

❌ **DON'T（禁止）**:
- APIキーをコードに直接書かない
- APIキーをGitHubにコミットしない
- APIキーをSlackやメールで共有しない

## よくある質問

**Q: 無料で使えますか？**
A: はい、Streamlit Community Cloudは無料です。ただし、Anthropic APIの使用料は別途かかります。

**Q: カスタムドメインは使えますか？**
A: はい、Settings → General → Custom domainで設定できます。

**Q: 複数人で使えますか？**
A: はい、URLを共有すれば誰でもアクセスできます。ただし、APIキーの使用料には注意してください。

**Q: データは保存されますか？**
A: はい、outputディレクトリに履歴が保存されます。ただし、Streamlit Cloudの無料プランでは永続的なストレージではありません。

## デプロイ完了！

デプロイが成功したら、URLをチーム members と共有しましょう！

例: `https://renai-manga-tool.streamlit.app`

---

**🎉 おめでとうございます！Webツールとして使用できるようになりました！**
