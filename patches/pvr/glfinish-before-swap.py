#!/usr/bin/env python3
"""Add glFinish() before SDL_GL_SwapWindow on PowerVR.

Some PowerVR drivers don't synchronize GPU rendering completion
before the buffer swap. Without glFinish(), the swap presents
an incomplete or empty buffer to the display.
"""
import sys

def patch(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    old = '''	renderManager_->SetSwapFunction([&]() {
#ifdef USING_EGL
		if (useEGLSwap)
			eglSwapBuffers(g_eglDisplay, g_eglSurface);
		else
			SDL_GL_SwapWindow(window_);
#else
		SDL_GL_SwapWindow(window_);
#endif
	});'''

    new = '''	renderManager_->SetSwapFunction([&]() {
#ifdef USING_EGL
		if (useEGLSwap)
			eglSwapBuffers(g_eglDisplay, g_eglSurface);
		else
			SDL_GL_SwapWindow(window_);
#else
		glFinish();
		SDL_GL_SwapWindow(window_);
#endif
	});'''

    if old not in content:
        print(f"WARNING: swap function block not found in {filepath}")
        sys.exit(1)

    content = content.replace(old, new)

    with open(filepath, 'w') as f:
        f.write(content)

    print(f"Patched: added glFinish() before SDL_GL_SwapWindow")

if __name__ == '__main__':
    patch('SDL/SDLGLGraphicsContext.cpp')
