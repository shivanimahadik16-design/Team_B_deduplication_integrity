"""
Benchmark Team B hash-index implementations.

Compares:
    1. HashMapIndex
    2. AVLTree
    3. RBTree

Measures:
    - Average lookup time
    - P95 lookup time
    - Memory usage
"""

import gc
import statistics
import time
import tracemalloc

from app.index.hashmap_index import HashMapIndex
from app.index.avl_tree import AVLTree
from app.index.rb_tree import RBTree


DATASET_SIZES = [1000, 5000, 10000]
LOOKUPS_PER_SIZE = 1000


def build_hashmap(size: int) -> HashMapIndex:
    index = HashMapIndex()

    for i in range(size):
        index.insert(f"hash_{i}", f"chunk_{i}")

    return index


def build_avl(size: int) -> AVLTree:
    tree = AVLTree()

    for i in range(size):
        tree.insert(f"hash_{i}", f"chunk_{i}")

    return tree


def build_rb_tree(size: int) -> RBTree:
    tree = RBTree()

    for i in range(size):
        tree.insert(f"hash_{i}", f"chunk_{i}")

    return tree


def measure_lookup(index, size: int, lookup_count: int = LOOKUPS_PER_SIZE):
    """
    Measure repeated lookup latency.

    Returns:
        average lookup time in microseconds
        p95 lookup time in microseconds
    """

    # Warm-up
    for i in range(min(100, size)):
        index.lookup(f"hash_{i}")

    timings_us = []

    for i in range(lookup_count):
        key = f"hash_{i % size}"

        start = time.perf_counter_ns()
        result = index.lookup(key)
        elapsed_ns = time.perf_counter_ns() - start

        # Make sure lookup really happened.
        if result is None:
            raise RuntimeError(f"Lookup failed for key: {key}")

        timings_us.append(elapsed_ns / 1000)

    average_us = statistics.mean(timings_us)

    sorted_timings = sorted(timings_us)
    p95_position = int(0.95 * len(sorted_timings)) - 1
    p95_us = sorted_timings[max(0, p95_position)]

    return average_us, p95_us


def measure_memory(builder, size: int):
    """
    Measure memory allocated while building an index.

    Returns memory allocated in KiB.
    """

    gc.collect()
    tracemalloc.start()

    snapshot_before = tracemalloc.take_snapshot()

    index = builder(size)

    snapshot_after = tracemalloc.take_snapshot()

    stats = snapshot_after.compare_to(snapshot_before, "lineno")

    allocated_bytes = sum(
        max(0, stat.size_diff)
        for stat in stats
    )

    tracemalloc.stop()

    return index, allocated_bytes / 1024


def benchmark():
    implementations = [
        ("HashMap", build_hashmap),
        ("AVL", build_avl),
        ("RedBlack", build_rb_tree),
    ]

    print("=" * 80)
    print("TEAM B HASH INDEX BENCHMARK")
    print("=" * 80)

    for size in DATASET_SIZES:
        print(f"\nDataset size: {size:,}")
        print("-" * 80)

        print(
            f"{'Index':<12}"
            f"{'Avg (us)':>15}"
            f"{'P95 (us)':>15}"
            f"{'Memory (KiB)':>18}"
        )

        for name, builder in implementations:
            index, memory_kib = measure_memory(builder, size)

            average_us, p95_us = measure_lookup(
                index,
                size,
            )

            print(
                f"{name:<12}"
                f"{average_us:>15.3f}"
                f"{p95_us:>15.3f}"
                f"{memory_kib:>18.2f}"
            )

    print("\nBenchmark complete.")


if __name__ == "__main__":
    benchmark()