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

    # Add logging after context creation success through to CheckGLExtensions
    old4 = '''	// At this point, we have a window that we can show finally.
	SDL_ShowWindow(window);'''

    new4 = '''	// At this point, we have a window that we can show finally.
	fprintf(stderr, "DEBUG: SDL_ShowWindow...\\n"); fflush(stderr);
	SDL_ShowWindow(window);
	fprintf(stderr, "DEBUG: SDL_ShowWindow done\\n"); fflush(stderr);'''

    if old4 not in content:
        print(f"WARNING: SDL_ShowWindow block not found in {filepath}")
        sys.exit(1)
    content = content.replace(old4, new4)

    old5 = '''	// Finally we can do the regular initialization.
	CheckGLExtensions();
	draw_ = Draw::T3DCreateGLContext(true);'''

    new5 = '''	// Finally we can do the regular initialization.
	fprintf(stderr, "DEBUG: CheckGLExtensions...\\n"); fflush(stderr);
	CheckGLExtensions();
	fprintf(stderr, "DEBUG: CheckGLExtensions done, T3DCreateGLContext...\\n"); fflush(stderr);
	draw_ = Draw::T3DCreateGLContext(true);
	fprintf(stderr, "DEBUG: T3DCreateGLContext done\\n"); fflush(stderr);'''

    if old5 not in content:
        print(f"WARNING: CheckGLExtensions block not found in {filepath}")
        sys.exit(1)
    content = content.replace(old5, new5)

    # Add logging inside CheckGLExtensions at the first GL calls
    filepath2 = 'Common/GPU/OpenGL/GLFeatures.cpp'
    with open(filepath2, 'r') as f:
        content2 = f.read()

    old6 = '''	const char *renderer = (const char *)glGetString(GL_RENDERER);
	const char *versionStr = (const char *)glGetString(GL_VERSION);
	const char *glslVersionStr = (const char *)glGetString(GL_SHADING_LANGUAGE_VERSION);'''

    new6 = '''	fprintf(stderr, "DEBUG: glGetString(GL_RENDERER)...\\n"); fflush(stderr);
	const char *renderer = (const char *)glGetString(GL_RENDERER);
	fprintf(stderr, "DEBUG: renderer=%s\\n", renderer ? renderer : "NULL"); fflush(stderr);
	const char *versionStr = (const char *)glGetString(GL_VERSION);
	fprintf(stderr, "DEBUG: version=%s\\n", versionStr ? versionStr : "NULL"); fflush(stderr);
	const char *glslVersionStr = (const char *)glGetString(GL_SHADING_LANGUAGE_VERSION);
	fprintf(stderr, "DEBUG: glsl=%s\\n", glslVersionStr ? glslVersionStr : "NULL"); fflush(stderr);'''

    if old6 not in content2:
        print(f"WARNING: glGetString block not found in {filepath2}")
        sys.exit(1)
    content2 = content2.replace(old6, new6)

    old7 = '''	glGetIntegerv(GL_MAX_TEXTURE_SIZE, &gl_extensions.maxTextureSize);'''
    new7 = '''	fprintf(stderr, "DEBUG: glGetIntegerv(GL_MAX_TEXTURE_SIZE)...\\n"); fflush(stderr);
	glGetIntegerv(GL_MAX_TEXTURE_SIZE, &gl_extensions.maxTextureSize);
	fprintf(stderr, "DEBUG: maxTextureSize=%d\\n", gl_extensions.maxTextureSize); fflush(stderr);'''

    if old7 not in content2:
        print(f"WARNING: glGetIntegerv block not found in {filepath2}")
        sys.exit(1)
    content2 = content2.replace(old7, new7)

    old8 = '''	// Start by assuming we're at 2.0.
	int parsed[2] = {2, 0};'''
    new8 = '''	fprintf(stderr, "DEBUG: parsing version string...\\n"); fflush(stderr);
	// Start by assuming we're at 2.0.
	int parsed[2] = {2, 0};'''

    if old8 not in content2:
        print(f"WARNING: version parse block not found in {filepath2}")
        sys.exit(1)
    content2 = content2.replace(old8, new8)

    old9 = '''#ifdef GL_MAJOR_VERSION
		// Before grabbing the values, reset the error.
		glGetError();
		glGetIntegerv(GL_MAJOR_VERSION, &gl_extensions.ver[0]);'''
    new9 = '''#ifdef GL_MAJOR_VERSION
		fprintf(stderr, "DEBUG: GL_MAJOR_VERSION query...\\n"); fflush(stderr);
		// Before grabbing the values, reset the error.
		glGetError();
		glGetIntegerv(GL_MAJOR_VERSION, &gl_extensions.ver[0]);'''

    if old9 not in content2:
        print(f"WARNING: GL_MAJOR_VERSION block not found in {filepath2}")
        sys.exit(1)
    content2 = content2.replace(old9, new9)

    old10 = '''			gl_extensions.GLES3 = gl3stubInit();'''
    new10 = '''			fprintf(stderr, "DEBUG: gl3stubInit...\\n"); fflush(stderr);
				gl_extensions.GLES3 = gl3stubInit();
				fprintf(stderr, "DEBUG: gl3stubInit done, GLES3=%d\\n", (int)gl_extensions.GLES3); fflush(stderr);'''

    # Only replace the first occurrence (inside the else branch at line ~306)
    if old10 not in content2:
        print(f"WARNING: gl3stubInit block not found in {filepath2}")
        sys.exit(1)
    content2 = content2.replace(old10, new10, 1)

    if old7 not in content2:
        print(f"WARNING: glGetIntegerv block not found in {filepath2}")
        sys.exit(1)
    content2 = content2.replace(old7, new7)

    with open(filepath2, 'w') as f:
        f.write(content2)

    print(f"Patched: Added debug logging inside CheckGLExtensions")

    with open(filepath, 'w') as f:
        f.write(content)

    print(f"Patched: Added debug logging around SDL GL init")

if __name__ == '__main__':
    patch('SDL/SDLGLGraphicsContext.cpp')
