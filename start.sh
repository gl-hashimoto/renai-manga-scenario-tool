#!/bin/bash

# 恋愛漫画シナリオ生成ツール起動スクリプト

echo "💘 恋愛漫画シナリオ生成ツールを起動中..."
echo "ポート: 8506"
echo "URL: http://localhost:8506"
echo ""

# スクリプトのディレクトリに移動
cd "$(dirname "$0")"

# Streamlitを起動
/Users/s-hashimoto/Documents/CURSOR/.venv/bin/streamlit run app.py
