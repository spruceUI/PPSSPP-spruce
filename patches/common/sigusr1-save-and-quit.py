#!/usr/bin/env python3
"""Add SIGUSR1 handler for external save-and-quit.

On spruceOS handhelds, the GameSwitcher needs to save state before
killing PPSSPP. This patch registers a SIGUSR1 handler that triggers
an async save state, then quits cleanly once the save completes.

Usage from shell: kill -USR1 $(pidof PPSSPPSDL)
"""
import sys

PATH = 'SDL/SDLMain.cpp'
with open(PATH) as f:
    src = f.read()

# --- 1. Add volatile flag near g_QuitRequested ---

OLD1 = '''static bool g_QuitRequested = false;
static bool g_RestartRequested = false;'''

NEW1 = '''static bool g_QuitRequested = false;
static bool g_RestartRequested = false;

static volatile sig_atomic_t g_saveAndQuit = 0;

static void saveAndQuitHandler(int) {
\tg_saveAndQuit = 1;
}'''

if OLD1 not in src:
    print(f'ERROR: cannot find g_QuitRequested block in {PATH}', file=sys.stderr)
    sys.exit(1)
src = src.replace(OLD1, NEW1, 1)

# --- 2. Add includes for SaveState and ParamSFO ---

OLD2 = '''#include "Core/System.h"'''

NEW2 = '''#include "Core/SaveState.h"
#include "Core/ELF/ParamSFO.h"
#include "Core/System.h"'''

if OLD2 not in src:
    print(f'ERROR: cannot find Core/System.h include in {PATH}', file=sys.stderr)
    sys.exit(1)
src = src.replace(OLD2, NEW2, 1)

# --- 3. Register SIGUSR1 handler after SIGPIPE ---

OLD3 = '''\t// Ignore sigpipe.
\tif (signal(SIGPIPE, SIG_IGN) == SIG_ERR) {
\t\tperror("Unable to ignore SIGPIPE");
\t}'''

NEW3 = '''\t// Ignore sigpipe.
\tif (signal(SIGPIPE, SIG_IGN) == SIG_ERR) {
\t\tperror("Unable to ignore SIGPIPE");
\t}

\t// Register SIGUSR1 handler for external save-and-quit (spruceOS GameSwitcher)
\tstruct sigaction sa = {};
\tsa.sa_handler = saveAndQuitHandler;
\tsa.sa_flags = SA_RESTART;
\tsigemptyset(&sa.sa_mask);
\tsigaction(SIGUSR1, &sa, NULL);'''

if OLD3 not in src:
    print(f'ERROR: cannot find SIGPIPE block in {PATH}', file=sys.stderr)
    sys.exit(1)
src = src.replace(OLD3, NEW3, 1)

# --- 4. Add save-and-quit check in Vulkan event loop ---

OLD4 = '''\t\tif (g_QuitRequested || g_RestartRequested)
\t\t\t\tbreak;

\t\t\tUpdateTextFocus();
\t\t\tUpdateSDLCursor();'''

NEW4 = '''\t\tif (g_QuitRequested || g_RestartRequested)
\t\t\t\tbreak;

\t\t\tif (g_saveAndQuit) {
\t\t\t\tg_saveAndQuit = 0;
\t\t\t\tif (PSP_IsInited() && GetUIState() == UISTATE_INGAME) {
\t\t\t\t\tSaveState::SaveSlot(SaveState::GetGamePrefix(g_paramSFO), g_Config.iCurrentStateSlot,
\t\t\t\t\t\t[](SaveState::Status status, std::string_view msg) {
\t\t\t\t\t\t\tg_QuitRequested = true;
\t\t\t\t\t\t});
\t\t\t\t} else {
\t\t\t\t\tg_QuitRequested = true;
\t\t\t\t}
\t\t\t}

\t\t\tUpdateTextFocus();
\t\t\tUpdateSDLCursor();'''

if OLD4 not in src:
    print(f'ERROR: cannot find Vulkan loop UpdateTextFocus block in {PATH}', file=sys.stderr)
    sys.exit(1)
src = src.replace(OLD4, NEW4, 1)

# --- 5. Add save-and-quit check in OpenGL event loop ---

OLD5 = '''\t} else while (true) {
\t\t{
\t\t\tSDL_Event event;
\t\t\twhile (SDL_PollEvent(&event)) {
\t\t\t\tProcessSDLEvent(window, event, &inputTracker);
\t\t\t}
\t\t}
\t\tif (g_QuitRequested || g_RestartRequested)'''

NEW5 = '''\t} else while (true) {
\t\t{
\t\t\tSDL_Event event;
\t\t\twhile (SDL_PollEvent(&event)) {
\t\t\t\tProcessSDLEvent(window, event, &inputTracker);
\t\t\t}
\t\t}
\t\tif (g_saveAndQuit) {
\t\t\tg_saveAndQuit = 0;
\t\t\tif (PSP_IsInited() && GetUIState() == UISTATE_INGAME) {
\t\t\t\tSaveState::SaveSlot(SaveState::GetGamePrefix(g_paramSFO), g_Config.iCurrentStateSlot,
\t\t\t\t\t[](SaveState::Status status, std::string_view msg) {
\t\t\t\t\t\tg_QuitRequested = true;
\t\t\t\t\t});
\t\t\t} else {
\t\t\t\tg_QuitRequested = true;
\t\t\t}
\t\t}
\t\tif (g_QuitRequested || g_RestartRequested)'''

if OLD5 not in src:
    print(f'ERROR: cannot find OpenGL loop block in {PATH}', file=sys.stderr)
    sys.exit(1)
src = src.replace(OLD5, NEW5, 1)

with open(PATH, 'w') as f:
    f.write(src)
print(f'Patched {PATH}: added SIGUSR1 save-and-quit handler')
