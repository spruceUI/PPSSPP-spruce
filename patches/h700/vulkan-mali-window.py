#!/usr/bin/env python3
"""Run Vulkan through VK_KHR_display under SDL's mali video driver.

The mali driver knows nothing of Vulkan: it refuses SDL_WINDOW_VULKAN and
has no SDL_GetWindowWMInfo, and PPSSPP exits on either. Create a plain
window for input instead, and treat missing WM info as an unknown
subsystem, which vulkan-display-fallback.py sends to VK_KHR_display.
"""
import sys

TARGET = 'SDL/SDLVulkanGraphicsContext.cpp'

EDITS = [
    ('''\twindow = SDL_CreateWindow("Initializing Vulkan...", x, y, w, h, mode);
\tif (!window) {''',
     '''\twindow = SDL_CreateWindow("Initializing Vulkan...", x, y, w, h, mode);
#if defined(VK_USE_PLATFORM_DISPLAY_KHR)
\tif (!window && (mode & SDL_WINDOW_VULKAN))
\t\twindow = SDL_CreateWindow("Initializing Vulkan...", x, y, w, h, mode & ~SDL_WINDOW_VULKAN);
#endif
\tif (!window) {'''),
    ('''\tif (!SDL_GetWindowWMInfo(window, &sys_info)) {
\t\tfprintf(stderr, "Error getting SDL window wm info: %s\\n", SDL_GetError());
\t\texit(1);
\t}''',
     '''\tif (!SDL_GetWindowWMInfo(window, &sys_info)) {
#if defined(VK_USE_PLATFORM_DISPLAY_KHR)
\t\tsys_info.subsystem = SDL_SYSWM_UNKNOWN;
#else
\t\tfprintf(stderr, "Error getting SDL window wm info: %s\\n", SDL_GetError());
\t\texit(1);
#endif
\t}'''),
]


def patch(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    for old, new in EDITS:
        if old not in content:
            print(f"WARNING: Could not find expected code in {filepath}")
            sys.exit(1)
        content = content.replace(old, new, 1)

    with open(filepath, 'w') as f:
        f.write(content)

    print("Patched: Vulkan window and WM info fall back for SDL's mali driver")


if __name__ == '__main__':
    patch(TARGET)
