#!/usr/bin/env python3
"""Unconditionally hide the mouse cursor.

On handheld devices there's no mouse, so the cursor should never appear.
"""
import re
import sys

def patch(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    original = content
    patched = False

    # Patch UpdateSDLCursor: replace entire function body with unconditional disable
    pattern = r'(void UpdateSDLCursor\(\) \{)\n.*?(\n\})'
    replacement = r'\1\n\tSDL_ShowCursor(SDL_DISABLE);\2'
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    if new_content != content:
        content = new_content
        patched = True
        print("Patched UpdateSDLCursor to unconditionally disable cursor")

    # Remove #ifdef MOBILE_DEVICE guard around SDL_ShowCursor(SDL_DISABLE)
    pattern = r'#ifdef MOBILE_DEVICE\s*\n\s*SDL_ShowCursor\(SDL_DISABLE\);\s*\n#endif'
    replacement = 'SDL_ShowCursor(SDL_DISABLE);'
    new_content = re.sub(pattern, replacement, content)
    if new_content != content:
        content = new_content
        patched = True
        print("Patched MOBILE_DEVICE guard to unconditionally disable cursor")

    if not patched:
        print(f"WARNING: No cursor patterns found to patch in {filepath}")
        sys.exit(1)

    with open(filepath, 'w') as f:
        f.write(content)

if __name__ == '__main__':
    patch('SDL/SDLMain.cpp')
