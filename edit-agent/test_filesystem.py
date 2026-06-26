"""Temporary test — delete after Day 5."""

from tools.filesystem import read_file, list_dir, write_file

# Test 1 — list the project root
print("=== list_dir ===")
print(list_dir("."))
print()

# Test 2 — read a real file
print("=== read_file ===")
print(read_file("client.py"))
print()

# Test 3 — write a new file then read it back
print("=== write_file ===")
write_file("workspace/hello.txt", "Hello from the agent!\n")
print(read_file("workspace/hello.txt"))
print()

# Test 4 — try to escape the project root (should raise PermissionError)
print("=== path traversal block ===")
try:
    read_file("../../etc/passwd")
except PermissionError as e:
    print(f"Blocked correctly: {e}")



from tools.diff import generate_diff, has_changes

original = """def greet(name):
    print("hello " + name)
"""

proposed = """def greet(name):
    print(f"Hello, {name}!")
"""

print("=== generate_diff ===")
print(generate_diff(original, proposed, "greet.py"))

print("=== has_changes ===")
print(has_changes(original, proposed))  # should print True
print(has_changes(original, original))  # should print False
