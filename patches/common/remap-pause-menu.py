#!/usr/bin/env python3
"""Disable Guide/Home button from opening PPSSPP pause menu.

On spruceOS handhelds, the home button is handled by the OS-level
homebutton_watchdog for GameSwitcher and emulator exit. PPSSPP's
default mapping of Guide → NKCODE_BACK (pause menu) interferes
with this. Users can open the PPSSPP menu via SELECT+X instead
(configured in controls.ini).
"""
import sys

PATH = 'SDL/SDLJoystick.cpp'
with open(PATH) as f:
    src = f.read()

OLD = '''\tcase SDL_CONTROLLER_BUTTON_GUIDE:
\t\treturn NKCODE_BACK; // pause menu'''

NEW = '''\tcase SDL_CONTROLLER_BUTTON_GUIDE:
\t\treturn NKCODE_BUTTON_16; // spruceOS: home button handled by OS watchdog, use dead-end keycode to absorb the input'''

if OLD not in src:
    print(f'ERROR: cannot find GUIDE button mapping in {PATH}', file=sys.stderr)
    sys.exit(1)

src = src.replace(OLD, NEW, 1)

with open(PATH, 'w') as f:
    f.write(src)
print(f'Patched {PATH}: Guide button no longer opens pause menu')
