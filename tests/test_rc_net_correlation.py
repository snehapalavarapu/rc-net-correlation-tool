from __future__ import annotations

import csv
import gzip
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from rc_net_correlation import build_deltas
from sample_spef_parser import parse_spef


REPO_ROOT = Path(__file__).resolve().parents[1]
REF_SPEF = REPO_ROOT / "tests" / "data" / "ref.spef"
NEW_SPEF = REPO_ROOT / "tests" / "data" / "new.spef"


class SpefCorrelationTests(unittest.TestCase):
    def test_parser_uses_name_map_for_stable_net_identity(self):
        ref = parse_spef(REF_SPEF)
        new = parse_spef(NEW_SPEF)

        self.assertIn("top/clk", ref.nets)
        self.assertIn("top/clk", new.nets)
        self.assertEqual(ref.nets["top/clk"].raw_name, "*1")
        self.assertEqual(new.nets["top/clk"].raw_name, "*2")

    def test_build_deltas_filters_zero_rc_and_sorts_by_rc_delta(self):
        deltas, stats = build_deltas(REF_SPEF, NEW_SPEF)

        self.assertEqual(stats["matched_nets"], 3)
        self.assertEqual(stats["skipped_zero_rc"], 1)
        self.assertEqual(deltas[0].name, "top/clk")
        self.assertAlmostEqual(deltas[0].delta_r, 2.0)
        self.assertAlmostEqual(deltas[0].delta_c, 0.1)
        self.assertAlmostEqual(deltas[0].delta_rc, 2.2)

    def test_quality_filter_and_net_selection_limit_results(self):
        deltas, stats = build_deltas(
            REF_SPEF,
            NEW_SPEF,
            selected_nets={"top/clk", "top/data[0]"},
            quality_filter=3,
        )

        self.assertEqual(stats["matched_nets"], 1)
        self.assertEqual(deltas[0].name, "top/clk")

    def test_cli_writes_summary_and_csv_for_gzip_input(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            ref_gz = tmpdir_path / "ref.spef.gz"
            new_gz = tmpdir_path / "new.spef.gz"
            ref_gz.write_bytes(gzip.compress(REF_SPEF.read_bytes()))
            new_gz.write_bytes(gzip.compress(NEW_SPEF.read_bytes()))
            outdir = tmpdir_path / "out"

            result = subprocess.run(
                [
                    sys.executable,
                    str(REPO_ROOT / "rc_net_correlation.py"),
                    "-ref_rc",
                    str(ref_gz),
                    "-new_rc",
                    str(new_gz),
                    "-nets",
                    "top/clk,top/reset",
                    "-output",
                    str(outdir),
                ],
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("Matched nets compared: 2", result.stdout)
            csv_files = list(outdir.glob("rc_correlation_details_*.csv"))
            summary_files = list(outdir.glob("rc_correlation_summary_*.txt"))
            self.assertEqual(len(csv_files), 1)
            self.assertEqual(len(summary_files), 1)

            with csv_files[0].open() as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual([row["net_name"] for row in rows], ["top/clk", "top/reset"])


if __name__ == "__main__":
    unittest.main()
