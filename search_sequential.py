#!/usr/bin/env python3
"""
Sequential search for values with α(n) > k.
Saves progress and can be resumed.
Usage: uv run search_sequential.py --k <k> --start <start> [--end <end>]
Example: uv run search_sequential.py --k 4 --start 1 --end 65535
"""

# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "ortools",
# ]
# ///

import time
import json
import os
from datetime import datetime
from ortools.sat.python import cp_model


def popcount(x):
    """Count set bits in integer."""
    return bin(x).count('1')


def alpha_leq_k_fast(n, k, last_hint=None):
    """Fast CP-SAT check with solution hints for consecutive n."""
    if n <= 0:
        return False, None
    
    masks = list(range(1, 2**k))
    M = min(n.bit_length() + 4, 60)
    powers = [1 << t for t in range(M + 1)]
    
    model = cp_model.CpModel()
    
    d = {mask: model.NewIntVar(0, M, f"d_{mask}") for mask in masks}
    y = {mask: model.NewIntVar(1, powers[-1], f"y_{mask}") for mask in masks}
    r = {mask: model.NewIntVar(0, M, f"r_{mask}") for mask in masks}
    
    for mask in masks:
        model.AddElement(d[mask], powers, y[mask])
    
    for mask1 in masks:
        for mask2 in masks:
            if mask1 != mask2 and (mask1 & mask2) == mask2:
                model.Add(d[mask1] <= d[mask2])
    
    for K in masks:
        terms = []
        for J in masks:
            if (J & K) == K:
                sign = 1 if (popcount(J) - popcount(K)) % 2 == 0 else -1
                terms.append(sign * d[J])
        model.Add(sum(terms) == r[K])
    
    singletons = [1 << i for i in range(k)]
    for i in range(len(singletons) - 1):
        model.Add(d[singletons[i]] >= d[singletons[i+1]])
    
    ie_sum = sum((1 if popcount(mask) % 2 == 1 else -1) * y[mask] for mask in masks)
    model.Add(ie_sum == n)
    
    # Add solution hints from previous solve
    if last_hint:
        for mask in masks:
            if mask in last_hint:
                model.AddHint(d[mask], last_hint[mask])
    
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    solver.parameters.cp_model_presolve = True
    
    status = solver.Solve(model)
    
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        d_vals = {mask: solver.Value(d[mask]) for mask in masks}
        return True, d_vals
    else:
        return False, None


def save_progress(k, n, found_list, start_time, total_checks):
    """Save progress to JSON file."""
    progress = {
        "k": k,
        "last_n_checked": n,
        "found_alpha_gt_k": found_list,
        "elapsed_seconds": time.time() - start_time,
        "timestamp": datetime.now().isoformat(),
        "total_checks": total_checks
    }
    
    filename = f"search_progress_k{k}.json"
    with open(filename, "w") as f:
        json.dump(progress, f, indent=2)


def load_progress(k):
    """Load progress from JSON file."""
    filename = f"search_progress_k{k}.json"
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    return None


def search_range(k, start_n, end_n=None):
    """Search for values with α(n) > k in given range."""
    # Load previous progress if exists
    progress = load_progress(k)
    if progress and progress['k'] == k:
        print(f"Resuming from n={progress['last_n_checked']+1}")
        start_n = progress['last_n_checked'] + 1
        found = progress['found_alpha_gt_k']
        total_checks = progress.get('total_checks', 0)
    else:
        found = []
        total_checks = 0
    
    if end_n:
        print(f"Searching for α(n) > {k} from n={start_n} to n={end_n}")
    else:
        print(f"Searching for α(n) > {k} starting from n={start_n}")
    print(f"Start time: {datetime.now().isoformat()}\n")
    
    start_time = time.time()
    n = start_n
    checked = 0
    last_report = time.time()
    last_hint = None
    
    try:
        while True:
            if end_n and n > end_n:
                break
            
            # CP-SAT check with hints
            feasible, d_vals = alpha_leq_k_fast(n, k, last_hint)
            
            if not feasible:
                print(f"✓ Found: α({n}) > {k} (binary: {bin(n)[2:]})")
                found.append(n)
                save_progress(k, n, found, start_time, total_checks + checked)
                last_hint = None  # Reset hints after finding α > k
            else:
                last_hint = d_vals  # Use as hint for next value
            
            checked += 1
            n += 1
            
            # Progress report every 30 seconds
            if time.time() - last_report > 30:
                elapsed = time.time() - start_time
                rate = checked / elapsed if elapsed > 0 else 0
                print(f"Progress: n={n}, checked {checked:,} values, rate={rate:.1f}/sec")
                save_progress(k, n-1, found, start_time, total_checks + checked)
                last_report = time.time()
            
            # Milestone reports
            if n % 10000 == 0:
                print(f"Milestone: n={n:,}")
    
    except KeyboardInterrupt:
        print(f"\nInterrupted at n={n}")
        save_progress(k, n-1, found, start_time, total_checks + checked)
        print("Progress saved. Resume by running the script again.")
        return
    
    # Summary
    elapsed = time.time() - start_time
    print("\nCompleted search")
    print(f"Time: {elapsed/60:.1f} minutes")
    print(f"Values checked: {checked:,}")
    print(f"Rate: {checked/elapsed:.1f} values/second" if elapsed > 0 else "")
    
    if found:
        print(f"\nFound {len(found)} values with α(n) > {k}:")
        for f in found[:10]:  # Show first 10
            print(f"  n={f} (binary: {bin(f)[2:]})")
        if len(found) > 10:
            print(f"  ... and {len(found)-10} more")


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__, 
                                   formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--k', type=int, required=True, help='Number of sets')
    parser.add_argument('--start', type=int, required=True, help='Starting value')
    parser.add_argument('--end', type=int, help='Ending value (optional)')
    
    args = parser.parse_args()
    
    search_range(args.k, args.start, args.end)


if __name__ == "__main__":
    main()