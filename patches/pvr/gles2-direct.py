#!/usr/bin/env python3
"""Skip GL version probing loop — request GLES 2.0 directly.

On PowerVR devices with SDL2's mali-fbdev driver, the GL version
loop (trying 3.2, 3.1, 3.0, 2.0 in sequence) creates and destroys
SDL windows for each failed attempt. The mali-fbdev driver doesn't
clean up EGL state properly between attempts, poisoning subsequent
context creation.

RetroArch works on the same device because it requests a single
specific GL version. This patch does the same — requests GLES 2.0
directly without the probing loop.
"""
import re
import sys

def patch(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Find the version attempt loop and replace with direct GLES 2.0 request
    # The loop starts with GLVersionPair attemptVersions[] and ends with
    # the fallback SDL_CreateWindow after the loop

    old = '''	GLVersionPair attemptVersions[] = {
#ifdef USING_GLES2
		{3, 2}, {3, 1}, {3, 0}, {2, 0},
#else
		{4, 6}, {4, 5}, {4, 4}, {4, 3}, {4, 2}, {4, 1}, {4, 0},
		{3, 3}, {3, 2}, {3, 1}, {3, 0},
#endif
	};'''

    new = '''	GLVersionPair attemptVersions[] = {
#ifdef USING_GLES2
		{2, 0},
#else
		{4, 6}, {4, 5}, {4, 4}, {4, 3}, {4, 2}, {4, 1}, {4, 0},
		{3, 3}, {3, 2}, {3, 1}, {3, 0},
#endif
	};'''

    if old not in content:
        print(f"WARNING: GL version loop not found in {filepath}")
        sys.exit(1)

    content = content.replace(old, new)

    with open(filepath, 'w') as f:
        f.write(content)

    print(f"Patched: GLES2 path requests only 2.0 (no version probing loop)")

if __name__ == '__main__':
    patch('SDL/SDLGLGraphicsContext.cpp')
