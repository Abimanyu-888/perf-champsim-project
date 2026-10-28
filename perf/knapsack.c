/*
 * knapsack.c  —  0/1 Knapsack Problem (bottom-up DP)
 *
 * Solves the 0/1 Knapsack exactly using a 2D DP table.
 * State: dp[i][w] = max value using first i items with capacity w.
 * Time:  O(n * W)
 * Space: O(n * W)
 *
 * For performance profiling:
 *   n=2000 items, W=500000 → table size ≈ 2000 * 500001 * 4 bytes ≈ 3.7 GB
 *   (Too large; use 1-D rolling array variant to keep working set at ~1.9 MB
 *    which fits in L2/L3 but NOT L1, giving interesting cache behaviour.)
 *
 * We intentionally use a large W so the 1-D dp[] array (W+1 ints ≈ 1.9 MiB)
 * exceeds L1D (typically 32–64 KiB) and exercises L2 prefetching.
 * This mirrors Coin Change from the reference report but uses a non-linear
 * access pattern because we sweep backwards for correctness.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

/* Problem parameters */
#define NUM_ITEMS   2000
#define CAPACITY    500000   /* W */

static int weight[NUM_ITEMS];
static int value[NUM_ITEMS];

/* 1-D DP array (rolling array optimisation — O(W) space) */
static int dp[CAPACITY + 1];

static void generate_items(unsigned seed)
{
    srand(seed);
    for (int i = 0; i < NUM_ITEMS; i++) {
        weight[i] = (rand() % 1000) + 1;  /* 1..1000  */
        value[i]  = (rand() % 1000) + 1;  /* 1..1000  */
    }
}

static int knapsack_01(void)
{
    memset(dp, 0, sizeof(dp));

    for (int i = 0; i < NUM_ITEMS; i++) {
        int wi = weight[i];
        int vi = value[i];
        /*
         * Sweep backwards so each item is only selected once.
         * This backward sweep is the key cache-behaviour difference vs.
         * Coin Change (which sweeps forward for unbounded items).
         * Backward access creates a strided, non-prefetchable pattern
         * when wi is large relative to cache-line coverage.
         */
        for (int w = CAPACITY; w >= wi; w--) {
            int candidate = dp[w - wi] + vi;
            if (candidate > dp[w])
                dp[w] = candidate;
        }
    }

    return dp[CAPACITY];
}

int main(void)
{
    generate_items(7);   /* fixed seed */

    printf("0/1 Knapsack DP  |  n=%d items, W=%d\n", NUM_ITEMS, CAPACITY);
    printf("dp[] array size  : ~%zu KiB\n",
           ((size_t)(CAPACITY + 1) * sizeof(int)) >> 10);

    clock_t t0 = clock();
    int ans = knapsack_01();
    clock_t t1 = clock();

    printf("Optimal value    : %d\n", ans);
    printf("CPU time         : %.4f s\n", (double)(t1 - t0) / CLOCKS_PER_SEC);

    /* Simple checksum */
    printf("Checksum         : %d\n", ans ^ (NUM_ITEMS * 54321));
    return 0;
}
