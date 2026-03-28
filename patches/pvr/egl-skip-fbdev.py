#!/usr/bin/env python3
"""Fix EGL init on FBDEV+PowerVR by using SDL's EGL display/surface.

On PowerVR devices with SDL2's mali-fbdev driver, SDL successfully
creates an EGL context internally. PPSSPP's EGL_Open/EGL_Init then
tries to create a SECOND context with nullptr window, which fails.

Fix: On FBDEV, skip PPSSPP's EGL init entirely and grab SDL's
existing EGL display/surface so PPSSPP can use eglSwapBuffers.
"""
import sys

def patch(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Replace the EGL init block to reuse SDL's EGL state on FBDEV
    old = """#ifdef USING_EGL
	if (EGL_Open(window) != 0) {
		fprintf(stderr, "EGL_Open() failed\\n");
	} else if (EGL_Init(window) != 0) {
		fprintf(stderr, "EGL_Init() failed\\n");
	} else {
		useEGLSwap = true;
	}
#endif"""

    new = """#ifdef USING_EGL
#ifdef USING_FBDEV
	// On FBDEV (PowerVR/Mali), SDL already created an EGL context.
	// Grab its display and surface so we can use eglSwapBuffers.
	g_eglDisplay = eglGetCurrentDisplay();
	g_eglSurface = eglGetCurrentSurface(EGL_DRAW);
	g_eglContext = eglGetCurrentContext();
	if (g_eglDisplay != EGL_NO_DISPLAY && g_eglSurface != EGL_NO_SURFACE) {
		useEGLSwap = true;
	}
#else
	if (EGL_Open(window) != 0) {
		fprintf(stderr, "EGL_Open() failed\\n");
	} else if (EGL_Init(window) != 0) {
		fprintf(stderr, "EGL_Init() failed\\n");
	} else {
		useEGLSwap = true;
	}
#endif
#endif"""

    if old not in content:
        print(f"WARNING: EGL init block not found in {filepath}")
        sys.exit(1)

    content = content.replace(old, new)

    # Also guard EGL_Close to not destroy SDL's context on FBDEV
    old_close = """void EGL_Close() {
	if (g_eglDisplay != EGL_NO_DISPLAY) {
		eglMakeCurrent(g_eglDisplay, NULL, NULL, EGL_NO_CONTEXT);
		if (g_eglContext != NULL) {
			eglDestroyContext(g_eglDisplay, g_eglContext);
		}
		if (g_eglSurface != NULL) {
			eglDestroySurface(g_eglDisplay, g_eglSurface);
		}
		eglTerminate(g_eglDisplay);
		g_eglDisplay = EGL_NO_DISPLAY;
	}"""

    new_close = """void EGL_Close() {
	if (g_eglDisplay != EGL_NO_DISPLAY) {
#ifdef USING_FBDEV
		// Don't destroy SDL's EGL context — just clear our references
		g_eglDisplay = EGL_NO_DISPLAY;
#else
		eglMakeCurrent(g_eglDisplay, NULL, NULL, EGL_NO_CONTEXT);
		if (g_eglContext != NULL) {
			eglDestroyContext(g_eglDisplay, g_eglContext);
		}
		if (g_eglSurface != NULL) {
			eglDestroySurface(g_eglDisplay, g_eglSurface);
		}
		eglTerminate(g_eglDisplay);
		g_eglDisplay = EGL_NO_DISPLAY;
#endif
	}"""

    if old_close not in content:
        print(f"WARNING: EGL_Close block not found in {filepath}")
        sys.exit(1)

    content = content.replace(old_close, new_close)

    with open(filepath, 'w') as f:
        f.write(content)

    print(f"Patched: FBDEV reuses SDL's EGL context instead of creating its own")

if __name__ == '__main__':
    patch('SDL/SDLGLGraphicsContext.cpp')
