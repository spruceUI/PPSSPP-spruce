#!/usr/bin/env python3
"""Add SIGUSR2 handler to toggle the pause menu externally.

On spruceOS handhelds, the home button is handled by the OS-level
homebutton_watchdog. When the user's tap-home action is set to
"Emulator menu", the watchdog sends SIGUSR2 to PPSSPP to open the
pause menu — no need for a button combo like SELECT+X.

Usage from shell: kill -USR2 $(pidof PPSSPPSDL)

Requires: sigusr1-save-and-quit.py must be applied first (adds the
signal infrastructure this patch extends).
"""
import sys

PATH = 'SDL/SDLMain.cpp'
with open(PATH) as f:
    src = f.read()

# --- 1. Add volatile flag and handler after the SIGUSR1 handler ---

OLD1 = '''static void saveAndQuitHandler(int) {
\tg_saveAndQuit = 1;
}'''

NEW1 = '''static void saveAndQuitHandler(int) {
\tg_saveAndQuit = 1;
}

static volatile sig_atomic_t g_togglePauseMenu = 0;

static void togglePauseMenuHandler(int) {
\tg_togglePauseMenu = 1;
}'''

if OLD1 not in src:
    print(f'ERROR: cannot find saveAndQuitHandler in {PATH} (sigusr1 patch applied?)', file=sys.stderr)
    sys.exit(1)
src = src.replace(OLD1, NEW1, 1)

# --- 2. Register SIGUSR2 handler after SIGUSR1 registration ---

OLD2 = '''\tsigaction(SIGUSR1, &sa, NULL);'''

NEW2 = '''\tsigaction(SIGUSR1, &sa, NULL);

\t// Register SIGUSR2 handler for external pause menu toggle (spruceOS home button)
\tsa.sa_handler = togglePauseMenuHandler;
\tsigaction(SIGUSR2, &sa, NULL);'''

if OLD2 not in src:
    print(f'ERROR: cannot find SIGUSR1 sigaction in {PATH}', file=sys.stderr)
    sys.exit(1)
src = src.replace(OLD2, NEW2, 1)

# --- 3. Add pause menu toggle check in Vulkan event loop ---
# Inserted between the g_saveAndQuit block and UpdateTextFocus()

OLD3 = '''\t\t\t\t} else {
\t\t\t\t\tg_QuitRequested = true;
\t\t\t\t}
\t\t\t}

\t\t\tUpdateTextFocus();'''

NEW3 = '''\t\t\t\t} else {
\t\t\t\t\tg_QuitRequested = true;
\t\t\t\t}
\t\t\t}

\t\t\tif (g_togglePauseMenu) {
\t\t\t\tg_togglePauseMenu = 0;
\t\t\t\tSystem_PostUIMessage(UIMessage::REQUEST_GAME_PAUSE);
\t\t\t}

\t\t\tUpdateTextFocus();'''

if OLD3 not in src:
    print(f'ERROR: cannot find Vulkan loop g_saveAndQuit tail in {PATH}', file=sys.stderr)
    sys.exit(1)
src = src.replace(OLD3, NEW3, 1)

# --- 4. Add pause menu toggle check in OpenGL event loop ---
# Inserted between the g_saveAndQuit block and g_QuitRequested check

OLD4 = '''\t\t\t} else {
\t\t\t\tg_QuitRequested = true;
\t\t\t}
\t\t}
\t\tif (g_QuitRequested || g_RestartRequested)'''

NEW4 = '''\t\t\t} else {
\t\t\t\tg_QuitRequested = true;
\t\t\t}
\t\t}
\t\tif (g_togglePauseMenu) {
\t\t\tg_togglePauseMenu = 0;
\t\t\tSystem_PostUIMessage(UIMessage::REQUEST_GAME_PAUSE);
\t\t}
\t\tif (g_QuitRequested || g_RestartRequested)'''

if OLD4 not in src:
    print(f'ERROR: cannot find OpenGL loop g_saveAndQuit tail in {PATH}', file=sys.stderr)
    sys.exit(1)
src = src.replace(OLD4, NEW4, 1)

with open(PATH, 'w') as f:
    f.write(src)
print(f'Patched {PATH}: added SIGUSR2 pause menu toggle handler')
