"""
Micro-Compass UI Renderer for MicroPython and GC9A01 Display (240x240)
High-performance scanline rasterization optimized for ESP32-C3 single-core execution.
"""

import math
import gc
import framebuf
from gc9a01 import color565, BLACK, WHITE, RED, GREEN, BLUE, YELLOW, ORANGE, GRAY, DARKGRAY

class CompassUI:
    """UI Drawing Helper for Micro-Compass with Off-Screen RAM Double-Buffering."""

    def __init__(self, display):
        self.display = display
        self.cx = 120  # Center X
        self.cy = 120  # Center Y
        self.radius = 114

        # Colors (Exact uint16 byte-swap mapping for MicroPython FrameBuffer on GC9A01 SPI)
        self.c_bg = BLACK
        self.c_bezel = color565(70, 80, 100)
        self.c_north = 0x00F8                # PURE RED (Byte-swapped for GC9A01 SPI so Red shows as RED!)
        self.c_south = WHITE
        self.c_text = color565(0, 215, 255)  # Gold / Yellow text
        self.c_cardinal = WHITE

        self.last_heading = -1
        self.frame_count = 0

        # Off-Screen RAM Double-Buffer (200x200 tile) for ZERO display flicker
        self.tw = 200
        self.th = 200
        self.tx = 20   # Left offset on 240x240 screen
        self.ty = 20   # Top offset on 240x240 screen
        self.tcx = 100 # Center X inside tile
        self.tcy = 100 # Center Y inside tile
        self.tradius = 96

        self.tile_buf = bytearray(self.tw * self.th * 2)
        self.fb = framebuf.FrameBuffer(self.tile_buf, self.tw, self.th, framebuf.RGB565)

    def draw_static_dial(self):
        """Draw outer static bezel ring on display background."""
        self.display.fill(self.c_bg)

        # Draw outer bezel ring (radii 114, 115, 116)
        for r in range(self.radius, self.radius + 3):
            x = r
            y = 0
            err = 0
            while x >= y:
                for px, py in (
                    (self.cx + x, self.cy + y), (self.cx - x, self.cy + y),
                    (self.cx + x, self.cy - y), (self.cx - x, self.cy - y),
                    (self.cx + y, self.cy + x), (self.cx - y, self.cy + x),
                    (self.cx + y, self.cy - x), (self.cx - y, self.cy - x)
                ):
                    if 0 <= px < 240 and 0 <= py < 240:
                        self.display.fill_rect(px, py, 1, 1, self.c_bezel)
                y += 1
                err += 1 + 2 * y
                if 2 * (err - x) + 1 > 0:
                    x -= 1
                    err += 1 - 2 * x

    def update(self, heading_deg):
        """Render frame off-screen in RAM double-buffer, then push atomically over SPI (ZERO flicker)."""
        heading_int = int(heading_deg + 0.5) % 360

        # Redraw when heading changes
        if heading_int == self.last_heading:
            return

        self.last_heading = heading_int

        # Calculate True Earth Magnetic North Direction Angle
        north_angle = -heading_deg

        # 1. Clear off-screen RAM buffer instantly
        self.fb.fill(BLACK)

        # 2. Draw rotating compass tick marks into off-screen buffer
        r_outer = self.tradius
        for deg in range(0, 360, 15):
            rad = math.radians(north_angle + deg)
            sin_a = math.sin(rad)
            cos_a = math.cos(rad)

            if deg % 90 == 0:
                length = 14
                color = self.c_cardinal
            elif deg % 45 == 0:
                length = 10
                color = GRAY
            else:
                length = 6
                color = DARKGRAY

            r_inner = r_outer - length
            x0 = int(self.tcx + r_outer * sin_a)
            y0 = int(self.tcy - r_outer * cos_a)
            x1 = int(self.tcx + r_inner * sin_a)
            y1 = int(self.tcy - r_inner * cos_a)

            self.fb.line(x0, y0, x1, y1, color)

        # 3. Draw 3x Large Rotating Cardinal Labels (N, E, S, W) - 24x24 px into off-screen buffer
        r_label = self.tradius - 30

        # North (Red)
        rad_N = math.radians(north_angle)
        nx = int(self.tcx + r_label * math.sin(rad_N) - 12)
        ny = int(self.tcy - r_label * math.cos(rad_N) - 12)
        self._draw_fb_char(nx, ny, "N", self.c_north)

        # East (White)
        rad_E = math.radians(north_angle + 90)
        ex = int(self.tcx + r_label * math.sin(rad_E) - 12)
        ey = int(self.tcy - r_label * math.cos(rad_E) - 12)
        self._draw_fb_char(ex, ey, "E", self.c_cardinal)

        # South (White)
        rad_S = math.radians(north_angle + 180)
        sx = int(self.tcx + r_label * math.sin(rad_S) - 12)
        sy = int(self.tcx - r_label * math.cos(rad_S) - 12) # Note: tcy
        sy = int(self.tcy - r_label * math.cos(rad_S) - 12)
        self._draw_fb_char(sx, sy, "S", self.c_cardinal)

        # West (White)
        rad_W = math.radians(north_angle + 270)
        wx = int(self.tcx + r_label * math.sin(rad_W) - 12)
        wy = int(self.tcy - r_label * math.cos(rad_W) - 12)
        self._draw_fb_char(wx, wy, "W", self.c_cardinal)

        # 4. Draw 3D Needle into off-screen buffer
        self._draw_fb_needle(north_angle)

        # 5. Draw central heading readout text box into off-screen buffer
        heading_str = f"{heading_int:03d} DEG"
        self._draw_fb_center_text(heading_str)

        # 6. ATOMIC SPI PUSH: Push completed off-screen frame to display in 1 transaction (ZERO flicker!)
        self.display.write_buffer(self.tx, self.ty, self.tw, self.th, self.tile_buf)

    def _draw_fb_char(self, x, y, char, color, scale=3):
        """Render 3x scaled (24x24 px) cardinal letter into off-screen FrameBuffer."""
        src_buf = bytearray(8)
        fb_src = framebuf.FrameBuffer(src_buf, 8, 8, framebuf.MONO_HLSB)
        fb_src.fill(0)
        fb_src.text(char, 0, 0, 1)

        for py in range(8):
            for px in range(8):
                if fb_src.pixel(px, py):
                    self.fb.fill_rect(x + px * scale, y + py * scale, scale, scale, color)

    def _draw_fb_needle(self, heading):
        """Draw 3D style dual-triangle compass needle into off-screen FrameBuffer."""
        rad = math.radians(heading)
        sin_a = math.sin(rad)
        cos_a = math.cos(rad)

        len_tip = 60
        len_tail = 42
        width = 9

        # North Tip (Red)
        nx = int(self.tcx + len_tip * sin_a)
        ny = int(self.tcy - len_tip * cos_a)

        # South Tip (White)
        sx = int(self.tcx - len_tail * sin_a)
        sy = int(self.tcy + len_tail * cos_a)

        # Base side points
        bx1 = int(self.tcx + width * cos_a)
        by1 = int(self.tcy + width * sin_a)
        bx2 = int(self.tcx - width * cos_a)
        by2 = int(self.tcy - width * sin_a)

        # Fill North triangle (Red)
        self._fill_fb_triangle(nx, ny, bx1, by1, bx2, by2, self.c_north)

        # Fill South triangle (White)
        self._fill_fb_triangle(sx, sy, bx1, by1, bx2, by2, self.c_south)

        # Center pin cap
        self._fill_fb_circle(self.tcx, self.tcy, 5, self.c_bezel)
        self._fill_fb_circle(self.tcx, self.tcy, 2, WHITE)

    def _fill_fb_triangle(self, x0, y0, x1, y1, x2, y2, color):
        """Rasterize filled triangle into off-screen FrameBuffer using horizontal scanlines."""
        if y0 > y1: x0, y0, x1, y1 = x1, y1, x0, y0
        if y0 > y2: x0, y0, x2, y2 = x2, y2, x0, y0
        if y1 > y2: x1, y1, x2, y2 = x2, y2, x1, y1

        total_height = y2 - y0
        if total_height == 0:
            return

        for i in range(total_height):
            second_half = i > (y1 - y0) or (y1 == y0)
            segment_height = (y2 - y1) if second_half else (y1 - y0)
            if segment_height == 0:
                continue

            alpha = i / total_height
            beta = (i - (y1 - y0 if second_half else 0)) / segment_height

            ax = int(x0 + (x2 - x0) * alpha)
            bx = int(x1 + (x2 - x1) * beta) if second_half else int(x0 + (x1 - x0) * beta)

            if ax > bx:
                ax, bx = bx, ax

            y = y0 + i
            if 0 <= y < self.th and bx >= 0 and ax < self.tw:
                x_start = max(0, ax)
                x_end = min(self.tw - 1, bx)
                self.fb.hline(x_start, y, x_end - x_start + 1, color)

    def _fill_fb_circle(self, x0, y0, r, color):
        """Draw filled circle into off-screen FrameBuffer."""
        for y in range(-r, r + 1):
            x_len = int(math.sqrt(r * r - y * y))
            self.fb.hline(x0 - x_len, y0 + y, 2 * x_len + 1, color)

    def _draw_fb_center_text(self, text):
        """Draw central boxed heading text in DOUBLE SIZE (2x scale / 16x16 px per char) into FrameBuffer."""
        scale = 2
        w_src = len(text) * 8
        h_src = 8
        box_w = w_src * scale + 16
        box_h = h_src * scale + 8
        bx = self.tcx - (box_w // 2)
        by = self.tcy + 22

        # Draw outer readout border box
        self.fb.rect(bx, by, box_w, box_h, self.c_bezel)
        self.fb.fill_rect(bx + 1, by + 1, box_w - 2, box_h - 2, BLACK)

        # Render 2x scaled text
        src_buf = bytearray(w_src * h_src // 8)
        fb_src = framebuf.FrameBuffer(src_buf, w_src, h_src, framebuf.MONO_HLSB)
        fb_src.fill(0)
        fb_src.text(text, 0, 0, 1)

        tx = self.tcx - (w_src * scale // 2)
        ty = by + 4

        for py in range(h_src):
            for px in range(w_src):
                if fb_src.pixel(px, py):
                    self.fb.fill_rect(tx + px * scale, ty + py * scale, scale, scale, self.c_text)

    def _draw_center_text(self, text):
        """Draw central boxed text showing current degree readout."""
        box_w = 90
        box_h = 20
        bx = self.cx - (box_w // 2)
        by = self.cy + 35

        tx = (box_w - len(text) * 8) // 2
        buf = bytearray(box_w * box_h * 2)
        fb = framebuf.FrameBuffer(buf, box_w, box_h, framebuf.RGB565)
        fb.fill(DARKGRAY)
        fb.rect(0, 0, box_w, box_h, WHITE)
        fb.text(text, tx, 6, self.c_text)
        self.display.write_buffer(bx, by, box_w, box_h, buf)

    def draw_error_screen(self, title, lines):
        """Display initialization error message."""
        self.display.fill(BLACK)

        self._draw_string(self.cx - (len(title) * 4), 40, title, RED)
        self.display.draw_line(20, 56, 220, 56, RED)

        start_y = 75
        spacing = 22
        for i, line in enumerate(lines):
            tx = self.cx - (len(line) * 4)
            self._draw_string(tx, start_y + (i * spacing), line, WHITE)

    # Optimized Fast Raster Primitives
    def _draw_rect(self, x, y, w, h, color):
        self.display.fill_rect(x, y, w, 1, color)
        self.display.fill_rect(x, y + h - 1, w, 1, color)
        self.display.fill_rect(x, y, 1, h, color)
        self.display.fill_rect(x + w - 1, y, 1, h, color)

    def _draw_circle(self, x0, y0, r, color):
        x = r
        y = 0
        err = 0

        while x >= y:
            for px, py in (
                (x0 + x, y0 + y), (x0 + y, y0 + x),
                (x0 - y, y0 + x), (x0 - x, y0 + y),
                (x0 - x, y0 - y), (x0 - y, y0 - x),
                (x0 + y, y0 - x), (x0 + x, y0 - y)
            ):
                if 0 <= px < 240 and 0 <= py < 240:
                    self.display.fill_rect(px, py, 1, 1, color)
            y += 1
            err += 1 + 2 * y
            if 2 * (err - x) + 1 > 0:
                x -= 1
                err += 1 - 2 * x

    def _fill_circle(self, x0, y0, r, color):
        for y in range(-r, r + 1):
            dx = int(math.sqrt(r * r - y * y))
            px = x0 - dx
            py = y0 + y
            w = 2 * dx + 1
            if 0 <= py < 240:
                x1 = max(0, px)
                x2 = min(239, px + w - 1)
                if x2 >= x1:
                    self.display.fill_rect(x1, py, x2 - x1 + 1, 1, color)

    def _fill_triangle(self, x0, y0, x1, y1, x2, y2, color):
        """Fast scanline triangle rasterizer (horizontal fill_rect lines)."""
        pts = [(x0, y0), (x1, y1), (x2, y2)]
        pts.sort(key=lambda p: p[1])
        (x0, y0), (x1, y1), (x2, y2) = pts

        if y0 == y2:
            return

        total_height = y2 - y0
        for i in range(total_height + 1):
            second_half = i > (y1 - y0) or y1 == y0
            segment_height = (y2 - y1) if second_half else (y1 - y0)
            if segment_height == 0:
                continue

            alpha = i / total_height
            beta = (i - (y1 - y0 if second_half else 0)) / segment_height

            ax = int(x0 + (x2 - x0) * alpha)
            bx = int(x1 + (x2 - x1) * beta) if second_half else int(x0 + (x1 - x0) * beta)

            if ax > bx:
                ax, bx = bx, ax

            ax = max(0, min(239, ax))
            bx = max(0, min(239, bx))
            cy = y0 + i
            if 0 <= cy < 240 and bx >= ax:
                self.display.fill_rect(ax, cy, bx - ax + 1, 1, color)

    def _draw_string(self, x, y, text, color, bg=BLACK):
        """Crisp, high-speed 16-bit RGB565 text renderer."""
        w = len(text) * 8
        h = 8
        buf = bytearray(w * h * 2)
        fb = framebuf.FrameBuffer(buf, w, h, framebuf.RGB565)
        fb.fill(bg)
        fb.text(text, 0, 0, color)
        self.display.write_buffer(x, y, w, h, buf)
