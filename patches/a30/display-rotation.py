#!/usr/bin/env python3
"""Add display rotation support for portrait-panel devices (e.g., Miyoo A30).

Reads the DISPLAY_ROTATION environment variable (0, 90, 180, 270) and
activates PPSSPP's existing DisplayRotation infrastructure for SDL/OpenGL.
PPSSPP already has rotation support (rot_matrix, ComputeOrthoMatrix,
CopyToOutput vertex rotation) but it's only wired up for Vulkan/UWP.
This patch wires it up for SDL.

Modifications to SDL/SDLMain.cpp:
1. After display mode detection: read DISPLAY_ROTATION, set g_display.rotation
   and rot_matrix, swap g_DesktopWidth/Height for 90/270 rotations
2. In window resize handler: swap dimensions when rotation is active
3. Mouse coordinates: transform from physical to logical space
4. Touch coordinates: transform from physical to logical space
"""
import sys


def patch(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    changes = 0

    # ── Mod 1: Add rotation detection after display mode detection ──
    # Insert after g_DesktopHeight = displayMode.h; / g_RefreshRate = ...;
    old = (
        'g_DesktopWidth = displayMode.w;\n'
        '\tg_DesktopHeight = displayMode.h;\n'
        '\tg_RefreshRate = displayMode.refresh_rate;'
    )
    new = (
        'g_DesktopWidth = displayMode.w;\n'
        '\tg_DesktopHeight = displayMode.h;\n'
        '\tg_RefreshRate = displayMode.refresh_rate;\n'
        '\n'
        '\t// Display rotation for portrait-panel devices (e.g., Miyoo A30)\n'
        '\t{\n'
        '\t\tconst char *rot_env = getenv("DISPLAY_ROTATION");\n'
        '\t\tint rot_deg = rot_env ? atoi(rot_env) : 0;\n'
        '\t\tg_display.rotation = DisplayRotation::ROTATE_0;\n'
        '\t\tg_display.rot_matrix.setIdentity();\n'
        '\t\tswitch (rot_deg) {\n'
        '\t\tcase 90:\n'
        '\t\t\tg_display.rotation = DisplayRotation::ROTATE_90;\n'
        '\t\t\tg_display.rot_matrix.setRotationZ90();\n'
        '\t\t\tstd::swap(g_DesktopWidth, g_DesktopHeight);\n'
        '\t\t\tbreak;\n'
        '\t\tcase 180:\n'
        '\t\t\tg_display.rotation = DisplayRotation::ROTATE_180;\n'
        '\t\t\tg_display.rot_matrix.setRotationZ180();\n'
        '\t\t\tbreak;\n'
        '\t\tcase 270:\n'
        '\t\t\tg_display.rotation = DisplayRotation::ROTATE_270;\n'
        '\t\t\tg_display.rot_matrix.setRotationZ270();\n'
        '\t\t\tstd::swap(g_DesktopWidth, g_DesktopHeight);\n'
        '\t\t\tbreak;\n'
        '\t\t}\n'
        '\t\tif (rot_deg != 0) {\n'
        '\t\t\tfprintf(stderr, "Display rotation: %d degrees\\n", rot_deg);\n'
        '\t\t}\n'
        '\t}'
    )
    if old not in content:
        print(f"ERROR: Could not find display mode detection block in {filepath}")
        sys.exit(1)
    content = content.replace(old, new, 1)
    changes += 1

    # ── Mod 2: Swap dimensions in window resize handler ──
    # After new_width_px/new_height_px are computed, swap if rotated
    old = (
        'int new_width_px = new_width * g_DesktopDPI;\n'
        '\t\t\tint new_height_px = new_height * g_DesktopDPI;'
    )
    new = (
        'int new_width_px = new_width * g_DesktopDPI;\n'
        '\t\t\tint new_height_px = new_height * g_DesktopDPI;\n'
        '\t\t\tif (g_display.rotation == DisplayRotation::ROTATE_90 || g_display.rotation == DisplayRotation::ROTATE_270) {\n'
        '\t\t\t\tstd::swap(new_width_px, new_height_px);\n'
        '\t\t\t}'
    )
    if old not in content:
        print(f"ERROR: Could not find resize handler dimension block in {filepath}")
        sys.exit(1)
    content = content.replace(old, new, 1)
    changes += 1

    # ── Mod 3: Transform mouse coordinates ──
    # After swap: g_DesktopWidth = logicalW = physH, g_DesktopHeight = logicalH = physW
    # ROTATE_90:  logical(x,y) = (phys_y, physW - phys_x)
    # ROTATE_270: logical(x,y) = (physH - phys_y, phys_x)
    # ROTATE_180: logical(x,y) = (physW - phys_x, physH - phys_y)
    old = (
        'float mx = event.motion.x * g_DesktopDPI * g_display.dpi_scale_x;\n'
        '\tfloat my = event.motion.y * g_DesktopDPI * g_display.dpi_scale_x;'
    )
    new = (
        'float mx = event.motion.x * g_DesktopDPI * g_display.dpi_scale_x;\n'
        '\tfloat my = event.motion.y * g_DesktopDPI * g_display.dpi_scale_x;\n'
        '\tif (g_display.rotation == DisplayRotation::ROTATE_90) {\n'
        '\t\tfloat tmp = mx;\n'
        '\t\tmx = my;\n'
        '\t\tmy = g_DesktopHeight * g_DesktopDPI * g_display.dpi_scale_x - tmp;\n'
        '\t} else if (g_display.rotation == DisplayRotation::ROTATE_270) {\n'
        '\t\tfloat tmp = mx;\n'
        '\t\tmx = g_DesktopWidth * g_DesktopDPI * g_display.dpi_scale_x - my;\n'
        '\t\tmy = tmp;\n'
        '\t} else if (g_display.rotation == DisplayRotation::ROTATE_180) {\n'
        '\t\tmx = g_DesktopWidth * g_DesktopDPI * g_display.dpi_scale_x - mx;\n'
        '\t\tmy = g_DesktopHeight * g_DesktopDPI * g_display.dpi_scale_x - my;\n'
        '\t}'
    )
    if old not in content:
        print(f"ERROR: Could not find mouse coordinate block in {filepath}")
        sys.exit(1)
    content = content.replace(old, new, 1)
    changes += 1

    # ── Mod 4: Transform touch coordinates ──
    # Touch events compute input.x/y from tfinger.x/y * window size.
    # SDL reports physical window dimensions, so we transform after.
    # There are 3 identical patterns (FINGERMOTION, FINGERDOWN, FINGERUP).
    # Same transform as mouse: after swap, g_DesktopWidth=physH, g_DesktopHeight=physW
    old_touch = (
        'input.x = event.tfinger.x * w * g_DesktopDPI * g_display.dpi_scale_x;\n'
        '\t\t\tinput.y = event.tfinger.y * h * g_DesktopDPI * g_display.dpi_scale_x;'
    )
    new_touch = (
        'input.x = event.tfinger.x * w * g_DesktopDPI * g_display.dpi_scale_x;\n'
        '\t\t\tinput.y = event.tfinger.y * h * g_DesktopDPI * g_display.dpi_scale_x;\n'
        '\t\t\tif (g_display.rotation == DisplayRotation::ROTATE_90) {\n'
        '\t\t\t\tfloat tmp = input.x;\n'
        '\t\t\t\tinput.x = input.y;\n'
        '\t\t\t\tinput.y = g_DesktopHeight * g_DesktopDPI * g_display.dpi_scale_x - tmp;\n'
        '\t\t\t} else if (g_display.rotation == DisplayRotation::ROTATE_270) {\n'
        '\t\t\t\tfloat tmp = input.x;\n'
        '\t\t\t\tinput.x = g_DesktopWidth * g_DesktopDPI * g_display.dpi_scale_x - input.y;\n'
        '\t\t\t\tinput.y = tmp;\n'
        '\t\t\t} else if (g_display.rotation == DisplayRotation::ROTATE_180) {\n'
        '\t\t\t\tinput.x = g_DesktopWidth * g_DesktopDPI * g_display.dpi_scale_x - input.x;\n'
        '\t\t\t\tinput.y = g_DesktopHeight * g_DesktopDPI * g_display.dpi_scale_x - input.y;\n'
        '\t\t\t}'
    )
    touch_count = content.count(old_touch)
    if touch_count == 0:
        print(f"ERROR: Could not find touch coordinate block in {filepath}")
        sys.exit(1)
    content = content.replace(old_touch, new_touch)
    changes += touch_count

    with open(filepath, 'w') as f:
        f.write(content)

    print(f"Patched display rotation support ({changes} modifications)")


if __name__ == '__main__':
    patch('SDL/SDLMain.cpp')
