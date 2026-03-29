#!/bin/bash
set -e

PPSSPP_VERSION="${PPSSPP_VERSION:-v1.20.3}"
OUTPUT_DIR="${OUTPUT_DIR:-/output}"

echo "=== Building PPSSPP ${PPSSPP_VERSION} for A30 (armhf / Mali fbdev) ==="

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

# Apply A30-specific patches
for patch in /patches/a30/*.py; do
    [ -f "$patch" ] && python3 "$patch" && echo "Applied: $(basename $patch)"
done

mkdir -p build && cd build

# Cross-compilation environment
export CCACHE_DIR="${CCACHE_DIR:-/ccache}"
export PATH="/opt/a30/bin:${PATH}"
SYSROOT=/opt/a30/arm-a30-linux-gnueabihf/sysroot

# Build fcntl64 compat shim — pre-built ffmpeg needs fcntl64 (glibc 2.28+)
# but A30 sysroot has glibc 2.23
cat > /tmp/fcntl64_compat.c << 'EOFC'
#include <stdarg.h>
#include <fcntl.h>
int fcntl64(int fd, int cmd, ...) {
    va_list ap;
    va_start(ap, cmd);
    void *arg = va_arg(ap, void *);
    va_end(ap);
    return fcntl(fd, cmd, arg);
}
EOFC
arm-a30-linux-gnueabihf-gcc -c /tmp/fcntl64_compat.c -o /tmp/fcntl64_compat.o \
    -march=armv7-a -mfpu=neon-vfpv4 -mfloat-abi=hard
arm-a30-linux-gnueabihf-ar rcs /tmp/libfcntl64_compat.a /tmp/fcntl64_compat.o

# Configure for A30: SDL2 + GLES2, Mali fbdev, NEON
cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_TOOLCHAIN_FILE=/tmp/a30-toolchain.cmake \
    -DCMAKE_C_COMPILER_LAUNCHER=ccache \
    -DCMAKE_CXX_COMPILER_LAUNCHER=ccache \
    -DCMAKE_C_FLAGS="-Ofast -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -ffunction-sections -fdata-sections -fomit-frame-pointer -flto -Wno-error -DHWCAP2_AES=1 -DHWCAP2_SHA1=4 -DHWCAP2_SHA2=8 -DHWCAP2_CRC32=16" \
    -DCMAKE_CXX_FLAGS="-Ofast -mcpu=cortex-a7 -mfpu=neon-vfpv4 -mfloat-abi=hard -ffunction-sections -fdata-sections -fomit-frame-pointer -flto -Wno-error" \
    -DCMAKE_EXE_LINKER_FLAGS="-Wl,--gc-sections -static-libstdc++ -L/tmp -Wl,--whole-archive -lfcntl64_compat -Wl,--no-whole-archive" \
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
    -DCMAKE_DISABLE_FIND_PACKAGE_X11=ON \
    -DARM=ON \
    -DARMV7=ON \
    -DUSING_ARM_NEON=ON

# Fix cross-compile: -isystem paths get sysroot-prepended by GCC, breaking includes
find . \( -name 'flags.make' -o -name 'build.ninja' \) -exec sed -i 's|-isystem |-I|g' {} +

# Build
make -j$(nproc) PPSSPPSDL

# Output
mkdir -p "$OUTPUT_DIR"
cp PPSSPPSDL "$OUTPUT_DIR/PPSSPPSDL_A30"
/opt/a30/bin/arm-a30-linux-gnueabihf-strip -s "$OUTPUT_DIR/PPSSPPSDL_A30"

# Copy assets (required at runtime)
cp -r ../assets "$OUTPUT_DIR/assets"

echo "=== Build complete: ${OUTPUT_DIR}/PPSSPPSDL_A30 ==="
