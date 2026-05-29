"""日报入口 — GitHub Actions 调用"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.report_generator import run_daily

if __name__ == "__main__":
    success = run_daily()
    sys.exit(0 if success else 1)