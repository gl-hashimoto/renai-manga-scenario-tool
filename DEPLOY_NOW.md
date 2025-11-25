# 🚀 デプロイ手順（今すぐ実行）

## ✅ 完了した作業

- [x] コードをコミット（v2.2.0）
- [x] GitHubにプッシュ（mainブランチ）

## 📋 次のステップ：Streamlit Cloudでデプロイ

### ステップ1: Streamlit Cloudにアクセス

1. https://share.streamlit.io/ にアクセス
2. GitHubアカウントでログイン

### ステップ2: 新しいアプリをデプロイ

1. **「New app」**ボタンをクリック

2. 以下の情報を入力：
   - **Repository**: `gl-hashimoto/renai-manga-scenario-tool`
   - **Branch**: `main`
   - **Main file path**: `app.py`
   - **App URL**（既存の場合）: `renai-manga-scenario-tool` または変更

### ステップ3: Advanced settings（重要！）

1. **「Advanced settings」**をクリック
2. **Python version**: `3.11` を選択（または `3.11.11` が利用可能ならそれ）

### ステップ4: Secretsの設定（最重要！）

**「Advanced settings」→「Secrets」タブ**で以下を入力：

```toml
ANTHROPIC_API_KEY = "sk-ant-api03-あなたの実際のAPIキー"
```

**⚠️ 重要な注意事項:**
- APIキーの形式: `sk-ant-api03-...`で始まる文字列
- ダブルクォーテーション（`"`）で囲む
- スペースや改行を入れない
- このキーは絶対に公開しないでください

### ステップ5: デプロイ実行

1. **「Deploy!」**ボタンをクリック
2. デプロイが開始されます（通常2〜3分）
3. ログが表示され、進行状況を確認できます

### ステップ6: デプロイ完了後の確認

デプロイが完了したら、以下のURLでアクセス可能になります：

**https://renai-manga-scenario-tool.streamlit.app/**

### ✅ 動作確認チェックリスト

- [ ] アプリが正常に起動する
- [ ] タイトルが「💙 恋愛漫画シナリオ生成ツールv2 v2.2.0」と表示される
- [ ] サイドバーの設定が表示される
- [ ] 視点選択機能が表示される
- [ ] テーマ入力エリアが表示される
- [ ] 「🎬 シナリオを生成する」ボタンが表示される

### 🧪 機能テスト

1. テーマを入力（例：「冷たい上司が私にだけ優しい」）
2. トーンを選択
3. 視点を選択（カスタム入力も試す）
4. 「🎬 シナリオを生成する」をクリック
5. シナリオが生成されることを確認
6. 文字数カウントが表示されることを確認

## 🔄 既存アプリを更新する場合

既にデプロイ済みの場合は、GitHubへのプッシュで自動的に再デプロイされます。

手動で再デプロイしたい場合：
1. Streamlit Cloudダッシュボードにアクセス
2. アプリを選択
3. 「⋮」→「Reboot app」をクリック

## 🐛 トラブルシューティング

### ❌ エラー: "ANTHROPIC_API_KEY not found"

**解決方法**:
1. Streamlit Cloudのダッシュボードに戻る
2. アプリの「Settings」→「Secrets」を開く
3. 以下を再設定:
```toml
ANTHROPIC_API_KEY = "sk-ant-api03-..."
```
4. 「Save」をクリック
5. アプリが自動的に再起動されるまで待つ

### ❌ エラー: "ModuleNotFoundError"

**解決方法**:
1. `requirements.txt`が正しくコミットされているか確認
2. GitHubにプッシュし直す
3. Streamlit Cloudで「Reboot app」をクリック

---

## 🎉 デプロイ完了！

デプロイが成功したら、URLをチーム members と共有しましょう！

**URL**: https://renai-manga-scenario-tool.streamlit.app/

---

**次のアクション**: Streamlit Cloudで上記の手順を実行してください！

