#!/bin/bash
set -e

PPSSPP_VERSION="${PPSSPP_VERSION:-v1.20.3}"
OUTPUT_DIR="${OUTPUT_DIR:-/output}"

echo "=== Building PPSSPP ${PPSSPP_VERSION} for aarch64 (universal 64-bit) ==="

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

# Apply 64-bit-specific patches
for patch in /patches/64/*.py; do
    [ -f "$patch" ] && python3 "$patch" && echo "Applied: $(basename $patch)"
done

mkdir -p build && cd build

# Cross-compilation environment
export CCACHE_DIR="${CCACHE_DIR:-/ccache}"

# Configure for universal 64-bit: SDL2 + OpenGL ES2, no X11/Wayland
cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_TOOLCHAIN_FILE=/tmp/aarch64-toolchain.cmake \
    -DCMAKE_C_COMPILER_LAUNCHER=ccache \
    -DCMAKE_CXX_COMPILER_LAUNCHER=ccache \
    -DUSING_GLES2=ON \
    -DUSING_EGL=ON \
    -DUSING_FBDEV=ON \
    -DVULKAN=OFF \
    -DUSING_X11_VULKAN=OFF \
    -DUSE_WAYLAND_WSI=OFF \
    -DUSE_DISCORD=OFF \
    -DUSE_MINIUPNPC=OFF \
    -DHEADLESS=OFF

# Build
make -j$(nproc) PPSSPPSDL

# Output
mkdir -p "$OUTPUT_DIR"
cp PPSSPPSDL "$OUTPUT_DIR/"
aarch64-linux-gnu-strip "$OUTPUT_DIR/PPSSPPSDL"

# Copy assets (required at runtime)
cp -r ../assets "$OUTPUT_DIR/assets"

echo "=== Build complete: ${OUTPUT_DIR}/PPSSPPSDL ==="
