#!/usr/bin/env python3
"""
Exhaustively verify if α(n) > k by trying all possible k-set configurations.
Usage: uv run exhaustive_verify.py <n> <k> [max_size]
Example: uv run exhaustive_verify.py 238117 4
"""

# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

import sys
import time
from itertools import product


def compute_union_size(sizes, k):
    """
    Compute |2^S1 ∪ ... ∪ 2^Sk| using inclusion-exclusion.
    sizes is a list of all intersection sizes in binary order.
    """
    result = 0
    num_masks = 2**k - 1
    
    for mask in range(1, num_masks + 1):
        # Count bits to determine sign
        bits = bin(mask).count('1')
        sign = 1 if bits % 2 == 1 else -1
        # sizes[mask-1] because we skip the empty set
        result += sign * (1 << sizes[mask - 1])
    
    return result


def check_constraints(sizes, k):
    """
    Check if the sizes satisfy all subset constraints.
    Returns True if valid, False otherwise.
    """
    masks = list(range(1, 2**k))
    
    # Check monotonicity: superset intersections ≤ subset intersections
    for mask1 in masks:
        for mask2 in masks:
            if mask1 != mask2 and (mask1 & mask2) == mask2:  # mask1 ⊇ mask2
                if sizes[mask1 - 1] > sizes[mask2 - 1]:
                    return False
    
    # Check region non-negativity via Möbius inversion
    for K in masks:
        region_size = 0
        for J in masks:
            if (J & K) == K:  # J ⊇ K
                bits_diff = bin(J).count('1') - bin(K).count('1')
                sign = 1 if bits_diff % 2 == 0 else -1
                region_size += sign * sizes[J - 1]
        if region_size < 0:
            return False
    
    return True


def exhaustive_search(n, k, max_size=None):
    """
    Exhaustively search for a k-set decomposition of n.
    Returns True if α(n) ≤ k, False if α(n) > k.
    """
    if max_size is None:
        # Proven bound: no set can be larger than floor(log2(n))
        max_size = n.bit_length() - 1 if n > 0 else 0
    
    print(f"Exhaustive search: α({n}) ≤ {k}?")
    print(f"Maximum set size: {max_size}")
    print(f"Binary of n: {bin(n)[2:]}")
    print()
    
    num_masks = 2**k - 1
    count = 0
    start_time = time.time()
    last_report = time.time()
    
    # Generate all possible size combinations
    # We need to assign a size to each of the 2^k - 1 nonempty intersections
    # Start with singleton sets (individual set sizes)
    singleton_masks = [1 << i for i in range(k)]
    
    # Try all possible sizes for singleton sets (with symmetry breaking)
    for singleton_sizes in product(range(max_size + 1), repeat=k):
        # Symmetry breaking: S1 ≥ S2 ≥ ... ≥ Sk
        if not all(singleton_sizes[i] >= singleton_sizes[i+1] for i in range(k-1)):
            continue
        
        # Initialize sizes array
        sizes = [0] * num_masks
        
        # Set singleton sizes
        for i, mask in enumerate(singleton_masks):
            sizes[mask - 1] = singleton_sizes[i]
        
        # Try all valid sizes for intersections
        ranges = []
        
        # Build ranges for each intersection based on constraints
        for mask in range(1, num_masks + 1):
            if mask in singleton_masks:
                continue
            
            # Find maximum based on subset constraints
            max_val = max_size
            for submask in range(1, num_masks + 1):
                if (mask & submask) == submask and mask != submask:
                    max_val = min(max_val, sizes[submask - 1])
            
            ranges.append(range(max_val + 1))
        
        # Try all combinations for non-singleton intersections
        non_singleton_masks = [m for m in range(1, num_masks + 1) if m not in singleton_masks]
        
        for intersection_sizes in product(*ranges):
            count += 1
            
            # Progress report
            if time.time() - last_report > 5:
                elapsed = time.time() - start_time
                print(f"Checked {count:,} configurations in {elapsed:.1f}s")
                last_report = time.time()
            
            # Fill in intersection sizes
            for i, mask in enumerate(non_singleton_masks):
                sizes[mask - 1] = intersection_sizes[i]
            
            # Check all constraints
            if not check_constraints(sizes, k):
                continue
            
            # Check if this gives n
            union_size = compute_union_size(sizes, k)
            
            if union_size == n:
                elapsed = time.time() - start_time
                print(f"\n✓ Found {k}-set decomposition!")
                print(f"Checked {count:,} configurations in {elapsed:.1f}s")
                print("\nSet sizes:")
                for i in range(k):
                    print(f"  |S_{i+1}| = {sizes[(1 << i) - 1]}")
                print(f"\nConclusion: α({n}) ≤ {k}")
                return True
    
    elapsed = time.time() - start_time
    print(f"\n✗ No {k}-set decomposition found!")
    print(f"Exhaustively checked {count:,} configurations in {elapsed:.1f}s")
    print(f"\nConclusion: α({n}) > {k}")
    return False


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    
    n = int(sys.argv[1])
    k = int(sys.argv[2])
    max_size = int(sys.argv[3]) if len(sys.argv) > 3 else None
    
    exhaustive_search(n, k, max_size)


if __name__ == "__main__":
    main()