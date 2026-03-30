#!/bin/bash
set -e

PPSSPP_VERSION="${PPSSPP_VERSION:-d357e6a32934800d3d80b49f910a603e1b069751}"
OUTPUT_DIR="${OUTPUT_DIR:-/output}"

echo "=== Building PPSSPP for Pixel2 (RK3326 / Mali-G52, aarch64 native) ==="
echo "=== Ref: ${PPSSPP_VERSION} ==="

# Clone PPSSPP with submodules
if [ ! -d "ppsspp" ]; then
    git clone --recurse-submodules --shallow-submodules \
        https://github.com/hrydgard/ppsspp.git
    cd ppsspp
    git checkout "$PPSSPP_VERSION"
    git submodule update --recursive
else
    cd ppsspp
fi

# Apply common patches
echo "=== Applying patches ==="
for patch in /patches/common/*.py; do
    [ -f "$patch" ] || continue
    python3 "$patch" && echo "Applied: $(basename $patch)"
done

# Apply pixel2-specific patches
for patch in /patches/pixel2/*.py; do
    [ -f "$patch" ] || continue
    python3 "$patch" && echo "Applied: $(basename $patch)"
done

mkdir -p build && cd build

# Set up ccache
export CCACHE_DIR="${CCACHE_DIR:-/ccache}"

# Configure — Hario's exact flags for Pixel2
cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_C_COMPILER=/usr/bin/clang \
    -DCMAKE_CXX_COMPILER=/usr/bin/clang++ \
    -DCMAKE_C_COMPILER_LAUNCHER=ccache \
    -DCMAKE_CXX_COMPILER_LAUNCHER=ccache \
    -DCMAKE_C_FLAGS="-Ofast -fno-tree-slp-vectorize -D_NDEBUG -march=armv8-a+crc -mtune=cortex-a35 -ftree-vectorize -funsafe-math-optimizations" \
    -DCMAKE_CXX_FLAGS="-Ofast -fno-tree-slp-vectorize -D_NDEBUG -march=armv8-a+crc -mtune=cortex-a35 -ftree-vectorize -funsafe-math-optimizations -fpermissive" \
    -DUSING_GLES2=ON \
    -DUSING_EGL=OFF \
    -DUSING_FBDEV=ON \
    -DVULKAN=OFF \
    -DUSING_X11_VULKAN=OFF \
    -DUSE_WAYLAND_WSI=OFF \
    -DUSE_VULKAN_DISPLAY_KHR=OFF \
    -DUSE_FFMPEG=YES \
    -DUSE_SYSTEM_FFMPEG=NO \
    -DUSE_SYSTEM_LIBPNG=OFF \
    -DUSE_MINIUPNPC=OFF \
    -DUSING_QT_UI=OFF \
    -DUSE_DISCORD=OFF \
    -DSDL2_LIBRARY="/usr/lib/aarch64-linux-gnu/libSDL2.so" \
    -DSDL2_INCLUDE_DIR="/usr/include/SDL2"

# Build
make -j$(nproc) PPSSPPSDL
strip -s PPSSPPSDL

# Output
mkdir -p "$OUTPUT_DIR"
cp PPSSPPSDL "$OUTPUT_DIR/PPSSPPSDL_Pixel2"

# Copy assets (required at runtime)
cp -r ../assets "$OUTPUT_DIR/assets"

echo "=== Build complete: ${OUTPUT_DIR}/PPSSPPSDL_Pixel2 ==="
