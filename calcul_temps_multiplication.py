# -*- coding: utf-8 -*-
"""
Created on Sat Apr 11 14:42:05 2026

@author: Pierre Guéno
"""
#%% LIBRARIES
import subprocess
import time
import numpy as np
import sys
# ─────────────────────────────────────────────
#%% CONFIGURATION
# ─────────────────────────────────────────────
CPP_SOURCE  = r"C:\Users\pierr\OneDrive - IPSA\Documents\IPSA\Aero 4\Semestre 2\In422 - Systèmes d'Information Temps Réel\final assignment\multiplication.cpp"
EXECUTABLE  = r"C:\Users\pierr\OneDrive - IPSA\Documents\IPSA\Aero 4\Semestre 2\In422 - Systèmes d'Information Temps Réel\final assignment\multiplication.exe"
NB_ITERATIONS = 5000

print(f"NB_ITERATIONS= {NB_ITERATIONS}")
# ─────────────────────────────────────────────
# COMPILATION
# ─────────────────────────────────────────────
print("Compiling C++ code...")
compile_cmd = ["g++", CPP_SOURCE, "-o", EXECUTABLE]
compile_result = subprocess.run(compile_cmd, capture_output=True, text=True)

if compile_result.returncode != 0:
    print("Compilation error:")
    print(compile_result.stderr)
    sys.exit(1)

print("Compilation successful.\n")

times = []

for i in range(NB_ITERATIONS):
    start = time.perf_counter()
    run_result = subprocess.run([EXECUTABLE], capture_output=True, text=True)
    end = time.perf_counter()

    if run_result.returncode != 0:
        print(f"Error at iteration {i+1}: {run_result.stderr}")
        sys.exit(1)

    elapsed = end - start
    times.append(elapsed)
    print(f"Iteration {i+1:>3}/{NB_ITERATIONS} — {elapsed:.6f} s")

#%% RESULTS

Min = np.min(times)
Max = np.max(times)
Q1 = np.percentile(times, 25)
Q2 = np.percentile(times, 50)
Q3 = np.percentile(times, 75)
