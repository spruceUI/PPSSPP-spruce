#!/usr/bin/env python3
"""Fix crash when glCopyImageSubDataOES is NULL on PowerVR GE8300.

PowerVR GE8300 either falsely reports GL_OES_copy_image support or
fails to provide the function pointer, causing a null function pointer
call in GLQueueRunner::PerformCopy when games trigger framebuffer
copies (e.g., Gran Turismo at race start, GoW at boot).

Fix: guard the framebufferCopySupported capability flag with a null
check on the actual function pointer, so PPSSPP falls back to its
non-copy path when the function isn't actually available.
"""
import sys

TARGET = 'Common/GPU/OpenGL/thin3d_gl.cpp'

OLD = '''caps_.framebufferCopySupported = gl_extensions.OES_copy_image || gl_extensions.NV_copy_image || gl_extensions.EXT_copy_image || gl_extensions.ARB_copy_image;'''

NEW = '''caps_.framebufferCopySupported = (gl_extensions.OES_copy_image || gl_extensions.NV_copy_image || gl_extensions.EXT_copy_image || gl_extensions.ARB_copy_image) && glCopyImageSubDataOES != nullptr;'''

def patch(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    if OLD not in content:
        # Try multiline variant
        old_ml = 'caps_.framebufferCopySupported = gl_extensions.OES_copy_image || gl_extensions.NV_copy_image || gl_extensions.EXT_copy_image || gl_extensions.ARB_copy_image;'
        if old_ml not in content:
            print(f"WARNING: Could not find framebufferCopySupported assignment in {filepath}")
            print("Trying flexible match...")
            # Try to find it with any whitespace
            import re
            pattern = r'caps_\.framebufferCopySupported\s*=\s*gl_extensions\.OES_copy_image\s*\|\|\s*gl_extensions\.NV_copy_image\s*\|\|\s*gl_extensions\.EXT_copy_image\s*\|\|\s*gl_extensions\.ARB_copy_image\s*;'
            match = re.search(pattern, content)
            if match:
                old_text = match.group(0)
                new_text = old_text.replace(
                    'gl_extensions.ARB_copy_image;',
                    'gl_extensions.ARB_copy_image) && glCopyImageSubDataOES != nullptr;'
                ).replace(
                    'caps_.framebufferCopySupported = gl_extensions.OES_copy_image',
                    'caps_.framebufferCopySupported = (gl_extensions.OES_copy_image'
                )
                content = content.replace(old_text, new_text)
            else:
                print(f"ERROR: Could not find framebufferCopySupported in {filepath}")
                sys.exit(1)
        else:
            content = content.replace(old_ml, NEW, 1)
    else:
        content = content.replace(OLD, NEW, 1)

    with open(filepath, 'w') as f:
        f.write(content)

    print(f"Patched: framebufferCopySupported now checks glCopyImageSubDataOES != nullptr")

if __name__ == '__main__':
    patch(TARGET)
