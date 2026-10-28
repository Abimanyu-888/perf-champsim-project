#!/usr/bin/env bash
# run_experiments.sh  —  Full experiment runner
# Must be executed on a Linux machine with perf installed.
# Usage:  bash run_experiments.sh
# See SETUP.md for environment prerequisites.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PERF_DIR="$PROJECT_DIR/perf"
BIN_DIR="$PROJECT_DIR/bin"
RESULTS_DIR="$PROJECT_DIR/results"

echo "=========================================="
echo " perf-champsim-project  |  TSP & Knapsack"
echo "=========================================="
echo ""

# ── 1. Compile C workloads ────────────────────────────────────────────────────
echo "[1/4] Compiling C workloads..."
gcc -O2 "$PERF_DIR/tsp.c"      -o "$BIN_DIR/tsp"
gcc -O2 "$PERF_DIR/knapsack.c" -o "$BIN_DIR/knapsack"
echo "  tsp and knapsack binaries built in $BIN_DIR/"

# ── 2. Profile TSP with perf ──────────────────────────────────────────────────
echo ""
echo "[2/4] Profiling TSP with perf stat (3 repetitions)..."
perf stat -r 3 \
    -e task-clock,context-switches,cpu-migrations,page-faults,\
cycles,instructions,branches,branch-misses,cache-references,cache-misses \
    "$BIN_DIR/tsp" 2>&1 | tee "$RESULTS_DIR/tsp_perf.txt"

echo ""
echo "  TSP results saved to results/tsp_perf.txt"

# ── 3. Profile Knapsack with perf ─────────────────────────────────────────────
echo ""
echo "[3/4] Profiling Knapsack with perf stat (3 repetitions)..."
perf stat -r 3 \
    -e task-clock,context-switches,cpu-migrations,page-faults,\
cycles,instructions,branches,branch-misses,cache-references,cache-misses \
    "$BIN_DIR/knapsack" 2>&1 | tee "$RESULTS_DIR/knapsack_perf.txt"

echo ""
echo "  Knapsack results saved to results/knapsack_perf.txt"

# ── 4. Run ChampSim (if binaries exist) ───────────────────────────────────────
echo ""
echo "[4/4] Running ChampSim simulations..."

TRACE="$PROJECT_DIR/traces/400.perlbench-41B.champsimtrace.xz"

if [[ ! -f "$TRACE" ]]; then
    echo "  WARNING: Trace file not found at $TRACE"
    echo "  Skipping ChampSim runs. See SETUP.md §4 for download instructions."
else
    if [[ -f "$BIN_DIR/champsim_l1d_32kb" ]]; then
        echo "  Running 32 KiB L1D configuration..."
        "$BIN_DIR/champsim_l1d_32kb" \
            --warmup-instructions 100000 \
            --simulation-instructions 1000000 \
            --json "$RESULTS_DIR/perlbench_32kb.json" \
            "$TRACE" 2>&1 | tee "$RESULTS_DIR/perlbench_32kb.txt"
    else
        echo "  WARNING: champsim_l1d_32kb binary not found. Build ChampSim first (SETUP.md §4)."
    fi

    if [[ -f "$BIN_DIR/champsim_l1d_64kb" ]]; then
        echo "  Running 64 KiB L1D configuration..."
        "$BIN_DIR/champsim_l1d_64kb" \
            --warmup-instructions 100000 \
            --simulation-instructions 1000000 \
            --json "$RESULTS_DIR/perlbench_64kb.json" \
            "$TRACE" 2>&1 | tee "$RESULTS_DIR/perlbench_64kb.txt"
    else
        echo "  WARNING: champsim_l1d_64kb binary not found. Build ChampSim first (SETUP.md §4)."
    fi
fi

echo ""
echo "=========================================="
echo " Experiments complete!"
echo " Now run:  python3 plot_results.py"
echo "=========================================="
