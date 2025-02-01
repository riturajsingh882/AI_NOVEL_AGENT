import os
import json

print("=== System Check ===")
print(f"Current Directory: {os.getcwd()}")
print(f"Files Here: {os.listdir()}")

print("\n=== Progress Check ===")
with open('book_progress.json') as f:
    progress = json.load(f)
    print(f"Progress Data: {progress}")

print("\n=== Chapter Files ===")
print(f"Chapters Found: {len(os.listdir('chapters'))}")