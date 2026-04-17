#!/usr/bin/env python3
"""Add signal handler to print backtrace on crash.

Installs a SIGSEGV/SIGABRT handler in SDL main that prints a
stack trace to stderr before exiting. Requires -rdynamic linker
flag and -funwind-tables for useful output.
"""
import sys

TARGET = 'SDL/SDLMain.cpp'

# Insert the signal handler before the main function
OLD = 'int main(int argc, char *argv[]) {'

NEW = '''#include <signal.h>
#include <execinfo.h>
#include <unistd.h>

static void crash_handler(int sig) {
\tfprintf(stderr, "\\n=== CRASH: signal %d ===\\n", sig);
\tvoid *frames[64];
\tint n = backtrace(frames, 64);
\tbacktrace_symbols_fd(frames, n, STDERR_FILENO);
\tfprintf(stderr, "=== END BACKTRACE ===\\n");
\t_exit(1);
}

int main(int argc, char *argv[]) {
\tsignal(SIGSEGV, crash_handler);
\tsignal(SIGABRT, crash_handler);
\tsignal(SIGFPE, crash_handler);'''

def patch(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    if OLD not in content:
        print(f"WARNING: Could not find main() in {filepath}")
        sys.exit(1)

    content = content.replace(OLD, NEW, 1)

    with open(filepath, 'w') as f:
        f.write(content)

    print(f"Patched: added crash backtrace signal handler")

if __name__ == '__main__':
    patch(TARGET)
