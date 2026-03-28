#!/usr/bin/env python3
"""Compact pause menu layout for 640x480 screens.

At 640x480, the save state panel gets only ~257dp of width, which is too
narrow for the 164dp thumbnail + slot number + buttons. This patch:
1. Halves the save state thumbnail from 164x94 to 80x46
2. Narrows the right button column from 320dp to 260dp

Together this gives the save state panel ~327dp — enough room.
"""
import sys


def patch(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    changes = 0

    # Reduce save state thumbnail size
    old = 'new UI::LayoutParams(82 * 2, 47 * 2)'
    new = 'new UI::LayoutParams(80, 46)'
    count = content.count(old)
    if count == 0:
        print(f"ERROR: Could not find thumbnail LayoutParams in {filepath}")
        sys.exit(1)
    content = content.replace(old, new)
    changes += count

    # Narrow the right button column (landscape mode only)
    old = 'new LinearLayoutParams(320, FILL_PARENT, actionMenuMargins)'
    new = 'new LinearLayoutParams(260, FILL_PARENT, actionMenuMargins)'
    if old not in content:
        print(f"ERROR: Could not find button column width in {filepath}")
        sys.exit(1)
    content = content.replace(old, new, 1)
    changes += 1

    with open(filepath, 'w') as f:
        f.write(content)

    print(f"Patched pause menu layout ({changes} changes)")


if __name__ == '__main__':
    patch('UI/PauseScreen.cpp')
