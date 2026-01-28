import argparse
import contextlib
import gc
import os
import statistics
import sys
import time
import glob

# Import the module to be benchmarked
import get_actor_name

def _format_stats(times_ms, runs, total_files):
    return (
        "Benchmark (ms): runs={runs} files_per_run={files}\n"
        "  Total Time: min={min_v:.3f} avg={avg_v:.3f} max={max_v:.3f}\n"
        "  Per File:   avg={per_file:.3f}"
    ).format(
        runs=runs,
        files=total_files,
        min_v=min(times_ms),
        avg_v=statistics.mean(times_ms),
        max_v=statistics.median(times_ms), # Using median for average to be more robust
        per_file=statistics.mean(times_ms) / total_files if total_files > 0 else 0
    )

def _time_runs(action, runs, warmup=1, disable_gc=False):
    if runs < 1:
        raise ValueError("runs must be >= 1")
    if warmup < 0:
        raise ValueError("warmup must be >= 0")

    was_enabled = gc.isenabled()
    if disable_gc:
        gc.disable()

    try:
        # Warmup
        for _ in range(warmup):
            action()

        # Measured runs
        timings_ms = []
        for _ in range(runs):
            start = time.perf_counter_ns()
            action()
            timings_ms.append((time.perf_counter_ns() - start) / 1_000_000)
    finally:
        if disable_gc and was_enabled:
            gc.enable()

    return timings_ms

def process_single_file(file_path):
    """
    Encapsulates the logic of processing a single file using the parser.
    """
    try:
        parser = get_actor_name.UAssetParser(file_path)
        if parser.parse_name_map():
            parser.extract_label_property()
    except Exception:
        pass 

def run_benchmark(search_path, runs=3, warmup=1, disable_gc=False, recursive=True):
    search_path = os.path.abspath(search_path)
    
    files = []
    if os.path.isfile(search_path):
         files = [search_path]
         print(f"Benchmarking single file: {search_path}")
    else:
        print(f"Scanning for .uasset files in: {search_path}...")
        pattern = "**/*.uasset" if recursive else "*.uasset"
        files = glob.glob(os.path.join(search_path, pattern), recursive=recursive)
    
    if not files:
        return "No .uasset files found."
        
    print(f"Found {len(files)} files. Starting benchmark...")

    def workload():
        for f in files:
            process_single_file(f)

    with open(os.devnull, "w") as sink:
        with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            timings = _time_runs(
                workload,
                runs,
                warmup=warmup,
                disable_gc=disable_gc,
            )
    
    return _format_stats(timings, runs, len(files))

def main():
    parser = argparse.ArgumentParser(description="Benchmark get_actor_name.py performance.")
    parser.add_argument("path", nargs="?", default=".", help="Directory to search for .uasset files")
    parser.add_argument("--runs", type=int, default=3, help="Number of benchmark runs")
    parser.add_argument("--warmup", type=int, default=1, help="Number of warmup runs")
    parser.add_argument("--no-gc", action="store_true", help="Disable GC during timing")
    parser.add_argument("--no-recurse", action="store_true", help="Do not search recursively")

    args = parser.parse_args()

    print(
        run_benchmark(
            args.path,
            runs=args.runs,
            warmup=args.warmup,
            disable_gc=args.no_gc,
            recursive=not args.no_recurse
        )
    )

if __name__ == "__main__":
    main()

