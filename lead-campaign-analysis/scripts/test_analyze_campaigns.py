import csv
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPT = SKILL_DIR / "scripts" / "analyze_campaigns.py"
MOCK = SKILL_DIR / "mock-data"


class AnalyzeCampaignsTest(unittest.TestCase):
    def test_weekly_report_is_read_only_and_marks_actions(self):
        before = (MOCK / "google-current.csv").read_text(encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--period", "weekly", "--input", str(MOCK / "google-current.csv"), str(MOCK / "naver-current.csv"), "--previous", str(MOCK / "google-previous.csv"), str(MOCK / "naver-previous.csv")],
            check=True, capture_output=True, text=True,
        )
        self.assertIn("## 핵심 요약", result.stdout)
        self.assertIn("제외 검토", result.stdout)
        self.assertIn("총예산 유지", result.stdout)
        self.assertIn("플랫폼 간 CPC/CPA 직접 비교 금지", result.stdout)
        self.assertEqual((MOCK / "google-current.csv").read_text(encoding="utf-8"), before)

    def test_rejects_unknown_required_columns(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "invalid.csv"
            with source.open("w", newline="", encoding="utf-8") as handle:
                csv.DictWriter(handle, fieldnames=["Campaign", "Cost"]).writeheader()
            result = subprocess.run([sys.executable, str(SCRIPT), "--period", "weekly", "--input", str(source)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("필수 열 누락", result.stderr)


if __name__ == "__main__":
    unittest.main()
