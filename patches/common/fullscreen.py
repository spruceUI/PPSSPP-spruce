#!/usr/bin/env python3
"""Replace SDL_WINDOW_FULLSCREEN_DESKTOP with SDL_WINDOW_FULLSCREEN.

Critical for DRM/KMS on embedded ARM devices — SDL_WINDOW_FULLSCREEN_DESKTOP
doesn't work correctly without a desktop compositor.
"""
import sys

def patch(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    count = content.count('SDL_WINDOW_FULLSCREEN_DESKTOP')
    if count == 0:
        print(f"WARNING: No SDL_WINDOW_FULLSCREEN_DESKTOP found in {filepath}")
        sys.exit(1)

    content = content.replace('SDL_WINDOW_FULLSCREEN_DESKTOP', 'SDL_WINDOW_FULLSCREEN')

    with open(filepath, 'w') as f:
        f.write(content)

    print(f"Patched {count} occurrences of SDL_WINDOW_FULLSCREEN_DESKTOP -> SDL_WINDOW_FULLSCREEN in {filepath}")

if __name__ == '__main__':
    patch('SDL/SDLMain.cpp')
