import time
import sys

print("Starting Mock Process...", flush=True)
for i in range(5):
    time.sleep(1)
    print(f"Progress: {i+1}/5", flush=True)
print("Mock Process Completed.", flush=True)
