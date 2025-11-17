#!/bin/bash

# 恋愛漫画シナリオ生成ツールv2起動スクリプト

echo "💘 恋愛漫画シナリオ生成ツールv2を起動中..."
echo "ポート: 8508"
echo "URL: http://localhost:8508"
echo ""

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"

# Streamlitを起動（ローカルでは8508、デプロイ時は自動割り当て）
/Users/s-hashimoto/Documents/CURSOR/.venv/bin/streamlit run app.py --server.port 8508
