#!/usr/bin/env python3
"""
Check if α(n) ≤ k using CP-SAT solver.
Usage: uv run cpsat_solver.py <n> <k>
Example: uv run cpsat_solver.py 238117 4
"""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "ortools",
# ]
# ///

import sys
import time
from itertools import combinations
from ortools.sat.python import cp_model


def popcount(x):
    """Count set bits in integer."""
    return bin(x).count('1')


def get_subset_masks(k):
    """Get all 2^k - 1 nonempty subset masks for k sets."""
    return list(range(1, 2**k))


def alpha_leq_k(n, k, max_slack_bits=4, time_limit_s=None):
    """
    Check if α(n) ≤ k using CP-SAT solver.
    Returns (feasible, d_values) where d_values[mask] = |intersection of sets in mask|
    """
    if n <= 0:
        return False, None
    
    # All nonempty subsets
    masks = get_subset_masks(k)
    
    # Maximum set size bound
    M = min(n.bit_length() + max_slack_bits, 60)
    powers = [1 << t for t in range(M + 1)]
    
    model = cp_model.CpModel()
    
    # Variables: d[mask] = size of intersection of sets indicated by mask
    d = {mask: model.NewIntVar(0, M, f"d_{mask}") for mask in masks}
    y = {mask: model.NewIntVar(1, powers[-1], f"y_{mask}") for mask in masks}
    
    # y[mask] = 2^{d[mask]}
    for mask in masks:
        model.AddElement(d[mask], powers, y[mask])
    
    # Monotonicity: if mask1 ⊇ mask2, then d[mask1] ≤ d[mask2]
    for mask1 in masks:
        for mask2 in masks:
            if mask1 != mask2 and (mask1 & mask2) == mask2:  # mask1 is superset
                model.Add(d[mask1] <= d[mask2])
    
    # Region constraints via Möbius inversion - ensure non-negative region sizes
    for K in masks:
        terms = []
        for J in masks:
            if (J & K) == K:  # J is superset of K
                sign = 1 if (popcount(J) - popcount(K)) % 2 == 0 else -1
                terms.append(sign * d[J])
        model.Add(sum(terms) >= 0)  # Region sizes must be non-negative
    
    # Symmetry breaking: order singleton sets
    singletons = [1 << i for i in range(k)]
    for i in range(len(singletons) - 1):
        if singletons[i] in d and singletons[i+1] in d:
            model.Add(d[singletons[i]] >= d[singletons[i+1]])
    
    # Inclusion-exclusion: sum equals n
    ie_sum = sum((1 if popcount(mask) % 2 == 1 else -1) * y[mask] for mask in masks)
    model.Add(ie_sum == n)
    
    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    if time_limit_s:
        solver.parameters.max_time_in_seconds = float(time_limit_s)
    
    status = solver.Solve(model)
    
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        d_vals = {mask: solver.Value(d[mask]) for mask in masks}
        return True, d_vals
    else:
        return False, None


def print_solution(k, d_vals):
    """Print the intersection sizes in a readable format."""
    print(f"\nFound {k}-set decomposition:")
    
    # Singletons
    print("Set sizes:")
    for i in range(k):
        mask = 1 << i
        if mask in d_vals:
            print(f"  |S_{i+1}| = {d_vals[mask]}")
    
    # Pairs
    pairs = [(i, j) for i in range(k) for j in range(i+1, k)]
    if pairs:
        print("Pairwise intersections:")
        for i, j in pairs:
            mask = (1 << i) | (1 << j)
            if mask in d_vals:
                print(f"  |S_{i+1} ∩ S_{j+1}| = {d_vals[mask]}")
    
    # Higher order intersections
    for size in range(3, k+1):
        combos = list(combinations(range(k), size))
        if combos:
            print(f"{size}-way intersections:")
            for indices in combos:
                mask = sum(1 << i for i in indices)
                if mask in d_vals:
                    sets = " ∩ ".join(f"S_{i+1}" for i in indices)
                    print(f"  |{sets}| = {d_vals[mask]}")


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    
    n = int(sys.argv[1])
    k = int(sys.argv[2])
    
    print(f"Checking if α({n}) ≤ {k}")
    print(f"Binary: {bin(n)[2:]}")
    
    start = time.perf_counter()
    feasible, d_vals = alpha_leq_k(n, k)
    elapsed = time.perf_counter() - start
    
    if feasible:
        print(f"\n✓ α({n}) ≤ {k} (solved in {elapsed*1000:.1f}ms)")
        print_solution(k, d_vals)
    else:
        print(f"\n✗ α({n}) > {k} (proved in {elapsed*1000:.1f}ms)")


if __name__ == "__main__":
    main()