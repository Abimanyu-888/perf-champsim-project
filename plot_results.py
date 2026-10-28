#!/usr/bin/env python3
"""
plot_results.py  —  Generate bar charts from perf + ChampSim results.
Run from the project root after perf results are collected:

    python3 plot_results.py

Reads:
    results/tsp_perf.txt        — raw perf stat output for TSP
    results/knapsack_perf.txt   — raw perf stat output for Knapsack
    results/perlbench_32kb.json — ChampSim JSON output (32 KiB L1D)
    results/perlbench_64kb.json — ChampSim JSON output (64 KiB L1D)

Writes:
    results/fig_ipc_bar.pdf
    results/fig_cache_bar.pdf
    results/fig_branch_bar.pdf
    results/fig_champsim_ipc.pdf
    results/fig_champsim_misses.pdf
"""

import re, json, sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

RESULTS = Path("results")

# ── colour palette (matches friend's report aesthetic) ────────────────────────
C_TSP  = "#4C72B0"   # blue
C_KS   = "#DD8452"   # orange
C_32   = "#55A868"   # green
C_64   = "#C44E52"   # red

# ─────────────────────────────────────────────────────────────────────────────
# 1.  Parse perf stat output
# ─────────────────────────────────────────────────────────────────────────────

def parse_perf(path: Path) -> dict:
    """Return dict of {counter_name: value} from a perf stat -r N output file."""
    text = path.read_text(errors="replace")
    data = {}
    patterns = {
        "instructions":       r"([\d,]+)\s+instructions",
        "cycles":             r"([\d,]+)\s+cycles",
        "cache_references":   r"([\d,]+)\s+cache-references",
        "cache_misses":       r"([\d,]+)\s+cache-misses",
        "branches":           r"([\d,]+)\s+branches",
        "branch_misses":      r"([\d,]+)\s+branch-misses",
        "elapsed_seconds":    r"([\d.]+)\s+seconds time elapsed",
    }
    for key, pat in patterns.items():
        m = re.search(pat, text)
        if m:
            val = m.group(1).replace(",", "")
            data[key] = float(val)
    if "instructions" in data and "cycles" in data:
        data["ipc"] = data["instructions"] / data["cycles"]
    if "cache_misses" in data and "cache_references" in data and data["cache_references"] > 0:
        data["cache_miss_rate"] = data["cache_misses"] / data["cache_references"] * 100
    if "branch_misses" in data and "branches" in data and data["branches"] > 0:
        data["branch_miss_rate"] = data["branch_misses"] / data["branches"] * 100
    return data


# ─────────────────────────────────────────────────────────────────────────────
# 2.  Parse ChampSim JSON output
# ─────────────────────────────────────────────────────────────────────────────

def parse_champsim_json(path: Path) -> dict:
    """Extract IPC and L1D/LLC miss counts from ChampSim JSON."""
    raw = json.loads(path.read_text())
    # ChampSim JSON structure: list of core records
    result = {}
    if isinstance(raw, list):
        core = raw[0]
    else:
        core = raw
    result["instructions"] = core.get("instructions", 0)
    result["cycles"]       = core.get("cycles", 0)
    result["ipc"]          = core.get("IPC", core.get("ipc",
                                core["instructions"] / max(core["cycles"], 1)
                             ))
    # Cache stats may be nested under "caches" list
    for cache in core.get("caches", []):
        name = cache.get("name", "")
        if "L1D" in name.upper() or "L1-D" in name.upper():
            result["l1d_misses"] = cache.get("misses", 0)
        if "LLC" in name.upper() or "L3" in name.upper():
            result["llc_misses"] = cache.get("misses", 0)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# 3.  Plotting helpers
# ─────────────────────────────────────────────────────────────────────────────

def bar2(ax, labels, vals, colors, ylabel, title, fmt="{:.3f}"):
    bars = ax.bar(labels, vals, color=colors, edgecolor="black", linewidth=0.7, width=0.5)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(vals)*0.01,
                fmt.format(v), ha="center", va="bottom", fontsize=10, fontweight="bold")
    ax.set_ylabel(ylabel, fontsize=11)
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.set_ylim(0, max(vals) * 1.18)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def save(fig, name):
    p = RESULTS / name
    fig.savefig(p, bbox_inches="tight", dpi=150)
    print(f"  Saved: {p}")
    plt.close(fig)


# ─────────────────────────────────────────────────────────────────────────────
# 4.  Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    missing = []
    for f in ["tsp_perf.txt", "knapsack_perf.txt"]:
        if not (RESULTS / f).exists():
            missing.append(f)
    if missing:
        print("WARNING: Missing perf result files:", missing)
        print("         Run the benchmarks first (see SETUP.md).")
        sys.exit(1)

    tsp = parse_perf(RESULTS / "tsp_perf.txt")
    ks  = parse_perf(RESULTS / "knapsack_perf.txt")

    # ── Figure 1: IPC comparison ────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(5, 4))
    bar2(ax,
         ["TSP\n(Held-Karp)", "Knapsack\n(0/1 DP)"],
         [tsp.get("ipc", 0), ks.get("ipc", 0)],
         [C_TSP, C_KS],
         "Instructions Per Cycle (IPC)",
         "Native IPC Comparison")
    save(fig, "fig_ipc_bar.pdf")

    # ── Figure 2: Cache miss rate ────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(5, 4))
    bar2(ax,
         ["TSP\n(Held-Karp)", "Knapsack\n(0/1 DP)"],
         [tsp.get("cache_miss_rate", 0), ks.get("cache_miss_rate", 0)],
         [C_TSP, C_KS],
         "Cache Miss Rate (%)",
         "L1/L2 Cache Miss Rate",
         fmt="{:.2f}%")
    save(fig, "fig_cache_bar.pdf")

    # ── Figure 3: Branch miss rate ───────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(5, 4))
    bar2(ax,
         ["TSP\n(Held-Karp)", "Knapsack\n(0/1 DP)"],
         [tsp.get("branch_miss_rate", 0), ks.get("branch_miss_rate", 0)],
         [C_TSP, C_KS],
         "Branch Miss Rate (%)",
         "Branch Predictor Miss Rate",
         fmt="{:.4f}%")
    save(fig, "fig_branch_bar.pdf")

    # ── ChampSim plots (optional) ────────────────────────────────────────────
    cs32_path = RESULTS / "perlbench_32kb.json"
    cs64_path = RESULTS / "perlbench_64kb.json"
    if cs32_path.exists() and cs64_path.exists():
        cs32 = parse_champsim_json(cs32_path)
        cs64 = parse_champsim_json(cs64_path)

        fig, ax = plt.subplots(figsize=(5, 4))
        bar2(ax,
             ["32 KiB L1D", "64 KiB L1D"],
             [cs32.get("ipc", 0), cs64.get("ipc", 0)],
             [C_32, C_64],
             "IPC",
             "ChampSim IPC: 32 KiB vs 64 KiB L1D")
        save(fig, "fig_champsim_ipc.pdf")

        fig, ax = plt.subplots(figsize=(5, 4))
        bar2(ax,
             ["32 KiB L1D", "64 KiB L1D"],
             [cs32.get("l1d_misses", 0), cs64.get("l1d_misses", 0)],
             [C_32, C_64],
             "L1D Misses",
             "ChampSim L1D Miss Count",
             fmt="{:.0f}")
        save(fig, "fig_champsim_misses.pdf")
    else:
        print("  ChampSim JSON files not found — skipping simulation plots.")

    print("\nAll plots generated successfully.")


if __name__ == "__main__":
    main()
