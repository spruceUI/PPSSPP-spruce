#!/usr/bin/env python3
"""Add signal handler to print backtrace on crash.

Installs a SIGSEGV/SIGABRT/SIGFPE handler AFTER SDL_Init so it
overrides SDL's own signal handlers. Uses sigaction with SA_SIGINFO
to capture the faulting PC register from the signal context.
Requires -rdynamic linker flag and -funwind-tables for useful output.
"""
import sys

TARGET = 'SDL/SDLMain.cpp'

# Add includes at the top, before main
INCLUDE_OLD = 'int main(int argc, char *argv[]) {'
INCLUDE_NEW = '''#include <signal.h>
#include <execinfo.h>
#include <unistd.h>
#include <ucontext.h>

static void crash_handler(int sig, siginfo_t *info, void *ucontext) {
\tucontext_t *uc = (ucontext_t *)ucontext;
\tvoid *crash_pc = (void *)uc->uc_mcontext.pc;
\tfprintf(stderr, "\\n=== CRASH: signal %d ===\\n", sig);
\tfprintf(stderr, "Fault address: %p\\n", info->si_addr);
\tfprintf(stderr, "Crash PC: %p\\n", crash_pc);
\tfprintf(stderr, "--- backtrace ---\\n");
\tvoid *frames[64];
\tint n = backtrace(frames, 64);
\t// Replace the signal handler frame with the actual crash PC
\tif (n > 0) frames[0] = crash_pc;
\tbacktrace_symbols_fd(frames, n, STDERR_FILENO);
\tfprintf(stderr, "=== END BACKTRACE ===\\n");
\t_exit(1);
}

static void install_crash_handler() {
\tstruct sigaction sa;
\tsa.sa_sigaction = crash_handler;
\tsa.sa_flags = SA_SIGINFO | SA_RESETHAND;
\tsigemptyset(&sa.sa_mask);
\tsigaction(SIGSEGV, &sa, nullptr);
\tsigaction(SIGABRT, &sa, nullptr);
\tsigaction(SIGFPE, &sa, nullptr);
\tsigaction(SIGBUS, &sa, nullptr);
}

int main(int argc, char *argv[]) {'''

# Install handler right after SDL_Init succeeds, before SDL_VERSION
HANDLER_OLD = '''\tSDL_VERSION(&compiled);'''
HANDLER_NEW = '''\tinstall_crash_handler();  // After SDL_Init so we override SDL's signal handlers

\tSDL_VERSION(&compiled);'''

def patch(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    if INCLUDE_OLD not in content:
        print(f"WARNING: Could not find main() in {filepath}")
        sys.exit(1)

    if HANDLER_OLD not in content:
        print(f"WARNING: Could not find SDL_VERSION in {filepath}")
        sys.exit(1)

    content = content.replace(INCLUDE_OLD, INCLUDE_NEW, 1)
    content = content.replace(HANDLER_OLD, HANDLER_NEW, 1)

    with open(filepath, 'w') as f:
        f.write(content)

    print(f"Patched: added crash backtrace handler (installed after SDL_Init)")

if __name__ == '__main__':
    patch(TARGET)
