# rc-net-correlation-tool

RC Net Correlation Tool for SPEF comparison using stable net names instead of raw numeric IDs.

## Files

- `/home/runner/work/rc-net-correlation-tool/rc-net-correlation-tool/rc_net_correlation.py` — main CLI tool
- `/home/runner/work/rc-net-correlation-tool/rc-net-correlation-tool/sample_spef_parser.py` — SPEF parser helper
- `/home/runner/work/rc-net-correlation-tool/rc-net-correlation-tool/tests/data/*.spef` — sample SPEF inputs for examples and tests

## Features

- Matches nets by real net names resolved through `*NAME_MAP`
- Supports `.spef` and `.spef.gz`
- Ignores nets that are zero-R and zero-C in both files by default
- Computes per-net R, C, and RC deltas with percentages
- Supports single-net analysis, comma-separated net lists, and optional quality filtering
- Writes a compact text summary and a detailed CSV report to the output directory

## Usage

```bash
python rc_net_correlation.py -ref_rc ref.spef.gz -new_rc new.spef.gz -output outdir
python rc_net_correlation.py -ref_rc ref.spef.gz -new_rc new.spef.gz -nets "netA,netB,netC" -output outdir
python rc_net_correlation.py -ref_rc ref.spef.gz -new_rc new.spef.gz -net netA -output outdir
python rc_net_correlation.py -ref_rc ref.spef.gz -new_rc new.spef.gz -quality_filter 3 -output outdir
python rc_net_correlation.py -h
```

## Output

The tool prints and writes:

- matched net count
- total common nets considered
- worst R, C, and RC delta nets ranked by delta magnitude
- per-net R / C / RC deltas and percent changes
- readable net names instead of ambiguous numeric IDs
- timestamped files in the output directory:
  - `rc_correlation_summary_<timestamp>.txt`
  - `rc_correlation_details_<timestamp>.csv`

## Example with bundled sample data

```bash
python rc_net_correlation.py \
  -ref_rc /home/runner/work/rc-net-correlation-tool/rc-net-correlation-tool/tests/data/ref.spef \
  -new_rc /home/runner/work/rc-net-correlation-tool/rc-net-correlation-tool/tests/data/new.spef \
  -output /tmp/rc_out
```

## Tests

```bash
python -m unittest /home/runner/work/rc-net-correlation-tool/rc-net-correlation-tool/tests/test_rc_net_correlation.py
```

## Notes on quality filtering

`-quality_filter` applies only when a net has an optional quality value in both SPEFs, such as a `*Q` or `*QUALITY` value inside a `*D_NET` section. Nets without quality data are excluded when the filter is enabled.
