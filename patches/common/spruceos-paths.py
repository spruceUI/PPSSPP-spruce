#!/usr/bin/env python3
"""Hardcode SpruceOS memstick path for PPSSPP.

Replaces the XDG_CONFIG_HOME / HOME-based path discovery with a
hardcoded path so PPSSPP finds config, saves, and state files
without relying on the HOME environment variable hack.

To change the memstick path, edit MEMSTICK_PATH below.
"""
import re
import sys

# ── Edit this path to change where PPSSPP stores config/saves ──
MEMSTICK_PATH = "/mnt/SDCARD/Saves/.config/ppsspp"
# ───────────────────────────────────────────────────────────────

def patch(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Replace the XDG/HOME config discovery block with a hardcoded path
    pattern = (
        r'(\#elif !PPSSPP_PLATFORM\(WINDOWS\)\n)'
        r'\tstd::string config;\n'
        r'\tif \(getenv\("XDG_CONFIG_HOME"\).*?\n'
        r'.*?config = "\./config";\n\n'
        r'\tg_Config\.memStickDirectory = Path\(config\) / "ppsspp";'
    )
    replacement = (
        r'\1'
        f'\tg_Config.memStickDirectory = Path("{MEMSTICK_PATH}");'
    )
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    if new_content == content:
        print(f"WARNING: memStickDirectory pattern not found in {filepath}")
        sys.exit(1)

    with open(filepath, 'w') as f:
        f.write(new_content)

    print(f"Patched memStickDirectory to: {MEMSTICK_PATH}")

if __name__ == '__main__':
    patch('UI/NativeApp.cpp')
