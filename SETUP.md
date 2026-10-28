# SETUP.md  —  perf-champsim-project (TSP & Knapsack)

**Authors:** Abimanyu Choudhary K (106124006) · Yuvraj Meena (106124142)

---

## Overview

This document provides **complete step-by-step instructions** to reproduce every experiment in our Computer Architecture assignment report. All native perf benchmarks must run on a **Linux machine** (VM or bare-metal). ChampSim simulation can also run on Linux.

```
perf-champsim-project/
├── perf/
│   ├── tsp.c              ← Held-Karp TSP benchmark
│   └── knapsack.c         ← 0/1 Knapsack benchmark
├── bin/                   ← compiled binaries (created by you)
├── results/               ← all output files go here
├── traces/                ← ChampSim trace (download separately)
├── champsim_config_32kb.json
├── champsim_config_64kb.json
├── plot_results.py        ← Python plotting script
├── run_experiments.sh     ← one-shot experiment runner
└── report/
    └── report.tex         ← LaTeX source for the PDF report
```

---

## §1  System Requirements

| Item | Requirement |
|---|---|
| OS | Linux (Ubuntu 20.04+ / Fedora 38+ recommended) |
| Compiler | GCC ≥ 9  (`gcc --version`) |
| perf | `linux-tools-$(uname -r)` or distro equivalent |
| Python | 3.8+ with `matplotlib`, `pandas` |
| LaTeX | TeX Live / MiKTeX (`pdflatex`, `bibtex`) |
| ChampSim deps | `cmake` ≥ 3.15, `g++` ≥ 9, `zlib1g-dev` |

---

## §2  Python Virtual Environment

```bash
cd ~/perf-champsim-project
python3 -m venv .venv
source .venv/bin/activate
pip install matplotlib pandas
```

---

## §3  Compiling and Running Native Benchmarks

### 3.1  Compile

```bash
cd ~/perf-champsim-project
gcc -O2 perf/tsp.c      -o bin/tsp
gcc -O2 perf/knapsack.c -o bin/knapsack
```

### 3.2  Verify correctness

```bash
./bin/tsp
./bin/knapsack
```

Both should print an `Optimal` result and a `Checksum` line within a few seconds.

### 3.3  Profile with perf

**TSP (Held-Karp):**
```bash
perf stat -r 3 \
  -e task-clock,context-switches,cpu-migrations,page-faults,\
cycles,instructions,branches,branch-misses,cache-references,cache-misses \
  ./bin/tsp 2>&1 | tee results/tsp_perf.txt
```

**Knapsack (0/1 DP):**
```bash
perf stat -r 3 \
  -e task-clock,context-switches,cpu-migrations,page-faults,\
cycles,instructions,branches,branch-misses,cache-references,cache-misses \
  ./bin/knapsack 2>&1 | tee results/knapsack_perf.txt
```

> **Tip:** If perf says `Permission denied`, run:
> ```bash
> sudo sysctl kernel.perf_event_paranoid=1
> ```

---

## §4  ChampSim Setup

### 4.1  Clone and build

```bash
cd ~
git clone https://github.com/ChampSim/ChampSim.git champsim
cd champsim
```

### 4.2  Build 32 KiB L1D binary

```bash
python3 config.py ~/perf-champsim-project/champsim_config_32kb.json
make -j$(nproc)
cp bin/champsim ~/perf-champsim-project/bin/champsim_l1d_32kb
```

### 4.3  Build 64 KiB L1D binary

```bash
python3 config.py ~/perf-champsim-project/champsim_config_64kb.json
make -j$(nproc)
cp bin/champsim ~/perf-champsim-project/bin/champsim_l1d_64kb
```

### 4.4  Download SPEC CPU trace

```bash
mkdir -p ~/perf-champsim-project/traces
# Download the standard Perlbench trace (requires academic access):
# https://dpc3.compas.cs.stonybrook.edu/champsimtrace.php
# Place the file at:
#   ~/perf-champsim-project/traces/400.perlbench-41B.champsimtrace.xz
```

### 4.5  Run ChampSim simulations

```bash
cd ~/perf-champsim-project

# 32 KiB control
./bin/champsim_l1d_32kb \
  --warmup-instructions 100000 \
  --simulation-instructions 1000000 \
  --json results/perlbench_32kb.json \
  traces/400.perlbench-41B.champsimtrace.xz \
  2>&1 | tee results/perlbench_32kb.txt

# 64 KiB experiment
./bin/champsim_l1d_64kb \
  --warmup-instructions 100000 \
  --simulation-instructions 1000000 \
  --json results/perlbench_64kb.json \
  traces/400.perlbench-41B.champsimtrace.xz \
  2>&1 | tee results/perlbench_64kb.txt
```

---

## §5  Generate Plots

```bash
cd ~/perf-champsim-project
source .venv/bin/activate
python3 plot_results.py
```

Plots will appear in `results/`:

| File | Content |
|---|---|
| `fig_ipc_bar.pdf` | IPC comparison TSP vs Knapsack |
| `fig_cache_bar.pdf` | Cache miss rate comparison |
| `fig_branch_bar.pdf` | Branch miss rate comparison |
| `fig_champsim_ipc.pdf` | ChampSim IPC 32 KiB vs 64 KiB |
| `fig_champsim_misses.pdf` | ChampSim L1D misses comparison |

---

## §6  Build the LaTeX Report

```bash
cd ~/perf-champsim-project/report
pdflatex report.tex
bibtex report
pdflatex report.tex
pdflatex report.tex   # third pass for cross-references
```

Output: `report/report.pdf`

---

## §7  One-Shot Runner (after ChampSim is set up)

```bash
cd ~/perf-champsim-project
bash run_experiments.sh
source .venv/bin/activate
python3 plot_results.py
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `perf: Permission denied` | `sudo sysctl kernel.perf_event_paranoid=1` |
| TSP takes too long | Reduce `N` in `tsp.c` (try 18) and recompile |
| ChampSim build fails | Ensure `cmake ≥ 3.15` and `g++ ≥ 9` |
| Plots show zeros | Check that `results/tsp_perf.txt` and `results/knapsack_perf.txt` exist |
| LaTeX `file not found` for figures | Run `python3 plot_results.py` before `pdflatex` |
