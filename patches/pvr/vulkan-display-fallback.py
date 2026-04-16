#!/usr/bin/env python3
"""Fall back to VK_KHR_display for unknown SDL subsystems.

On the SmartPro/Brick (PowerVR GE8300), SDL reports subsystem 0
(SDL_SYSWM_UNKNOWN) instead of SDL_SYSWM_KMSDRM. PPSSPP's Vulkan
surface init switch/case doesn't handle this and calls exit(1).

Fix: when VK_USE_PLATFORM_DISPLAY_KHR is defined, treat the default
case the same as KMSDRM — call InitSurface(WINDOWSYSTEM_DISPLAY).
"""
import sys

TARGET = 'SDL/SDLVulkanGraphicsContext.cpp'

OLD = '''\tdefault:
\t\tfprintf(stderr, "Vulkan subsystem %d not supported\\n", sys_info.subsystem);
\t\texit(1);
\t\tbreak;
\t}'''

NEW = '''#if defined(VK_USE_PLATFORM_DISPLAY_KHR)
\tdefault:
\t\tvulkan_->InitSurface(WINDOWSYSTEM_DISPLAY, nullptr, nullptr);
\t\tbreak;
#else
\tdefault:
\t\tfprintf(stderr, "Vulkan subsystem %d not supported\\n", sys_info.subsystem);
\t\texit(1);
\t\tbreak;
#endif
\t}'''

def patch(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    if OLD not in content:
        print(f"WARNING: Could not find Vulkan subsystem default case in {filepath}")
        sys.exit(1)

    content = content.replace(OLD, NEW, 1)

    with open(filepath, 'w') as f:
        f.write(content)

    print(f"Patched: Vulkan default subsystem falls back to WINDOWSYSTEM_DISPLAY")

if __name__ == '__main__':
    patch(TARGET)
