import time
import random
import sys

sys.setrecursionlimit(20000)

class BenchmarkLab:

    @staticmethod
    def bubble_sort(arr): 
        n = len(arr)
        arr_copy = arr[:] 
        for i in range(n):
            for j in range(0, n-i-1):
                if arr_copy[j] > arr_copy[j+1]:
                    arr_copy[j], arr_copy[j+1] = arr_copy[j+1], arr_copy[j]
        return arr_copy

    @staticmethod
    def merge_sort(arr): 
        if len(arr) <= 1: return arr
        mid = len(arr) // 2
        left = BenchmarkLab.merge_sort(arr[:mid])
        right = BenchmarkLab.merge_sort(arr[mid:])
        
        res = []
        i = j = 0
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                res.append(left[i]); i += 1
            else:
                res.append(right[j]); j += 1
        res.extend(left[i:]); res.extend(right[j:])
        return res

    @staticmethod
    def linear_search(arr, target): 
        for i in range(len(arr)):
            if arr[i] == target: return True
        return False

    @staticmethod
    def binary_search(arr, target): 
        low, high = 0, len(arr) - 1
        while low <= high:
            mid = (low + high) // 2
            if arr[mid] == target: return True
            elif arr[mid] < target: low = mid + 1
            else: high = mid - 1
        return False

    @staticmethod
    def nested_loop_find(arr, k):
        n = len(arr)
        best_window = []
        min_diff = float('inf')
        for i in range(n - k + 1):
            window = arr[i : i+k] 
            diff = window[-1] - window[0]
            if diff < min_diff:
                min_diff = diff
                best_window = window
        return best_window

    @staticmethod
    def sliding_window_find(arr, k): 
        n = len(arr)
        best_window = []
        min_diff = float('inf')
        for i in range(n - k + 1):
            diff = arr[i+k-1] - arr[i]
            if diff < min_diff:
                min_diff = diff
                best_window = (i, i+k) 
        return best_window


    @staticmethod
    def measure(func, *args):
        start = time.perf_counter()
        func(*args)
        end = time.perf_counter()
        return (end - start) * 1000 


def run_tests():
    print("THỰC NGHIỆM HIỆU NĂNG GIẢI THUẬT")

    print("\nKịch bản 1: SẮP XẾP: Bubble Sort (O(N^2)) vs Merge Sort (O(N log N))")
    print("-" * 65)
    print(f"{'Size (N)':<15} | {'Bubble Sort (ms)':<20} | {'Merge Sort (ms)':<20}")
    print("-" * 65)
    
    sizes = [1000, 5000, 10000] 
    for n in sizes:
        data = [random.randint(1, 1000000) for _ in range(n)]
        
        t_bubble = BenchmarkLab.measure(BenchmarkLab.bubble_sort, data)
        t_merge = BenchmarkLab.measure(BenchmarkLab.merge_sort, data)
        
        print(f"{n:<15} | {t_bubble:<20.4f} | {t_merge:<20.4f}")

    print("\nKịch bản 2: TÌM KIẾM: Linear Search (O(N)) vs Binary Search (O(log N))")
    print("-" * 65)
    print(f"{'Size (N)':<15} | {'Linear Search (ms)':<20} | {'Binary Search (ms)':<20}")
    print("-" * 65)
    
    sizes = [100000, 1000000, 5000000]
    for n in sizes:
        data = sorted([random.randint(1, n*10) for _ in range(n)])
        target = data[-1] 
        
        t_linear = BenchmarkLab.measure(BenchmarkLab.linear_search, data, target)
        t_binary = BenchmarkLab.measure(BenchmarkLab.binary_search, data, target)
        
        print(f"{n:<15} | {t_linear:<20.4f} | {t_binary:<20.6f}")

    print("\nKịch bản 3: XẾP PHÒNG: Brute Force (O(N*K)) vs Sliding Window (O(N))")
    print("-" * 65)
    print(f"{'Size (N)':<15} | {'Nested Loop (ms)':<20} | {'Sliding Window (ms)':<20}")
    print("-" * 65)
    
    sizes = [10000, 50000, 100000]
    k_group = 50 
    for n in sizes:
        data = sorted([random.randint(1, n*2) for _ in range(n)])
        
        t_nested = BenchmarkLab.measure(BenchmarkLab.nested_loop_find, data, k_group)
        t_sliding = BenchmarkLab.measure(BenchmarkLab.sliding_window_find, data, k_group)
        
        print(f"{n:<15} | {t_nested:<20.4f} | {t_sliding:<20.4f}")

if __name__ == "__main__":
    run_tests()