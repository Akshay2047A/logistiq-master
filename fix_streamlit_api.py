"""Fix deprecated width='stretch' / width='content' in all Streamlit view files."""
import os
import re

target_dir = r"c:\Users\omaks\Downloads\logistiq-master\logistiq-master\logistiq"

changed = []

for root, dirs, files in os.walk(target_dir):
    for fname in files:
        if not fname.endswith(".py"):
            continue
        fpath = os.path.join(root, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                src = f.read()
            original = src

            # width='stretch' → use_container_width=True
            src = src.replace("width='stretch'", "use_container_width=True")
            src = src.replace('width="stretch"', "use_container_width=True")
            # width='content' → (remove param entirely)
            src = re.sub(r",\s*width='content'", "", src)
            src = re.sub(r",\s*width=\"content\"", "", src)
            # use_container_width= on plotly_chart — some may have been reverted
            # make sure st_folium keeps use_container_width
            # (no action needed; it was already fixed)

            if src != original:
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(src)
                changed.append(fpath)
        except Exception as e:
            print(f"  ERROR {fpath}: {e}")

print(f"\nFixed {len(changed)} file(s):")
for p in changed:
    print(" ", p)
