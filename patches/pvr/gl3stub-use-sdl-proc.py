#!/usr/bin/env python3
"""Use SDL_GL_GetProcAddress instead of eglGetProcAddress in gl3stub.

On PowerVR with EGL=OFF, eglGetProcAddress may return NULL for GLES3
functions because PPSSPP doesn't initialize EGL directly (SDL handles
it internally). SDL_GL_GetProcAddress works because SDL has an active
GL context.

This ensures gl3stubInit succeeds and PPSSPP uses GLES3 rendering
paths, matching the old working binary's behavior.
"""
import sys

def patch(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    old = '''#include "EGL/egl.h"

GLboolean gl3stubInit() {
    #define FIND_PROC(s) s = (void*)eglGetProcAddress(#s)'''

    new = '''#include "EGL/egl.h"
#include "SDL2/SDL.h"

GLboolean gl3stubInit() {
    #define FIND_PROC(s) s = (void*)SDL_GL_GetProcAddress(#s)'''

    if old not in content:
        print(f"WARNING: gl3stub FIND_PROC block not found in {filepath}")
        sys.exit(1)

    content = content.replace(old, new)

    with open(filepath, 'w') as f:
        f.write(content)

    print(f"Patched: gl3stubInit uses SDL_GL_GetProcAddress instead of eglGetProcAddress")

if __name__ == '__main__':
    patch('Common/GPU/OpenGL/gl3stub.c')
