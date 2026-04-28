import os

target_dir = r"c:\Users\omaks\Downloads\logistiq-master\logistiq-master\logistiq"

for root, dirs, files in os.walk(target_dir):
    for f in files:
        if f.endswith('.py') or f.endswith('.md'):
            filepath = os.path.join(root, f)
            try:
                # Try reading as UTF-8
                with open(filepath, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                if "ðŸš¢" in content:
                    print(f"FOUND literal 'ðŸš¢' in {filepath} (UTF-8)")
                if "🚢" in content:
                    print(f"FOUND actual '🚢' in {filepath} (UTF-8)")
                    
            except UnicodeDecodeError:
                print(f"UnicodeDecodeError reading {filepath} as UTF-8")
                
            try:
                # Try reading as cp1252 or Windows-1252
                with open(filepath, 'r', encoding='cp1252') as file:
                    content2 = file.read()
                if "ðŸš¢" in content2:
                    print(f"FOUND literal 'ðŸš¢' in {filepath} (CP1252)")
            except Exception as e:
                pass
