import unittest
import os
import sys
import glob
import time
import statistics
import gc
import shutil

# Add scripts to path to import get_actor_name
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, 'scripts')
TESTS_DIR = os.path.join(PROJECT_ROOT, 'tests')
sys.path.append(SCRIPTS_DIR)

try:
    import get_actor_name
except ImportError:
    raise ImportError("Could not import 'get_actor_name'. Check path configuration.")


def generate_performance_data(target_dir, target_count=2000):
    """Generate test files by copying from version folders."""
    import re

    # Find version folders
    source_files = []
    for entry in os.listdir(TESTS_DIR):
        if re.match(r'^\d+_\d+$', entry):
            folder = os.path.join(TESTS_DIR, entry)
            if os.path.isdir(folder):
                source_files.extend(glob.glob(os.path.join(folder, '*.uasset')))

    if not source_files:
        return 0

    os.makedirs(target_dir, exist_ok=True)

    count = 0
    iteration = 0
    while count < target_count:
        for src in source_files:
            if count >= target_count:
                break
            name = os.path.basename(src)
            base, ext = os.path.splitext(name)
            dest = os.path.join(target_dir, f"{base}_{iteration}{ext}")
            shutil.copy2(src, dest)
            count += 1
        iteration += 1

    return count


class TestPerformance(unittest.TestCase):

    _generated = False  # Track if we generated the data

    def setUp(self):
        self.test_dir = os.path.join(PROJECT_ROOT, 'tests', 'big_performance_test')

        # Auto-generate if missing
        if not os.path.exists(self.test_dir):
            print("\n[Performance Test] Generating test data (2000 files)...")
            count = generate_performance_data(self.test_dir, 2000)
            if count == 0:
                self.skipTest("No source files in version folders (5_3/, 5_4/, etc.)")
            print(f"[Performance Test] Generated {count} files")
            TestPerformance._generated = True

        self.files = glob.glob(os.path.join(self.test_dir, "**/*.uasset"), recursive=True)
        if not self.files:
            self.skipTest("No .uasset files found for performance test.")

    def test_processing_speed(self):
        """
        Benchmark the parser speed. 
        Expects average time per file to be < 0.2 ms (Python Optimized).
        """
        runs = 5
        warmup = 1
        
        # Workload
        def workload():
            for f in self.files:
                # Direct API call, bypassing CLI overhead
                try:
                    parser = get_actor_name.UAssetParser(f)
                    if parser.parse_name_map():
                        parser.extract_label_property()
                except Exception:
                    pass

        # Warmup
        for _ in range(warmup):
            workload()

        # Measure
        timings_ms = []
        gc_enabled = gc.isenabled()
        gc.disable() # Disable GC for stable micro-benchmarking
        
        try:
            for _ in range(runs):
                start = time.perf_counter_ns()
                workload()
                end = time.perf_counter_ns()
                timings_ms.append((end - start) / 1_000_000)
        finally:
            if gc_enabled:
                gc.enable()

        avg_total_time = statistics.mean(timings_ms)
        min_total_time = min(timings_ms)
        max_total_time = max(timings_ms) # using max for worst case
        median_total_time = statistics.median(timings_ms)
        
        avg_per_file = avg_total_time / len(self.files)
        
        stats_msg = (
            f"\nBenchmark Results (runs={runs}, files={len(self.files)}):\n"
            f"  Total Time (ms): min={min_total_time:.3f} | avg={avg_total_time:.3f} | median={median_total_time:.3f} | max={max_total_time:.3f}\n"
            f"  Per File   (ms): avg={avg_per_file:.4f}"
        )
        print(stats_msg)

        # Threshold: 0.20ms per file (Optimized Python is ~0.09ms, so this gives ~2x buffer)
        # If unoptimized, it was ~0.16ms-0.2ms, so this is tight but safe for "Optimized" status.
        THRESHOLD_PER_FILE_MS = 0.20
        
        self.assertLess(
            avg_per_file,
            THRESHOLD_PER_FILE_MS,
            f"Performance regression! {avg_per_file:.4f} ms/file > {THRESHOLD_PER_FILE_MS} ms/file"
        )

    @classmethod
    def tearDownClass(cls):
        """Clean up generated test data."""
        test_dir = os.path.join(PROJECT_ROOT, 'tests', 'big_performance_test')
        if cls._generated and os.path.exists(test_dir):
            shutil.rmtree(test_dir)
            print(f"\n[Performance Test] Cleaned up: {test_dir}")


if __name__ == '__main__':
    unittest.main()
