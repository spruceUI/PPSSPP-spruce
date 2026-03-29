#!/usr/bin/env python3
"""Add debug logging around SDL GL init to find exact crash point."""
import sys

def patch(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Add debug prints around key SDL calls in SDLGLGraphicsContext::Init
    old = '''	SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, ver.major);
		SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, ver.minor);'''

    new = '''	fprintf(stderr, "DEBUG: Trying GL %d.%d\\n", ver.major, ver.minor);
		fflush(stderr);
		SDL_GL_SetAttribute(SDL_GL_CONTEXT_MAJOR_VERSION, ver.major);
		SDL_GL_SetAttribute(SDL_GL_CONTEXT_MINOR_VERSION, ver.minor);'''

    if old not in content:
        print(f"WARNING: GL version set block not found in {filepath}")
        sys.exit(1)
    content = content.replace(old, new)

    old2 = '''		window = SDL_CreateWindow("PPSSPP", x, y, w, h, mode);
		if (!window) {'''

    new2 = '''		fprintf(stderr, "DEBUG: SDL_CreateWindow(x=%d, y=%d, w=%d, h=%d, mode=0x%x)\\n", x, y, w, h, mode);
		fflush(stderr);
		window = SDL_CreateWindow("PPSSPP", x, y, w, h, mode);
		fprintf(stderr, "DEBUG: SDL_CreateWindow returned %p\\n", (void*)window);
		fflush(stderr);
		if (!window) {'''

    if old2 not in content:
        print(f"WARNING: SDL_CreateWindow block not found in {filepath}")
        sys.exit(1)
    content = content.replace(old2, new2)

    old3 = '''		glContext = SDL_GL_CreateContext(window);
		if (glContext != nullptr) {'''

    new3 = '''		fprintf(stderr, "DEBUG: SDL_GL_CreateContext...\\n");
		fflush(stderr);
		glContext = SDL_GL_CreateContext(window);
		fprintf(stderr, "DEBUG: SDL_GL_CreateContext returned %p\\n", (void*)glContext);
		fflush(stderr);
		if (glContext != nullptr) {'''

    if old3 not in content:
        print(f"WARNING: SDL_GL_CreateContext block not found in {filepath}")
        sys.exit(1)
    content = content.replace(old3, new3, 1)

    with open(filepath, 'w') as f:
        f.write(content)

    print(f"Patched: Added debug logging around SDL GL init")

if __name__ == '__main__':
    patch('SDL/SDLGLGraphicsContext.cpp')
