import os

target_dir = r"c:\Users\omaks\Downloads\logistiq-master\logistiq-master\logistiq"

changes = {
    "use_container_width=True": "width='stretch'",
    "use_container_width=False": "width='content'"
}

changed_files = []

for root, dirs, files in os.walk(target_dir):
    for f in files:
        if f.endswith('.py'):
            filepath = os.path.join(root, f)
            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                original = content
                for k, v in changes.items():
                    content = content.replace(k, v)
                
                if content != original:
                    with open(filepath, 'w', encoding='utf-8') as file:
                        file.write(content)
                    changed_files.append(filepath)
            except Exception:
                pass

print("FIXED_FILES:")
for f in changed_files:
    print(f)
