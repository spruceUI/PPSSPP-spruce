#!/usr/bin/env python3
"""Force no alpha channel in EGL framebuffer config for PowerVR.

PowerVR's display engine uses per-pixel alpha when the EGL surface
has an alpha channel (RGBA8888), making the output transparent.
Setting SDL_GL_ALPHA_SIZE to 0 selects RGBX8888 instead, which
uses global alpha (fully opaque).
"""
import sys

def patch(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    old = '''	SDL_GL_SetAttribute(SDL_GL_STENCIL_SIZE, 8);
	SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER, 1);'''

    new = '''	SDL_GL_SetAttribute(SDL_GL_STENCIL_SIZE, 8);
	SDL_GL_SetAttribute(SDL_GL_DOUBLEBUFFER, 1);
	SDL_GL_SetAttribute(SDL_GL_ALPHA_SIZE, 0);'''

    if old not in content:
        print(f"WARNING: GL attribute block not found in {filepath}")
        sys.exit(1)

    content = content.replace(old, new)

    with open(filepath, 'w') as f:
        f.write(content)

    print(f"Patched: SDL_GL_ALPHA_SIZE = 0 (force RGBX8888, no per-pixel alpha)")

if __name__ == '__main__':
    patch('SDL/SDLMain.cpp')
