# rc-net-correlation-tool

RC Net Correlation Tool for SPEF comparison using stable net names instead of raw numeric IDs.

## Files

- `rc_net_correlation.py` — main CLI tool
- `sample_spef_parser.py` — SPEF parser helper
- `tests/data/*.spef` — sample SPEF inputs for examples and tests

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
  -ref_rc tests/data/ref.spef \
  -new_rc tests/data/new.spef \
  -output /tmp/rc_out
```

## Tests

```bash
python -m unittest tests.test_rc_net_correlation
```

## Notes on quality filtering

When `-quality_filter` is enabled, a matched net must have a quality value in both SPEFs and both values must be greater than or equal to the threshold. Quality values can come from optional `*Q` or `*QUALITY` entries inside a `*D_NET` section.
