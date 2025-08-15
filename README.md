## Problem

  Given a positive integer n, α(n) is the minimum number of sets whose power 
  sets' union has exactly n elements.

  **Examples:**
  - α(12) = 2 because |2^{0,2,3} ∪ 2^{1,2,3}| = 12
  - α(13) = 3 because |2^{0,1,5} ∪ 2^{2,3} ∪ 2^{4,5}| = 13
  - α(419) = 4 because |2^S₁ ∪ 2^S₂ ∪ 2^S₃ ∪ 2^S₄| = 419 where
    S₁={0,1,2,4,5,12,13,14}, S₂={3,6,7,8,9,15}, S₃={4,5,6,7,8,9}, S₄={10,11,12,13,14,15}

  ## Main Result

  At SAT 2025, Kuldeep Meel asked in connection to his [paper](https://doi.org/10.4230/LIPIcs.SAT.2025.9): 
  "What is the smallest number that cannot be expressed as the union of 4 power sets?"

  **Answer: 238,117**

  This is the first value where α(n) > 4. We found this through exhaustive 
  search up to 65,535 and verification using constraint programming.

  ## Key Sequence

  The smallest n requiring exactly k power sets:

  | k    | n       | Binary                   |
  | ---- | :------ | ------------------------ |
  | 1    | 1       | 1                        |
  | 2    | 3       | 11                       |
  | 3    | 13      | 1101                     |
  | 4    | 419     | 110100011                |
  | 5    | 238,117 | 111010001000100101       |

  ## Tools

  Four Python scripts using [CP-SAT](https://developers.google.com/optimization/cp/cp_solver) constraint solver:

  - `cpsat_solver.py` - Test if α(n) ≤ k
  - `find_decomposition.py` - Find explicit sets and output to ADF format
  - `search_sequential.py` - Search ranges for α(n) > k
  - `exhaustive_verify.py` - Brute-force verification
  - `adf_verifier.py` - Verify ADF decomposition files

  ## Quick Start

  ```bash
  # Install uv
  curl -LsSf https://astral.sh/uv/install.sh | sh

  # Test Meel's number
  uv run cpsat_solver.py 238117 4
  # Output: ✗ α(238117) > 4

  # Find decomposition
  uv run find_decomposition.py 13 3
  # Output: Creates n_13_k3.adf with the sets

  # Search a range
  uv run search_sequential.py --k 3 --start 400 --end 500
  # Output: Found n=419
  ```

  Python 3.11+ required. No other dependencies - [uv](https://docs.astral.sh/uv/) handles everything.

  ## ADF Format

  Decompositions are stored in ADF (Alpha Decomposition Format), a simple text format:

  ```
  c Comment lines start with 'c'
  p alpha 13 3        # Problem: α(13) with 3 sets
  s 1 0 1 5 0        # Set 1: {0, 1, 5}
  s 2 2 3 0          # Set 2: {2, 3}
  s 3 4 5 0          # Set 3: {4, 5}
  ```

  Verify with: `python adf_verifier.py file.adf`