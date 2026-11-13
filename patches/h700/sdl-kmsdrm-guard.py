#!/usr/bin/env python3
"""Compile the KMSDRM Vulkan surface case only where SDL declares it.

The h700 build links SDL2 2.0.10 headers, which predate SDL_SYSWM_KMSDRM.
The case does what the VK_KHR_display default from
vulkan-display-fallback.py already does, so without it nothing changes.
"""
import sys

TARGET = 'SDL/SDLVulkanGraphicsContext.cpp'

OLD = '''#if defined(VK_USE_PLATFORM_DISPLAY_KHR)
\tcase SDL_SYSWM_KMSDRM:'''

NEW = '''#if defined(VK_USE_PLATFORM_DISPLAY_KHR) && SDL_VERSION_ATLEAST(2, 0, 16)
\tcase SDL_SYSWM_KMSDRM:'''


def patch(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    if OLD not in content:
        print(f"WARNING: Could not find the KMSDRM Vulkan case in {filepath}")
        sys.exit(1)

    content = content.replace(OLD, NEW, 1)

    with open(filepath, 'w') as f:
        f.write(content)

    print("Patched: KMSDRM Vulkan case needs SDL 2.0.16")


if __name__ == '__main__':
    patch(TARGET)
