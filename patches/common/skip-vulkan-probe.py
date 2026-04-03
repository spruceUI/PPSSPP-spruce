#!/usr/bin/env python3
"""Skip the Vulkan runtime probe — return false immediately.

Even with VULKAN=OFF, PPSSPP probes for Vulkan at startup by dlopen'ing
libvulkan.so, creating a test VkInstance, and enumerating GPUs (~65ms).
This is wasted work on devices without Vulkan support.

This patch makes VulkanMayBeAvailable() return false immediately.
Only applied to non-Vulkan builds (TSPS skips this patch).
"""
import sys

TARGET = 'Common/GPU/Vulkan/VulkanLoader.cpp'

OLD = '''bool VulkanMayBeAvailable() {'''
NEW = '''bool VulkanMayBeAvailable() {
\treturn false;  // Patched: skip probe on non-Vulkan builds'''

def patch(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    if OLD not in content:
        print(f"WARNING: Could not find VulkanMayBeAvailable in {filepath}")
        sys.exit(1)

    content = content.replace(OLD, NEW, 1)

    with open(filepath, 'w') as f:
        f.write(content)

    print(f"Patched VulkanMayBeAvailable to return false in {filepath}")

if __name__ == '__main__':
    patch(TARGET)
