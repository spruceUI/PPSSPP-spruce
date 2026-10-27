#!/usr/bin/env python3
"""Force a fullscreen window when USING_FBDEV is off.

SDLMain.cpp only adds a fullscreen flag inside the USING_FBDEV branch:

    #elif defined(USING_FBDEV) || PPSSPP_PLATFORM(SWITCH)
        mode |= SDL_WINDOW_FULLSCREEN_DESKTOP;
    #else
        mode |= SDL_WINDOW_RESIZABLE | SDL_WINDOW_ALLOW_HIGHDPI;

The dArkMoss builds turn USING_FBDEV off - it is what made PPSSPP render into
/dev/fb0 instead of the KMS plane - so without this it takes the desktop
branch and asks for a resizable window. There is no window manager on KMSDRM,
and the block just below keys the render resolution off the fullscreen flag:

    if (mode & SDL_WINDOW_FULLSCREEN) {
        g_display.pixel_xres = g_DesktopWidth; ...

so losing the flag also loses the correct resolution.

Runs after patches/common/fullscreen.py, which has already rewritten
SDL_WINDOW_FULLSCREEN_DESKTOP to SDL_WINDOW_FULLSCREEN throughout this file -
hence matching on the desktop branch's own text rather than on that constant.
"""
import sys

PATH = "SDL/SDLMain.cpp"
OLD = "mode |= SDL_WINDOW_RESIZABLE | SDL_WINDOW_ALLOW_HIGHDPI;"
NEW = "mode |= SDL_WINDOW_FULLSCREEN;  // dArkMoss: KMSDRM, no window manager"

with open(PATH) as f:
    src = f.read()

if OLD not in src:
    print(f"ERROR: could not find the windowed branch in {PATH}", file=sys.stderr)
    sys.exit(1)

n = src.count(OLD)
src = src.replace(OLD, NEW)
with open(PATH, "w") as f:
    f.write(src)
print(f"Patched {n} windowed-mode branch(es) to fullscreen in {PATH}")
