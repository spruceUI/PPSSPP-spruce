#!/usr/bin/env python3
"""Fix crash when glGetStringi is unavailable on GLES 3.2 PowerVR.

On PowerVR GE8300, gl3stubInit() fails to load GLES 3.0 function
pointers (returns false), but GL_MAJOR_VERSION reports 3.2. The
extension enumeration code checks ver[0] >= 3 and calls glGetStringi
which is a NULL function pointer — segfault.

Fix: also check that glGetStringi is non-NULL before using the GL3+
extension enumeration path.
"""
import sys

def patch(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    old = '''	if (gl_extensions.ver[0] >= 3) {
		// Let's use the new way for OpenGL 3.x+, required in the core profile.
		GLint numExtensions = 0;
		glGetIntegerv(GL_NUM_EXTENSIONS, &numExtensions);'''

    new = '''	if (gl_extensions.ver[0] >= 3 && glGetStringi) {
		// Let's use the new way for OpenGL 3.x+, required in the core profile.
		GLint numExtensions = 0;
		glGetIntegerv(GL_NUM_EXTENSIONS, &numExtensions);'''

    if old not in content:
        print(f"WARNING: glGetStringi block not found in {filepath}")
        sys.exit(1)

    content = content.replace(old, new)

    with open(filepath, 'w') as f:
        f.write(content)

    print(f"Patched: guard glGetStringi call with NULL check")

if __name__ == '__main__':
    patch('Common/GPU/OpenGL/GLFeatures.cpp')
