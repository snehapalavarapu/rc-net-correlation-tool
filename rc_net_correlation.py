from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

from sample_spef_parser import NetData, parse_spef


@dataclass
class NetDelta:
    name: str
    ref_r: float
    new_r: float
    delta_r: float
    pct_r: float | None
    ref_c: float
    new_c: float
    delta_c: float
    pct_c: float | None
    ref_rc: float
    new_rc: float
    delta_rc: float
    pct_rc: float | None
    ref_quality: float | None
    new_quality: float | None


def _percent_delta(reference: float, delta: float) -> float | None:
    if reference == 0:
        return None
    return (delta / reference) * 100.0


def _parse_net_selection(net: str | None, nets: str | None) -> set[str] | None:
    values: list[str] = []
    if net:
        values.append(net)
    if nets:
        values.extend(part.strip() for part in nets.split(","))
    filtered = {value for value in values if value}
    return filtered or None


def _passes_quality(net: NetData, threshold: float | None) -> bool:
    if threshold is None:
        return True
    if net.quality is None:
        return False
    return net.quality >= threshold


def _is_zero_rc(net: NetData) -> bool:
    return net.total_r == 0.0 and net.total_c == 0.0


def build_deltas(
    ref_path: str | Path,
    new_path: str | Path,
    selected_nets: set[str] | None = None,
    quality_filter: float | None = None,
    include_zero_rc: bool = False,
) -> tuple[list[NetDelta], dict[str, int | str]]:
    ref_data = parse_spef(ref_path)
    new_data = parse_spef(new_path)

    common_names = set(ref_data.nets) & set(new_data.nets)
    if selected_nets is not None:
        common_names &= selected_nets

    deltas: list[NetDelta] = []
    skipped_quality = 0
    skipped_zero_rc = 0

    for name in sorted(common_names):
        ref_net = ref_data.nets[name]
        new_net = new_data.nets[name]

        if quality_filter is not None and (
            not _passes_quality(ref_net, quality_filter)
            or not _passes_quality(new_net, quality_filter)
        ):
            skipped_quality += 1
            continue

        if not include_zero_rc and _is_zero_rc(ref_net) and _is_zero_rc(new_net):
            skipped_zero_rc += 1
            continue

        delta_r = new_net.total_r - ref_net.total_r
        delta_c = new_net.total_c - ref_net.total_c
        ref_rc = ref_net.rc
        new_rc = new_net.rc
        delta_rc = new_rc - ref_rc
        deltas.append(
            NetDelta(
                name=name,
                ref_r=ref_net.total_r,
                new_r=new_net.total_r,
                delta_r=delta_r,
                pct_r=_percent_delta(ref_net.total_r, delta_r),
                ref_c=ref_net.total_c,
                new_c=new_net.total_c,
                delta_c=delta_c,
                pct_c=_percent_delta(ref_net.total_c, delta_c),
                ref_rc=ref_rc,
                new_rc=new_net.rc,
                delta_rc=delta_rc,
                pct_rc=_percent_delta(ref_rc, delta_rc),
                ref_quality=ref_net.quality,
                new_quality=new_net.quality,
            )
        )

    deltas.sort(key=lambda item: abs(item.delta_rc), reverse=True)
    stats = {
        "ref_nets": len(ref_data.nets),
        "new_nets": len(new_data.nets),
        "common_nets": len(common_names),
        "matched_nets": len(deltas),
        "skipped_quality": skipped_quality,
        "skipped_zero_rc": skipped_zero_rc,
        "selected_nets": len(selected_nets) if selected_nets else 0,
        "ref_path": str(ref_data.path),
        "new_path": str(new_data.path),
    }
    return deltas, stats


def _format_pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:.2f}%"


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("--top must be a positive integer")
    return parsed


def _write_ranked_section(summary, deltas: Sequence[NetDelta], top_n: int, key_name: str) -> None:
    metric_attr = f"delta_{key_name}"
    ranked = sorted(deltas, key=lambda item: abs(getattr(item, metric_attr)), reverse=True)[:top_n]
    labels = {
        "r": [("R", "delta_r", "pct_r"), ("C", "delta_c", "pct_c"), ("RC", "delta_rc", "pct_rc")],
        "c": [("C", "delta_c", "pct_c"), ("R", "delta_r", "pct_r"), ("RC", "delta_rc", "pct_rc")],
        "rc": [("RC", "delta_rc", "pct_rc"), ("R", "delta_r", "pct_r"), ("C", "delta_c", "pct_c")],
    }
    summary.write(f"\nWorst {key_name.upper()} deltas (sorted by |Δ{key_name.upper()}|):\n")
    if not ranked:
        summary.write("  No matched nets after filtering.\n")
        return
    for index, item in enumerate(ranked, start=1):
        metric_parts = []
        for label, delta_attr, pct_attr in labels[key_name]:
            metric_parts.append(
                f"Δ{label}={getattr(item, delta_attr):.6f} ({_format_pct(getattr(item, pct_attr))})"
            )
        summary.write(
            f"  {index}. {item.name}: " + ", ".join(metric_parts) + "\n"
        )


def write_reports(
    deltas: Sequence[NetDelta],
    stats: dict[str, int | str],
    output_dir: str | Path,
    top_n: int = 10,
) -> tuple[Path, Path]:
    outdir = Path(output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    summary_path = outdir / f"rc_correlation_summary_{timestamp}.txt"
    csv_path = outdir / f"rc_correlation_details_{timestamp}.csv"

    with summary_path.open("w", encoding="utf-8") as summary:
        summary.write("RC Net Correlation Summary\n")
        summary.write(f"Reference SPEF: {stats['ref_path']}\n")
        summary.write(f"New SPEF: {stats['new_path']}\n")
        summary.write(f"Reference nets: {stats['ref_nets']}\n")
        summary.write(f"New nets: {stats['new_nets']}\n")
        summary.write(f"Common nets: {stats['common_nets']}\n")
        summary.write(f"Matched nets compared: {stats['matched_nets']}\n")
        summary.write(f"Skipped by zero-RC filter: {stats['skipped_zero_rc']}\n")
        summary.write(f"Skipped by quality filter: {stats['skipped_quality']}\n")
        _write_ranked_section(summary, deltas, top_n, "r")
        _write_ranked_section(summary, deltas, top_n, "c")
        _write_ranked_section(summary, deltas, top_n, "rc")

    fieldnames = [
        "net_name",
        "ref_r",
        "new_r",
        "delta_r",
        "pct_r",
        "ref_c",
        "new_c",
        "delta_c",
        "pct_c",
        "ref_rc",
        "new_rc",
        "delta_rc",
        "pct_rc",
        "ref_quality",
        "new_quality",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as csv_handle:
        writer = csv.DictWriter(csv_handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in deltas:
            writer.writerow(
                {
                    "net_name": item.name,
                    "ref_r": f"{item.ref_r:.12g}",
                    "new_r": f"{item.new_r:.12g}",
                    "delta_r": f"{item.delta_r:.12g}",
                    "pct_r": "" if item.pct_r is None else f"{item.pct_r:.6f}",
                    "ref_c": f"{item.ref_c:.12g}",
                    "new_c": f"{item.new_c:.12g}",
                    "delta_c": f"{item.delta_c:.12g}",
                    "pct_c": "" if item.pct_c is None else f"{item.pct_c:.6f}",
                    "ref_rc": f"{item.ref_rc:.12g}",
                    "new_rc": f"{item.new_rc:.12g}",
                    "delta_rc": f"{item.delta_rc:.12g}",
                    "pct_rc": "" if item.pct_rc is None else f"{item.pct_rc:.6f}",
                    "ref_quality": "" if item.ref_quality is None else f"{item.ref_quality:.12g}",
                    "new_quality": "" if item.new_quality is None else f"{item.new_quality:.12g}",
                }
            )

    return summary_path, csv_path


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare two SPEF files using stable net names from NAME_MAP."
    )
    parser.add_argument("-ref_rc", required=True, help="Reference SPEF file (.spef or .spef.gz)")
    parser.add_argument("-new_rc", required=True, help="New SPEF file (.spef or .spef.gz)")
    parser.add_argument("-output", required=True, help="Output directory for reports")
    parser.add_argument("-net", help="Compare a single net name")
    parser.add_argument("-nets", help="Comma-separated list of net names to compare")
    parser.add_argument(
        "-quality_filter",
        type=float,
        help="Keep only nets whose optional quality metric is >= this threshold in both SPEFs",
    )
    parser.add_argument(
        "--include-zero-rc",
        action="store_true",
        help="Include nets that have zero R and zero C in both SPEFs",
    )
    parser.add_argument(
        "--top",
        type=_positive_int,
        default=10,
        help="Number of highest |ΔRC| nets to show in the summary (default: 10)",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    selected_nets = _parse_net_selection(args.net, args.nets)
    deltas, stats = build_deltas(
        ref_path=args.ref_rc,
        new_path=args.new_rc,
        selected_nets=selected_nets,
        quality_filter=args.quality_filter,
        include_zero_rc=args.include_zero_rc,
    )
    summary_path, csv_path = write_reports(deltas, stats, args.output, top_n=args.top)

    print(f"Matched nets compared: {stats['matched_nets']}")
    print(f"Total common nets considered: {stats['common_nets']}")
    print(f"Summary report: {summary_path}")
    print(f"Detailed CSV: {csv_path}")
    if deltas:
        print("Top RC delta nets:")
        for item in deltas[: min(args.top, len(deltas))]:
            print(
                f"  {item.name}: ΔR={item.delta_r:.6f}, ΔC={item.delta_c:.6f}, ΔRC={item.delta_rc:.6f}"
            )
    else:
        print("No matched nets remained after filtering.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
