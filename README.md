# PPSSPP-spruce



CI-built PPSSPP binaries for [SpruceOS](https://github.com/spruceUI/spruceOS), targeting per-device vendor toolchains for maximum performance on handheld devices.

## Builds

| Binary | Devices | SoC / GPU | Toolchain |
|--------|---------|-----------|-----------|
| `PPSSPPSDL.64` | Universal ARM64 | aarch64 | Ubuntu Focal GCC 9.4 | 
| `PPSSPPSDL_TrimUI` | Brick, SmartPro (TSP) | A133 / PowerVR GE8300 | Ubuntu Focal GCC 9.4 + SmartPro SDK |
| `PPSSPPSDL_SmartProS` | SmartPro S (TSPS) | A523 / Mali G57 | Buildroot GCC 10.3 |
| `PPSSPPSDL_Flip` | Flip | RK3566 / Mali G52 | Steward-Fu GCC 13.3 |
| `PPSSPPSDL_Pixel2` | GKD Pixel 2 | RK3326 / Mali G31 | Ubuntu Noble Clang 18 |
| `PPSSPPSDL_A30` | Miyoo A30 | A33 / Mali 400 | Steward-Fu GCC 13.2 |

All builds are triggered via **GitHub Actions > workflow_dispatch**. Binaries are uploaded to the [`latest` release](https://github.com/spruceUI/PPSSPP-spruce/releases/tag/latest).

## Patches

Patches in `patches/common/` are applied to all builds. Device-specific patches go in `patches/<device>/`.

### Common patches

| Patch | What it does |
|-------|-------------|
| `fullscreen.py` | `SDL_WINDOW_FULLSCREEN_DESKTOP` → `SDL_WINDOW_FULLSCREEN` (required for DRM/KMS) |
| `hide-cursor.py` | Unconditionally hide mouse cursor |
| `no-mute-secondary.py` | Remove auto-mute when PPSSPP_ID > 1 |

### Assets path

Assets (fonts, UI images, flash0 firmware files) are found **relative to the binary** at `<binary_dir>/assets/`. This is not patched — it uses PPSSPP's built-in exe-relative discovery via `/proc/self/exe`. No changes needed as long as the `assets/` folder sits next to the binary.

## Vendor SDK tarballs

The PVR and TSPS builds require proprietary vendor SDKs stored in the [`sdk-toolchains` release](https://github.com/spruceUI/PPSSPP-spruce/releases/tag/sdk-toolchains). Flip and A30 toolchains are public and downloaded automatically during Docker build.

## PPSSPP version

All builds currently target **v1.20.3**. To change, pass `ppsspp_version` when triggering the workflow (e.g., `v1.21.0`).
