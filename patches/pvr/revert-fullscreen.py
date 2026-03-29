#!/usr/bin/env python3
"""Revert SDL_WINDOW_FULLSCREEN back to SDL_WINDOW_FULLSCREEN_DESKTOP for PVR.

The common fullscreen patch replaces FULLSCREEN_DESKTOP with FULLSCREEN
for DRM/KMS devices. But the PVR build uses SDL2's mali-fbdev driver
where FULLSCREEN_DESKTOP is required — it uses the current display mode
without trying to change it, which is the only mode mali-fbdev supports.
"""
import sys

def patch(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # The common patch already ran, so we're reverting FULLSCREEN back to FULLSCREEN_DESKTOP
    # But we need to be careful not to create SDL_WINDOW_FULLSCREEN_DESKTOP_DESKTOP
    # The common patch replaced all SDL_WINDOW_FULLSCREEN_DESKTOP with SDL_WINDOW_FULLSCREEN
    # So now we need to restore them. We replace SDL_WINDOW_FULLSCREEN with SDL_WINDOW_FULLSCREEN_DESKTOP
    # but only standalone instances (not already part of FULLSCREEN_DESKTOP)

    # Since the common patch already converted all _DESKTOP to non-_DESKTOP,
    # every instance of SDL_WINDOW_FULLSCREEN is now a candidate for restoration
    count = content.count('SDL_WINDOW_FULLSCREEN')
    content = content.replace('SDL_WINDOW_FULLSCREEN', 'SDL_WINDOW_FULLSCREEN_DESKTOP')

    with open(filepath, 'w') as f:
        f.write(content)

    print(f"Reverted {count} occurrences of SDL_WINDOW_FULLSCREEN -> SDL_WINDOW_FULLSCREEN_DESKTOP in {filepath}")

if __name__ == '__main__':
    patch('SDL/SDLMain.cpp')
