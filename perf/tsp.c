/*
 * tsp.c  —  Traveling Salesman Problem (Held-Karp DP)
 *
 * Solves TSP exactly for N cities using bitmask dynamic programming.
 * State: dp[S][i] = min cost to visit all cities in subset S, ending at city i.
 * Time:  O(2^N * N^2)
 * Space: O(2^N * N)
 *
 * For performance profiling purposes, N=20 gives a working set of:
 *   2^20 * 20 * 4 bytes = ~80 MB  → stresses L2/L3 cache.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include <time.h>

#define N 20          /* number of cities */
#define INF INT_MAX/2 /* safe infinity */

/* Distance matrix — generated with a fixed seed for reproducibility */
static int dist[N][N];

/* DP table: dp[mask][city] */
/* Allocated on heap to avoid stack overflow for large N              */
static int (*dp)[N];

/* Predecessor table for path reconstruction */
static int (*parent)[N];

static void generate_distances(unsigned seed)
{
    srand(seed);
    for (int i = 0; i < N; i++) {
        dist[i][i] = 0;
        for (int j = i + 1; j < N; j++) {
            int d = (rand() % 100) + 1; /* 1..100 */
            dist[i][j] = d;
            dist[j][i] = d;
        }
    }
}

static int held_karp(void)
{
    int states = 1 << N;
    dp     = malloc(sizeof(int)  * states * N);
    parent = malloc(sizeof(int)  * states * N);

    if (!dp || !parent) {
        fprintf(stderr, "Memory allocation failed\n");
        exit(1);
    }

    /* Initialise all entries to INF / -1 */
    for (int s = 0; s < states; s++)
        for (int i = 0; i < N; i++) {
            dp[s][i]     = INF;
            parent[s][i] = -1;
        }

    /* Base case: start at city 0 (bit 0 set) */
    dp[1][0] = 0;

    /* Fill DP table */
    for (int mask = 1; mask < states; mask++) {
        if (!(mask & 1)) continue; /* city 0 must always be in set */
        for (int u = 0; u < N; u++) {
            if (!(mask & (1 << u))) continue;
            if (dp[mask][u] == INF)  continue;
            /* Try extending to city v not yet in mask */
            for (int v = 0; v < N; v++) {
                if (mask & (1 << v)) continue;
                int nmask = mask | (1 << v);
                int ncost = dp[mask][u] + dist[u][v];
                if (ncost < dp[nmask][v]) {
                    dp[nmask][v]     = ncost;
                    parent[nmask][v] = u;
                }
            }
        }
    }

    /* Find optimal return to city 0 */
    int full = states - 1;
    int best = INF, last = -1;
    for (int u = 1; u < N; u++) {
        if (dp[full][u] == INF) continue;
        int total = dp[full][u] + dist[u][0];
        if (total < best) {
            best = total;
            last = u;
        }
    }

    /* (Optional) reconstruct tour — just to exercise parent[] memory */
    if (last >= 0) {
        int cur_mask = full, cur = last;
        while (cur != -1) {
            int prev = parent[cur_mask][cur];
            if (prev == -1) break;
            cur_mask ^= (1 << cur);
            cur = prev;
        }
    }

    free(dp);
    free(parent);
    return best;
}

int main(void)
{
    /* Use a fixed seed so results are reproducible */
    generate_distances(42);

    printf("TSP Held-Karp DP  |  N=%d cities\n", N);
    printf("Working-set size  : ~%zu MiB\n",
           ((size_t)(1 << N) * N * sizeof(int) * 2) >> 20);

    clock_t t0 = clock();
    int ans = held_karp();
    clock_t t1 = clock();

    printf("Optimal tour cost : %d\n", ans);
    printf("CPU time          : %.4f s\n", (double)(t1 - t0) / CLOCKS_PER_SEC);

    /* Simple checksum for verification */
    printf("Checksum          : %d\n", ans ^ (N * 12345));
    return 0;
}
