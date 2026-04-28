import os

mappings = {
    "ðŸš¢": "🚢",
    "ðŸš›": "🚛",
    "ðŸš‚": "🚂",
    "ðŸŒ€": "🌀",
    "â‚¹": "₹",
    "â€\"": "–",
    "â†'": "→",
    "âœ…": "✅",
    "âš ": "⚠",
    "ðŸ¤–": "🤖",
    "ðŸ\"¡": "📡",
    "ðŸ'°": "💰",
    "ðŸŒ±": "🌱",
    "ðŸ—º": "🗺",
    "ðŸ\"¦": "📦",
    "âŒ ": "❌"
}

changed_files = []
target_dir = r"c:\Users\omaks\Downloads\logistiq-master\logistiq-master\logistiq"

for root, dirs, files in os.walk(target_dir):
    for f in files:
        if f.endswith('.py') or f.endswith('.md') or f.endswith('.json'):
            filepath = os.path.join(root, f)
            try:
                with open(filepath, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                original = content
                for k, v in mappings.items():
                    content = content.replace(k, v)
                
                if content != original:
                    with open(filepath, 'w', encoding='utf-8') as file:
                        file.write(content)
                    changed_files.append(filepath)
            except Exception as e:
                pass

print("CHANGED_FILES:")
for f in changed_files:
    print(f)
