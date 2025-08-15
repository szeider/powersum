#!/usr/bin/env python3
"""
ADF (Alpha Decomposition Format) parser and verifier.
Verifies that a decomposition file correctly represents α(n) ≤ k.
Usage: python adf_verifier.py <file.adf>
"""

import sys
from pathlib import Path
from itertools import combinations


def parse_adf(filename):
    """Parse an ADF file and return (n, k, sets)."""
    n = k = None
    sets = []
    expected_set_id = 1
    
    with open(filename, 'r') as f:
        for line in f:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Comment line
            if line.startswith('c'):
                continue
            
            # Problem line
            if line.startswith('p'):
                parts = line.split()
                if len(parts) != 4 or parts[1] != 'alpha':
                    raise ValueError(f"Invalid problem line: {line}")
                n = int(parts[2])
                k = int(parts[3])
                if n <= 0 or k <= 0:
                    raise ValueError(f"n and k must be positive: n={n}, k={k}")
            
            # Set line
            elif line.startswith('s'):
                if n is None or k is None:
                    raise ValueError("Set line before problem line")
                
                parts = line.split()
                if len(parts) < 3:
                    raise ValueError(f"Invalid set line: {line}")
                
                set_id = int(parts[1])
                if set_id != expected_set_id:
                    raise ValueError(f"Expected set {expected_set_id}, got {set_id}")
                
                # Parse elements (everything between set_id and final 0)
                if parts[-1] != '0':
                    raise ValueError(f"Set line must end with 0: {line}")
                
                elements = []
                for elem in parts[2:-1]:
                    val = int(elem)
                    if val < 0:
                        raise ValueError(f"Negative element {val} in set {set_id}")
                    elements.append(val)
                
                sets.append(set(elements))
                expected_set_id += 1
            
            else:
                raise ValueError(f"Unknown line type: {line}")
    
    # Validate we got exactly k sets
    if len(sets) != k:
        raise ValueError(f"Expected {k} sets, got {len(sets)}")
    
    return n, k, sets


def compute_union_size(sets):
    """Compute |2^S1 ∪ 2^S2 ∪ ... ∪ 2^Sk| using inclusion-exclusion."""
    k = len(sets)
    if k == 0:
        return 0
    
    # Compute all intersection sizes
    masks = list(range(1, 2**k))
    intersection_sizes = {}
    
    for mask in masks:
        # Find intersection of sets indicated by mask
        intersection = None
        for i in range(k):
            if mask & (1 << i):
                if intersection is None:
                    intersection = sets[i].copy()
                else:
                    intersection = intersection & sets[i]
        intersection_sizes[mask] = len(intersection) if intersection else 0
    
    # Apply inclusion-exclusion principle
    result = 0
    for mask in masks:
        bits = bin(mask).count('1')
        sign = 1 if bits % 2 == 1 else -1
        result += sign * (1 << intersection_sizes[mask])
    
    return result


def verify_decomposition(n, k, sets):
    """Verify that the sets form a valid α(n) ≤ k decomposition."""
    union_size = compute_union_size(sets)
    
    if union_size == n:
        return True, union_size
    else:
        return False, union_size


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    
    filename = sys.argv[1]
    if not Path(filename).exists():
        print(f"Error: File '{filename}' not found")
        sys.exit(1)
    
    try:
        # Parse the file
        n, k, sets = parse_adf(filename)
        print(f"Parsed: α({n}) ≤ {k} decomposition")
        
        # Show the sets
        for i, S in enumerate(sets, 1):
            if S:
                elements = ', '.join(map(str, sorted(S)))
                print(f"  S{i} = {{{elements}}}")
            else:
                print(f"  S{i} = ∅")
        
        # Verify the decomposition
        print(f"\nVerifying |2^S1 ∪ ... ∪ 2^S{k}| = {n}...")
        valid, actual_size = verify_decomposition(n, k, sets)
        
        if valid:
            print(f"✓ Valid decomposition: union size = {actual_size}")
        else:
            print(f"✗ Invalid decomposition: union size = {actual_size} ≠ {n}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()