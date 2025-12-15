"""
Project Entry Point
AI Critic Agent - Main
"""

import os
import sys
import json
from pathlib import Path

# ============================================================
# Environment Setup
# ============================================================

from dotenv import load_dotenv

# 强制从项目根目录加载 .env
PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

# Debug check（第一次跑建议保留）
if not os.getenv("OPENAI_API_KEY"):
    print("❌ ERROR: OPENAI_API_KEY not found.")
    print("👉 Expected .env at:", PROJECT_ROOT / ".env")
    sys.exit(1)

# ============================================================
# Imports (after env is loaded)
# ============================================================

from idea_decomposer.decomposer import IdeaDecomposer


# ============================================================
# Main Logic
# ============================================================

def main():
    print("=" * 72)
    print(" AI CRITIC AGENT — IDEA DECOMPOSER TEST ")
    print("=" * 72)

    # 1. 读取命令行输入
    if len(sys.argv) > 1:
        idea = " ".join(sys.argv[1:])
    else:
        idea = (
            "An AI-powered platform that helps startup founders "
            "stress-test their business ideas using structured critiques."
        )

    print("\n📥 Input Idea:")
    print(idea)

    print("\n⏳ Running Idea Decomposer...\n")

    try:
        decomposer = IdeaDecomposer()

        # 拿 Pydantic 对象（更适合后续 reasoning / critic agent）
        result = decomposer.decompose(idea, return_json=False)

        print("✅ Decomposition succeeded.")
        print("-" * 72)

        print(f"Product Type     : {result.product_type}")
        print(f"Target User      : {result.target_user}")
        print(f"Value Proposition: {result.value_proposition}")

        print("\nAssumptions:")
        for a in result.assumptions:
            category = getattr(a.category, "value", a.category)
            importance = getattr(a.importance, "value", a.importance)

            print(f"  • {a.id}")
            print(f"    - Category  : {category}")
            print(f"    - Importance: {importance}")
            print(f"    - Text      : {a.assumption}")

        risk_categories = [
            getattr(c, "value", c) for c in result.risk_categories
        ]
        print("\nRisk Categories:", ", ".join(risk_categories))

        # JSON（给后续模块 or API 用）
        print("\n📦 JSON Output:")
        print(json.dumps(result.model_dump(), indent=2, ensure_ascii=False))

        print("\n" + "=" * 72)
        print("🎉 Main pipeline completed successfully.")

    except Exception as e:
        print("❌ Pipeline failed:")
        print(str(e))
        import traceback
        traceback.print_exc()
        sys.exit(1)


# ============================================================
# Entry
# ============================================================

if __name__ == "__main__":
    main()
