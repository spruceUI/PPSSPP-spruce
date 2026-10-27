#!/bin/bash
set -e

PPSSPP_VERSION="${PPSSPP_VERSION:-v1.20.3}"
OUTPUT_DIR="${OUTPUT_DIR:-/output}"

echo "=== Building PPSSPP ${PPSSPP_VERSION} for dArkMoss RK3566 (Cortex-A55 / Mali G52, KMSDRM) ==="

# Clone PPSSPP with submodules
if [ ! -d "ppsspp" ]; then
    git clone --depth 1 --branch "$PPSSPP_VERSION" \
        --recurse-submodules --shallow-submodules \
        https://github.com/hrydgard/ppsspp.git
fi

cd ppsspp

# Apply common patches
echo "=== Applying patches ==="
for patch in /patches/common/*.py; do
    [ -f "$patch" ] && python3 "$patch" && echo "Applied: $(basename $patch)"
done

# Apply dArkMoss patches
for patch in /patches/darkmoss/*.py; do
    [ -f "$patch" ] && python3 "$patch" && echo "Applied: $(basename $patch)"
done

mkdir -p build && cd build

# Cross-compilation environment
export CCACHE_DIR="${CCACHE_DIR:-/ccache}"
export PATH="/opt/flip/bin:/opt/flip/aarch64-flip-linux-gnu/bin:${PATH}"

# Configure for dArkMoss: SDL2 + GLES2 on KMSDRM, and crucially NOT fbdev.
#
# USING_FBDEV makes EGL_Open() pass a null native display and window, which on
# a Mali blob resolves to /dev/fb0. On dArkMoss that is a dead emulated shim -
# it reads back all zeros and nothing scans it out. Measured on hardware: with
# the Flip build, PPSSPP held DRM master and presented a 720x1440 framebuffer
# (exactly fb0's virtual_size) that was entirely black, while the game booted
# and emulated normally underneath.
#
# USING_EGL=OFF hands the context and the buffer swap back to SDL
# (SDL_GL_SwapWindow), so PPSSPP draws into the GBM surface SDL already owns.
# Still GLES2 - the ES profile request in SDLGLGraphicsContext.cpp is what
# USING_GLES2 controls, and that part was always correct.
cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_TOOLCHAIN_FILE=/tmp/flip-toolchain.cmake \
    -DCMAKE_C_COMPILER_LAUNCHER=ccache \
    -DCMAKE_CXX_COMPILER_LAUNCHER=ccache \
    -DCMAKE_C_FLAGS="-Ofast -mcpu=cortex-a55 -ffunction-sections -fdata-sections -fomit-frame-pointer -flto=auto -Wno-error" \
    -DCMAKE_CXX_FLAGS="-Ofast -mcpu=cortex-a55 -ffunction-sections -fdata-sections -fomit-frame-pointer -flto=auto -Wno-error" \
    -DCMAKE_EXE_LINKER_FLAGS="-Wl,--gc-sections -flto=auto" \
    -DUSING_GLES2=ON \
    -DUSING_EGL=OFF \
    -DUSING_FBDEV=OFF \
    -DVULKAN=OFF \
    -DUSING_X11_VULKAN=OFF \
    -DUSE_WAYLAND_WSI=OFF \
    -DBUILD_SHARED_LIBS=OFF \
    -DUSE_SYSTEM_LIBPNG=OFF \
    -DUSE_SYSTEM_FFMPEG=OFF \
    -DUSE_DISCORD=OFF \
    -DUSE_MINIUPNPC=OFF \
    -DHEADLESS=OFF \
    -DUNITTEST=OFF \
    -DCMAKE_DISABLE_FIND_PACKAGE_SDL2_ttf=ON \
    -DCMAKE_DISABLE_FIND_PACKAGE_Fontconfig=ON \
    -DCMAKE_DISABLE_FIND_PACKAGE_X11=ON

# Fix cross-compile: -isystem paths get sysroot-prepended by GCC, breaking includes
find . \( -name 'flags.make' -o -name 'build.ninja' \) -exec sed -i 's|-isystem |-I|g' {} +

# Build
make -j$(nproc) PPSSPPSDL

# Output
mkdir -p "$OUTPUT_DIR"
cp PPSSPPSDL "$OUTPUT_DIR/PPSSPPSDL_dArkMoss3566"
/opt/flip/aarch64-flip-linux-gnu/bin/strip -s "$OUTPUT_DIR/PPSSPPSDL_dArkMoss3566"

# Copy assets (required at runtime)
cp -r ../assets "$OUTPUT_DIR/assets"

echo "=== Build complete: ${OUTPUT_DIR}/PPSSPPSDL_dArkMoss3566 ==="
