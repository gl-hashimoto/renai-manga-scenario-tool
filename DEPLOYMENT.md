# Streamlit Community Cloudへのデプロイ手順

## 1. GitHubリポジトリの準備

このプロジェクトをGitHubにプッシュします。

```bash
cd "/Users/s-hashimoto/Documents/CURSOR/#biz_制作ツール/恋愛漫画シナリオ生成ツールv2"
git init
git add .
git commit -m "Initial commit: 恋愛漫画シナリオ生成ツールv2"
```

## 2. Streamlit Community Cloudでのデプロイ

### 手順：
1. https://share.streamlit.io/ にアクセス
2. GitHubアカウントでログイン
3. 「New app」をクリック
4. リポジトリ、ブランチ、メインファイル（`app.py`）を選択
5. 「Deploy!」をクリック

### Secrets設定（重要）：

デプロイ後、Settings → Secrets で以下を設定：

```toml
ANTHROPIC_API_KEY = "sk-ant-api03-your-actual-api-key-here"
```

**注意**:
- APIキーは絶対にGitHubにコミットしないでください
- Streamlit Cloud上でSecretsとして安全に管理されます
- ローカルでは`.env`ファイルを使用（gitignore済み）

## 3. 動作確認

デプロイ完了後、以下を確認：
- [ ] アプリが正常に起動する
- [ ] APIキーがSecrets経由で読み込まれる
- [ ] シナリオ生成が動作する
- [ ] 履歴が保存される（outputディレクトリ）

## 4. カスタムドメイン設定（オプション）

Settings → General → Custom domain で独自ドメインを設定可能

## トラブルシューティング

### APIキーエラーが出る場合
1. Streamlit Cloud上でSecretsが正しく設定されているか確認
2. キーの形式が正しいか確認（`ANTHROPIC_API_KEY = "sk-ant-..."`）

### デプロイエラーが出る場合
1. requirements.txtが正しいか確認
2. Pythonバージョンを確認（Python 3.8+推奨）
3. ログを確認してエラー箇所を特定

## セキュリティ注意事項

- ✅ `.env`ファイルは`.gitignore`に含まれています
- ✅ `secrets.toml`も`.gitignore`に含まれています
- ✅ APIキーはStreamlit Cloud Secretsで管理
- ❌ 絶対にAPIキーをコードやGitHubにコミットしない
