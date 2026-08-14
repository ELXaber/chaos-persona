from axiom_manager import create_axiom_manager
import os

print("Testing KB write...")
am = create_axiom_manager()

result = am.add_axiom("test_windows", "KB write test successful on Windows at " + str(os.path.exists("knowledge_base/discoveries.jsonl")))
print("Add result:", result)

axiom = am.get_current_axiom("test_windows")
print("Read back:", axiom)

# Check if file actually exists and has content
kb_path = "knowledge_base/discoveries.jsonl"
if os.path.exists(kb_path):
    print(f"File exists, size: {os.path.getsize(kb_path)} bytes")
    with open(kb_path, "r", encoding="utf-8") as f:
        print("First line preview:", f.readline()[:200])
else:
    print("File NOT found at", kb_path)