#!/bin/bash
# 医药研发周报 - 站点生成脚本
# 用法: bash generate.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ============================================================
# 配置
# ============================================================
REPORT_DIR="reports"
ARCHIVES_JSON="archives.json"

# 确保目录存在
mkdir -p "$REPORT_DIR"

echo "=========================================="
echo "  医药研发周报 - 站点初始化完成"
echo "=========================================="
echo ""
echo "站点目录: $SCRIPT_DIR"
echo "报告目录: $REPORT_DIR"
echo ""
echo "后续步骤:"
echo "1. 每周自动生成报告到 reports/YYYY/MM-DD/"
echo "2. 更新 archives.json 归档索引"
echo "3. 自动 git commit & push 到 GitHub Pages"
echo ""
echo "=========================================="
