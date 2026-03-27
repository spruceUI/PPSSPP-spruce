#!/usr/bin/env python3
"""Remove auto-mute for secondary PPSSPP instances.

PPSSPP auto-silences audio when PPSSPP_ID > 1, which can trigger
incorrectly on handheld devices and mute audio entirely.
"""
import re
import sys

def patch(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Remove the entire block that silences secondary instances
    pattern = r'\n\t// Automatically silence secondary instances.*?\n\tif \(PPSSPP_ID > 1\) \{.*?\n\t\}'
    new_content = re.sub(pattern, '', content, flags=re.DOTALL)

    if new_content == content:
        print(f"WARNING: Secondary instance mute block not found in {filepath}")
        sys.exit(1)

    with open(filepath, 'w') as f:
        f.write(new_content)

    print(f"Removed secondary instance auto-mute from {filepath}")

if __name__ == '__main__':
    patch('Core/Config.cpp')
