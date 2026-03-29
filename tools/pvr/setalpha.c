/*
 * setalpha - Set Allwinner DE2 display layer alpha mode
 *
 * Usage: setalpha <0|1>
 *   0 = opaque  (global alpha, alpha_value=255)
 *   1 = transparent (pixel alpha)
 *
 * Opens /dev/disp and uses DISP_LAYER_GET_CONFIG / DISP_LAYER_SET_CONFIG
 * ioctls to change the UI layer's alpha mode. This prevents a blank screen
 * on PowerVR GE8300 devices where EGL selects RGBA8888 and the display
 * engine defaults to per-pixel alpha.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/ioctl.h>

/* Allwinner DE2 ioctl commands from sunxi_display2.h */
#define DISP_LAYER_SET_CONFIG 0x47
#define DISP_LAYER_GET_CONFIG 0x48

/* Alpha modes */
#define ALPHA_MODE_PIXEL        0
#define ALPHA_MODE_GLOBAL       1
#define ALPHA_MODE_GLOBAL_PIXEL 2

/*
 * Minimal struct definitions matching the kernel's disp_layer_config.
 * We only need to reach the alpha_mode and alpha_value fields in
 * disp_layer_info, but must match the full layout so the kernel
 * copies the right bytes.
 *
 * These are from sunxi_display2.h for the DE2 display engine.
 */

typedef struct { int x; int y; unsigned int width; unsigned int height; } disp_rect;
typedef struct { long long x; long long y; long long width; long long height; } disp_rect64;
typedef struct { unsigned int width; unsigned int height; } disp_rectsz;

typedef struct {
    unsigned long long addr[3];
    disp_rectsz        size[3];
    unsigned int       align[3];
    unsigned int       format;        /* disp_pixel_format */
    unsigned int       color_space;   /* disp_color_space */
    unsigned int       trd_right_addr[3];
    int                pre_multiply;  /* bool */
    disp_rect64        crop;
    unsigned int       flags;         /* disp_buffer_flags */
    unsigned int       scan;          /* disp_scan_flags */
} disp_fb_info;

typedef struct {
    unsigned int       mode;          /* disp_layer_mode: 0=buffer, 1=color */
    unsigned char      zorder;
    unsigned char      alpha_mode;    /* 0=pixel, 1=global, 2=global_pixel */
    unsigned char      alpha_value;   /* 0-255 */
    disp_rect          screen_win;
    int                b_trd_out;     /* bool */
    unsigned int       out_trd_mode;  /* disp_3d_out_mode */
    union {
        unsigned int   color;
        disp_fb_info   fb;
    };
    unsigned int       id;
} disp_layer_info;

typedef struct {
    disp_layer_info    info;
    int                enable;        /* bool */
    unsigned int       channel;
    unsigned int       layer_id;
} disp_layer_config;

int main(int argc, char *argv[])
{
    if (argc != 2 || (argv[1][0] != '0' && argv[1][0] != '1')) {
        fprintf(stderr, "Usage: %s <0|1>\n", argv[0]);
        fprintf(stderr, "  0 = opaque (global alpha)\n");
        fprintf(stderr, "  1 = transparent (pixel alpha)\n");
        return 1;
    }

    int opaque = (argv[1][0] == '0');

    int fd = open("/dev/disp", O_RDWR);
    if (fd < 0) {
        perror("open /dev/disp");
        return 1;
    }

    /* UI framebuffer layer: channel 1, layer_id 0 on A133 TrimUI devices */
    disp_layer_config config;
    memset(&config, 0, sizeof(config));
    config.channel = 1;
    config.layer_id = 0;

    /* args: screen=0, config_ptr, count=1, unused=0 */
    unsigned long args[4] = { 0, (unsigned long)&config, 1, 0 };

    if (ioctl(fd, DISP_LAYER_GET_CONFIG, args) < 0) {
        perror("ioctl DISP_LAYER_GET_CONFIG");
        close(fd);
        return 1;
    }

    if (opaque) {
        config.info.alpha_mode = ALPHA_MODE_GLOBAL;
        config.info.alpha_value = 255;
    } else {
        config.info.alpha_mode = ALPHA_MODE_PIXEL;
    }

    if (ioctl(fd, DISP_LAYER_SET_CONFIG, args) < 0) {
        perror("ioctl DISP_LAYER_SET_CONFIG");
        close(fd);
        return 1;
    }

    close(fd);
    return 0;
}
