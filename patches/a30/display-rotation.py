#!/usr/bin/env python3
"""Add display rotation support for portrait-panel devices (e.g., Miyoo A30).

Reads the DISPLAY_ROTATION environment variable (0, 90, 180, 270) and
activates PPSSPP's existing DisplayRotation infrastructure for SDL/OpenGL.
PPSSPP already has rotation support (rot_matrix, ComputeOrthoMatrix,
CopyToOutput vertex rotation) but it's only wired up for Vulkan/UWP.
This patch wires it up for SDL/OpenGL.

Files modified:
  SDL/SDLMain.cpp — rotation detection, dimension swap, input transform
  Common/GPU/OpenGL/GLQueueRunner.cpp — viewport/scissor rotation for backbuffer
    (mirrors what VulkanQueueRunner already does with RotateRectToDisplay)
"""
import sys


def patch_sdlmain(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    changes = 0

    # ── Mod 1: Add rotation detection after display mode detection ──
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
        '\t\t// DISPLAY_ROTATION is how far the panel is rotated from normal;\n'
        '\t\t// we apply the inverse rotation to compensate.\n'
        '\t\t// We apply the inverse rotation to compensate for panel orientation.\n'
        '\t\tswitch (rot_deg) {\n'
        '\t\tcase 90:\n'
        '\t\t\tg_display.rotation = DisplayRotation::ROTATE_270;\n'
        '\t\t\tg_display.rot_matrix.setRotationZ270();\n'
        '\t\t\tstd::swap(g_DesktopWidth, g_DesktopHeight);\n'
        '\t\t\tbreak;\n'
        '\t\tcase 180:\n'
        '\t\t\tg_display.rotation = DisplayRotation::ROTATE_180;\n'
        '\t\t\tg_display.rot_matrix.setRotationZ180();\n'
        '\t\t\tbreak;\n'
        '\t\tcase 270:\n'
        '\t\t\tg_display.rotation = DisplayRotation::ROTATE_90;\n'
        '\t\t\tg_display.rot_matrix.setRotationZ90();\n'
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

    # ── Mod 4: Transform touch coordinates (3 identical sites) ──
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

    print(f"Patched {filepath}: {changes} modifications")


def patch_glqueuerunner(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    changes = 0

    # ── Add Display.h include (for DisplayRotation enum and g_display) ──
    old = '#include "Common/Math/math_util.h"'
    new = '#include "Common/Math/math_util.h"\n#include "Common/System/Display.h"'
    if old not in content:
        print(f"ERROR: Could not find math_util include in {filepath}")
        sys.exit(1)
    content = content.replace(old, new, 1)
    changes += 1

    # ── Viewport: rotate for backbuffer ──
    # For GL with ortho*rot, dp(x,y) maps to physical(y,x) for ROTATE_90.
    # The viewport/scissor must use the same transform: just swap x/y and w/h.
    # Don't use RotateRectToDisplay (Vulkan formula) — it doesn't match the
    # GL ortho*rot shader transform due to different Y conventions.
    old = (
        'case GLRRenderCommand::VIEWPORT:\n'
        '\t\t{\n'
        '\t\t\tfloat y = c.viewport.vp.y;\n'
        '\t\t\tif (!curFB_)\n'
        '\t\t\t\ty = curFBHeight_ - y - c.viewport.vp.h;\n'
        '\n'
        '\t\t\t// TODO: Support FP viewports through glViewportArrays\n'
        '\t\t\tif (viewport.x != c.viewport.vp.x || viewport.y != y || viewport.w != c.viewport.vp.w || viewport.h != c.viewport.vp.h) {\n'
        '\t\t\t\tglViewport((GLint)c.viewport.vp.x, (GLint)y, (GLsizei)c.viewport.vp.w, (GLsizei)c.viewport.vp.h);'
    )
    new = (
        'case GLRRenderCommand::VIEWPORT:\n'
        '\t\t{\n'
        '\t\t\tfloat vp_x = c.viewport.vp.x;\n'
        '\t\t\tfloat vp_y = c.viewport.vp.y;\n'
        '\t\t\tfloat vp_w = c.viewport.vp.w;\n'
        '\t\t\tfloat vp_h = c.viewport.vp.h;\n'
        '\t\t\tif (!curFB_) {\n'
        '\t\t\t\tif (g_display.rotation == DisplayRotation::ROTATE_90 || g_display.rotation == DisplayRotation::ROTATE_270) {\n'
        '\t\t\t\t\tstd::swap(vp_x, vp_y);\n'
        '\t\t\t\t\tstd::swap(vp_w, vp_h);\n'
        '\t\t\t\t} else {\n'
        '\t\t\t\t\tvp_y = curFBHeight_ - vp_y - vp_h;\n'
        '\t\t\t\t}\n'
        '\t\t\t}\n'
        '\n'
        '\t\t\t// TODO: Support FP viewports through glViewportArrays\n'
        '\t\t\tif (viewport.x != vp_x || viewport.y != vp_y || viewport.w != vp_w || viewport.h != vp_h) {\n'
        '\t\t\t\tglViewport((GLint)vp_x, (GLint)vp_y, (GLsizei)vp_w, (GLsizei)vp_h);'
    )
    if old not in content:
        print(f"ERROR: Could not find VIEWPORT block in {filepath}")
        sys.exit(1)
    content = content.replace(old, new, 1)
    changes += 1

    # Update the viewport cache variables to use our transformed values
    old = (
        '\t\t\t\tviewport.x = c.viewport.vp.x;\n'
        '\t\t\t\tviewport.y = y;\n'
        '\t\t\t\tviewport.w = c.viewport.vp.w;\n'
        '\t\t\t\tviewport.h = c.viewport.vp.h;'
    )
    new = (
        '\t\t\t\tviewport.x = vp_x;\n'
        '\t\t\t\tviewport.y = vp_y;\n'
        '\t\t\t\tviewport.w = vp_w;\n'
        '\t\t\t\tviewport.h = vp_h;'
    )
    if old not in content:
        print(f"ERROR: Could not find viewport cache block in {filepath}")
        sys.exit(1)
    content = content.replace(old, new, 1)
    changes += 1

    # ── Scissor: same swap treatment as viewport ──
    old = (
        'case GLRRenderCommand::SCISSOR:\n'
        '\t\t{\n'
        '\t\t\tint y = c.scissor.rc.y;\n'
        '\t\t\tif (!curFB_)\n'
        '\t\t\t\ty = curFBHeight_ - y - c.scissor.rc.h;\n'
        '\t\t\tif (scissorRc.x != c.scissor.rc.x || scissorRc.y != y || scissorRc.w != c.scissor.rc.w || scissorRc.h != c.scissor.rc.h) {\n'
        '\t\t\t\tglScissor(c.scissor.rc.x, y, c.scissor.rc.w, c.scissor.rc.h);\n'
        '\t\t\t\tscissorRc.x = c.scissor.rc.x;\n'
        '\t\t\t\tscissorRc.y = y;\n'
        '\t\t\t\tscissorRc.w = c.scissor.rc.w;\n'
        '\t\t\t\tscissorRc.h = c.scissor.rc.h;\n'
        '\t\t\t}'
    )
    new = (
        'case GLRRenderCommand::SCISSOR:\n'
        '\t\t{\n'
        '\t\t\tint sc_x = c.scissor.rc.x;\n'
        '\t\t\tint sc_y = c.scissor.rc.y;\n'
        '\t\t\tint sc_w = c.scissor.rc.w;\n'
        '\t\t\tint sc_h = c.scissor.rc.h;\n'
        '\t\t\tif (!curFB_) {\n'
        '\t\t\t\tif (g_display.rotation == DisplayRotation::ROTATE_90 || g_display.rotation == DisplayRotation::ROTATE_270) {\n'
        '\t\t\t\t\tstd::swap(sc_x, sc_y);\n'
        '\t\t\t\t\tstd::swap(sc_w, sc_h);\n'
        '\t\t\t\t} else {\n'
        '\t\t\t\t\tsc_y = curFBHeight_ - sc_y - sc_h;\n'
        '\t\t\t\t}\n'
        '\t\t\t}\n'
        '\t\t\tif (scissorRc.x != sc_x || scissorRc.y != sc_y || scissorRc.w != sc_w || scissorRc.h != sc_h) {\n'
        '\t\t\t\tglScissor(sc_x, sc_y, sc_w, sc_h);\n'
        '\t\t\t\tscissorRc.x = sc_x;\n'
        '\t\t\t\tscissorRc.y = sc_y;\n'
        '\t\t\t\tscissorRc.w = sc_w;\n'
        '\t\t\t\tscissorRc.h = sc_h;\n'
        '\t\t\t}'
    )
    if old not in content:
        print(f"ERROR: Could not find SCISSOR block in {filepath}")
        sys.exit(1)
    content = content.replace(old, new, 1)
    changes += 1

    with open(filepath, 'w') as f:
        f.write(content)

    print(f"Patched {filepath}: {changes} modifications")


if __name__ == '__main__':
    patch_sdlmain('SDL/SDLMain.cpp')
    patch_glqueuerunner('Common/GPU/OpenGL/GLQueueRunner.cpp')
