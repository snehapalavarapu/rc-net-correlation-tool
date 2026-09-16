# RC Net Correlation Tool Presentation

---

## FULL PRESENTATION (5 Slides)

### Slide 1 — RC Net Correlation Tool
**Title:** RC Net Correlation Tool for Same-Design SPEF Comparison

**Subtitle:** Stable net matching, non-zero RC filtering, and readable summaries

**Key Points:**
- Compares two SPEFs from the same design using real net names, not raw numeric IDs
- Matches nets by NAME_MAP / stable net identity to avoid false mismatches
- Ignores zero-RC nets by default so results reflect meaningful parasitic differences
- Highlights worst deltas in R, C, and RC across matched nets
- Designed for quick review of extraction quality and design-to-design drift

**Key Idea:**
The original failure mode was treating local numeric labels as if they were true net names. That is incorrect because the same number can refer to different nets in each SPEF. The tool fixes that by using actual net names for comparison.

---

### Slide 2 — Features and Workflow
**Title:** What the Tool Does

**Capabilities:**
- Reads both SPEFs and builds a stable net map
- Keeps only common nets with non-zero RC characteristics
- Compares R, C, and RC deltas per net
- Reports the worst offenders with readable net names
- Supports single-net analysis, user-selected net lists, quality-based filtering, and help

**Typical Workflow:**
1. Provide reference SPEF and target SPEF
2. Optional: specify selected nets or quality threshold
3. Run comparison
4. Review worst-net summary and detailed deltas
5. Use results to diagnose extraction or RC shifts

---

### Slide 3 — Use Cases
**Title:** Where This Is Useful

**Key Applications:**
- Golden-vs-target RC comparison for same design
- Finding nets with major parasitic drift after a change
- Checking whether extraction changed significantly after ECOs, routing, or fill updates
- Validating extraction quality before signoff
- Narrowing a review to only the nets that matter

**Examples:**
- Compare two SPEFs for the same block
- Compare only a few critical nets
- Restrict to nets that pass a given quality score
- Focus on the highest delta nets first

---

### Slide 4 — Example Commands
**Title:** Example Usage

**Command Examples:**
```bash
# Basic comparison
python rc_net_correlation.py -ref_rc ref.spef.gz -new_rc new.spef.gz -output outdir

# Specific nets only
python rc_net_correlation.py -ref_rc ref.spef.gz -new_rc new.spef.gz -nets "netA,netB,netC" -output outdir

# Quality-based filtering
python rc_net_correlation.py -ref_rc ref.spef.gz -new_rc new.spef.gz -quality_filter 3 -output outdir

# Help
python rc_net_correlation.py -h
```

**Output Provides:**
- Matched net count
- Total nets compared
- Worst RC delta nets (ranked)
- Per-net R / C / RC deltas
- Readable net names instead of ambiguous numeric IDs

---

### Slide 5 — Why This Is Better Than Raw Numeric Matching
**Title:** Correctness Matters

**The Problem:**
- Numeric labels in SPEF are local identifiers, not global net names
- The same number may refer to different nets in each SPEF
- Comparing by those values creates false mismatches and misleading summaries

**The Solution:**
- Stable name matching enables correct same-design analysis
- Non-zero RC filtering removes noise from floating or empty net data

**Bottom Line:**
This tool is built to answer the real question: **"Which nets actually changed, and by how much?"**

---

## CONDENSED PRESENTATION (3 Slides)

### Slide 1 — What It Does
**Title:** RC Net Correlation Tool: Compare SPEFs by Real Net Names

**Problem:**
- SPEF numeric labels (e.g., *N1, *N2) are local IDs, not true net names
- Same number can refer to different nets in each file → false mismatches
- Raw numeric comparison creates misleading results

**Solution:**
- Match nets by NAME_MAP (stable net identity)
- Compare using real net names instead of ambiguous numeric IDs
- Ignore zero-RC nets to focus on meaningful differences
- Highlight worst deltas in R, C, and RC values

**Bottom Line:** Answer the real question: **"Which nets actually changed, and by how much?"**

---

### Slide 2 — Features & Usage
**Title:** Quick Reference: Features and Commands

**Key Features:**
- Stable net matching (avoids false mismatches)
- RC filtering (removes noise)
- Delta analysis (worst-case reporting)
- Readable output (real net names)
- Flexible filtering (single nets, user lists, quality thresholds)

**Example Commands:**
```bash
# Basic comparison
python rc_net_correlation.py -ref_rc ref.spef.gz -new_rc new.spef.gz -output outdir

# Specific nets only
python rc_net_correlation.py -ref_rc ref.spef.gz -new_rc new.spef.gz -nets "netA,netB,netC" -output outdir

# Quality filtering
python rc_net_correlation.py -ref_rc ref.spef.gz -new_rc new.spef.gz -quality_filter 3 -output outdir
```

**Output:** Matched net count, worst RC delta nets, per-net R/C/RC deltas, readable net names

---

### Slide 3 — Use Cases & Workflow
**Title:** When & How to Use This Tool

**When to Use:**
- Golden-vs-target RC comparison for same design
- Finding nets with major parasitic drift after ECOs, routing, or fill updates
- Validating extraction quality before signoff
- Narrowing review to high-impact nets only

**Workflow:**
1. Provide reference and target SPEF files
2. Optional: filter by nets or quality threshold
3. Run comparison
4. Review worst-net summary and detailed deltas
5. Diagnose extraction shifts or design drift

**Result:** Quick, accurate review of which nets changed and why
