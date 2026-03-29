#!/bin/bash
set -e

PPSSPP_VERSION="${PPSSPP_VERSION:-v1.20.3}"
OUTPUT_DIR="${OUTPUT_DIR:-/output}"

echo "=== Building PPSSPP ${PPSSPP_VERSION} for Brick/TSP (A133 / PowerVR GE8300) ==="

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

# Apply PVR-specific patches
for patch in /patches/pvr/*.py; do
    [ -f "$patch" ] && python3 "$patch" && echo "Applied: $(basename $patch)"
done

mkdir -p build && cd build

# Cross-compilation environment
export CCACHE_DIR="${CCACHE_DIR:-/ccache}"
export PATH="/usr/bin:${PATH}"

# Configure for PowerVR: SDL2 + GLES2, link PowerVR userspace libs directly
# SDL2 dynamically linked from /usr/trimui/lib
cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_TOOLCHAIN_FILE=/tmp/pvr-toolchain.cmake \
    -DCMAKE_C_COMPILER_LAUNCHER=ccache \
    -DCMAKE_CXX_COMPILER_LAUNCHER=ccache \
    -DCMAKE_C_FLAGS="-Wno-error" \
    -DCMAKE_CXX_FLAGS="-Wno-error" \
    -DCMAKE_EXE_LINKER_FLAGS="-static-libstdc++ -Wl,--no-as-needed -lIMGegl -lglslcompiler -lsrv_um -lusc -Wl,--as-needed" \
    -DUSING_GLES2=ON \
    -DUSING_EGL=OFF \
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
cp PPSSPPSDL "$OUTPUT_DIR/PPSSPPSDL_TrimUI"
aarch64-linux-gnu-strip "$OUTPUT_DIR/PPSSPPSDL_TrimUI"

# Copy assets (required at runtime)
cp -r ../assets "$OUTPUT_DIR/assets"

echo "=== Build complete: ${OUTPUT_DIR}/PPSSPPSDL_TrimUI ==="
