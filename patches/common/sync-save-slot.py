#!/usr/bin/env python3
"""Add SyncSaveSlot to SaveState — synchronous save for SIGUSR1 handler.

SaveSlot is async (queues for next frame). SyncSaveSlot uses
CChunkFileReader::Save directly to capture and write state
immediately, without the game advancing.
"""
import sys

# --- 1. Add declaration to SaveState.h ---

PATH_H = 'Core/SaveState.h'
with open(PATH_H) as f:
    src_h = f.read()

OLD_H = '\tCChunkFileReader::Error SaveToRam(std::vector<u8> &state);'

NEW_H = '''\tCChunkFileReader::Error SaveToRam(std::vector<u8> &state);
\tvoid SyncSaveSlot(std::string_view gamePrefix, int slot);'''

if OLD_H not in src_h:
    print(f'ERROR: cannot find SaveToRam declaration in {PATH_H}', file=sys.stderr)
    sys.exit(1)
src_h = src_h.replace(OLD_H, NEW_H, 1)

with open(PATH_H, 'w') as f:
    f.write(src_h)
print(f'Patched {PATH_H}: added SyncSaveSlot declaration')

# --- 2. Add implementation to SaveState.cpp ---

PATH_CPP = 'Core/SaveState.cpp'
with open(PATH_CPP) as f:
    src_cpp = f.read()

# Add after SaveToRam/LoadFromRam block
OLD_CPP = '''\tCChunkFileReader::Error LoadFromRam(std::vector<u8> &data, std::string *errorString) {
\t\tSaveStart state;
\t\treturn CChunkFileReader::LoadPtr(&data[0], state, errorString);
\t}'''

NEW_CPP = '''\tCChunkFileReader::Error LoadFromRam(std::vector<u8> &data, std::string *errorString) {
\t\tSaveStart state;
\t\treturn CChunkFileReader::LoadPtr(&data[0], state, errorString);
\t}

\tvoid SyncSaveSlot(std::string_view gamePrefix, int slot) {
\t\tPath fn = GenerateSaveSlotPath(gamePrefix, slot, STATE_EXTENSION);
\t\tif (fn.empty()) return;
\t\tstd::string title = g_paramSFO.GetValueString("TITLE");
\t\tif (title.empty()) {
\t\t\ttitle = PSP_CoreParameter().fileToStart.ToVisualString();
\t\t\tstd::size_t lslash = title.find_last_of('/');
\t\t\ttitle = title.substr(lslash + 1);
\t\t}
\t\tSaveStart state;
\t\tCChunkFileReader::Error result = CChunkFileReader::Save(fn, title, PPSSPP_GIT_VERSION, state);
\t\tif (result == CChunkFileReader::ERROR_NONE) {
\t\t\tINFO_LOG(Log::SaveState, "SyncSaveSlot: saved to '%s'", fn.c_str());
\t\t} else {
\t\t\tERROR_LOG(Log::SaveState, "SyncSaveSlot: failed to save to '%s'", fn.c_str());
\t\t}
\t}'''

if OLD_CPP not in src_cpp:
    print(f'ERROR: cannot find LoadFromRam block in {PATH_CPP}', file=sys.stderr)
    sys.exit(1)
src_cpp = src_cpp.replace(OLD_CPP, NEW_CPP, 1)

with open(PATH_CPP, 'w') as f:
    f.write(src_cpp)
print(f'Patched {PATH_CPP}: added SyncSaveSlot implementation')
