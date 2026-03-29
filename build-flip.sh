#!/bin/bash
set -e

PPSSPP_VERSION="${PPSSPP_VERSION:-v1.20.3}"
OUTPUT_DIR="${OUTPUT_DIR:-/output}"

echo "=== Building PPSSPP ${PPSSPP_VERSION} for Miyoo Flip (RK3566 / Mali G52) ==="

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

# Apply flip-specific patches
for patch in /patches/flip/*.py; do
    [ -f "$patch" ] && python3 "$patch" && echo "Applied: $(basename $patch)"
done

mkdir -p build && cd build

# Cross-compilation environment
export CCACHE_DIR="${CCACHE_DIR:-/ccache}"
export PATH="/opt/flip/bin:/opt/flip/aarch64-flip-linux-gnu/bin:${PATH}"

# Configure for Flip: SDL2 + GLES2, fbdev, no X11/Wayland/Vulkan
cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_TOOLCHAIN_FILE=/tmp/flip-toolchain.cmake \
    -DCMAKE_C_COMPILER_LAUNCHER=ccache \
    -DCMAKE_CXX_COMPILER_LAUNCHER=ccache \
    -DCMAKE_C_FLAGS="-Ofast -mcpu=cortex-a55 -ffunction-sections -fdata-sections -fomit-frame-pointer -flto -Wno-error" \
    -DCMAKE_CXX_FLAGS="-Ofast -mcpu=cortex-a55 -ffunction-sections -fdata-sections -fomit-frame-pointer -flto -Wno-error" \
    -DCMAKE_EXE_LINKER_FLAGS="-Wl,--gc-sections -flto" \
    -DUSING_GLES2=ON \
    -DUSING_EGL=ON \
    -DUSING_FBDEV=ON \
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
cp PPSSPPSDL "$OUTPUT_DIR/PPSSPPSDL_Flip"
/opt/flip/aarch64-flip-linux-gnu/bin/strip "$OUTPUT_DIR/PPSSPPSDL_Flip"

# Copy assets (required at runtime)
cp -r ../assets "$OUTPUT_DIR/assets"

echo "=== Build complete: ${OUTPUT_DIR}/PPSSPPSDL_Flip ==="
