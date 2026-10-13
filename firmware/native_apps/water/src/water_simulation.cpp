// SPDX-License-Identifier: MIT
// Particle solver, span painter and boat adapted from locked The-Badge app_water.c.
#include "espocket/water_simulation.hpp"
#include <algorithm>
#include <bit>
#include <cmath>
#include <cstring>
#include <new>
#ifdef ESP_PLATFORM
#include "esp_heap_caps.h"
#endif
namespace espocket::water {
namespace {
constexpr int CX = center, CY = center, R = bowl_radius, NP = particle_count;
constexpr float DEG2RAD = 0.0174533f, HR = 22.0f, INV_HR = 1 / HR, HR2 = HR * HR;
constexpr int GC = 24, NB_MAX = 128, COLW = 6, ROWH = 6, NCOL = 78, NROW = 78, SPANS = 6;
constexpr float INV_GS = GC / 466.0f, INV_COLW = 1.0f / COLW, INV_ROWH = 1.0f / ROWH;
constexpr float KSTIFF = 26000, KNEAR = 78000, THRESH = 3;
constexpr float BOAT_G = 1900, BOAT_LIFT = 12, BOAT_SUB_MAX = 26;
float frsqrt(float x)
{
    float y = std::bit_cast<float>(0x5f3759dfu - (std::bit_cast<uint32_t>(x) >> 1));
    const float h = 0.5f * x;
    y *= 1.5f - h * y * y;
    return y * (1.5f - h * y * y);
}
void clamp_circle(float *x, float *y)
{
    const float dx = *x - CX, dy = *y - CY, d2 = dx * dx + dy * dy;
    if (d2 > (R - 2) * (R - 2)) {
        const float k = (R - 2) * frsqrt(d2);
        *x = CX + dx * k; *y = CY + dy * k;
    }
}
uint16_t rgb565(int r, int g, int b) { return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3); }
template <class T> T *allocate()
{
#ifdef ESP_PLATFORM
    auto *memory = heap_caps_malloc(sizeof(T), MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
    return memory ? new (memory) T{} : nullptr;
#else
    return new (std::nothrow) T{};
#endif
}
template <class T> void release(T *p)
{
#ifdef ESP_PLATFORM
    if (p) { p->~T(); heap_caps_free(p); }
#else
    delete p;
#endif
}
}
Frame::Frame() { previous_top.fill(1); }
std::shared_ptr<Frame> Frame::create() { return {allocate<Frame>(), [](Frame *p) { release(p); }}; }
struct Simulation::State {
    float x_[NP]{}, y_[NP]{}, px_[NP]{}, py_[NP]{}, vx_[NP]{}, vy_[NP]{};
    uint16_t head_[GC * GC]{}, next_[NP]{}, nb_j[NB_MAX]{};
    float nb_q[NB_MAX]{}, nb_ux[NB_MAX]{}, nb_uy[NB_MAX]{};
    uint8_t dens_[NROW][NCOL]{}, chur_[NROW][NCOL]{}, spn_[466]{}, sfrac_[466]{}, foam_[466]{};
    int8_t slope_[466]{};
    int16_t sp0_[466][SPANS]{}, sp1_[466][SPANS]{};
    uint16_t scol_[466 * 3]{}, depth_lut_[201]{};
    float rho0_ = 3, boat_x_ = CX, boat_y_ = CY - 20, boat_vx_ = 0, boat_vy_ = 0;
    float gux_ = 0, guy_ = 1, boat_angle_ = 0;
    bool boat_first_ = true, neighbor_overflow_ = false;
    Frame *frame_ = nullptr;
    float along(float x, float y) const { return (x - CX) * gux_ + (y - CY) * guy_; }
    float cross(float x, float y) const { return (x - CX) * guy_ - (y - CY) * gux_; }
    // Initialize the locked staggered arrangement, then measure its rest density.
    void initialize()
    {
        int n = 0;
        for (int row = 0; row < 44 && n < NP; row++) {
            float y = CY - 14 + row * 10.2f;
            for (int col = -23; col <= 23 && n < NP; col++) {
                float x = CX + col * 10.2f + (row & 1 ? 5.1f : 0);
                float dx = x - CX, dy = y - CY;
                if (dx * dx + dy * dy > (float)(R - 8) * (R - 8)) continue;
                x_[n] = x; y_[n] = y;
                vx_[n] = vy_[n] = 0;
                n++;
            }
        }
        for (; n < NP; n++) { x_[n] = CX; y_[n] = CY + 120; vx_[n] = vy_[n] = 0; }

        grid_build_from_current();
        float sum = 0; int cnt = 0;
        for (int i = 0; i < NP; i++) {
            float dx = x_[i] - CX, dy = y_[i] - CY;
            if (dx * dx + dy * dy > (float)(R - 40) * (R - 40)) continue;
            float rho = 0;
            for (int j = 0; j < NP; j++) {
                if (j == i) continue;
                float ex = x_[j] - x_[i], ey = y_[j] - y_[i];
                float r2 = ex * ex + ey * ey;
                if (r2 >= HR2 || r2 < 1e-4f) continue;
                float q = 1.0f - sqrtf(r2) / HR;
                rho += q * q;
            }
            sum += rho; cnt++;
        }
        rho0_ = cnt ? sum / cnt : 3.0f;

        boat_x_ = CX; boat_y_ = CY - 20;
        depth_lut_build();
    }
    void grid_build_from_current(void)
    {
        memset(head_, 0xFF, sizeof head_);
        for (int i = 0; i < NP; i++) {
            int cx = (int)(x_[i] * INV_GS), cy = (int)(y_[i] * INV_GS);
            if (cx < 0) cx = 0;
            if (cx >= GC) cx = GC - 1;
            if (cy < 0) cy = 0;
            if (cy >= GC) cy = GC - 1;
            int c = cy * GC + cx;
            next_[i] = head_[c];
            head_[c] = (uint16_t)i;
        }
    }

    // Clavet double density relaxation; neighbor scratch belongs to this instance.
    void neighbors_relax(float dt)
    {

        float dt2 = dt * dt;
        for (int i = 0; i < NP; i++) {
            float rho = 0, rhon = 0;
            int cx = (int)(x_[i] * INV_GS), cy = (int)(y_[i] * INV_GS);
            int nb = 0;

            for (int oy = -1; oy <= 1; oy++) {
                int yy = cy + oy;
                if (yy < 0 || yy >= GC) continue;
                for (int ox = -1; ox <= 1; ox++) {
                    int xx = cx + ox;
                    if (xx < 0 || xx >= GC) continue;
                    for (uint16_t j = head_[yy * GC + xx]; j != 0xFFFF; j = next_[j]) {
                        if (j == i) continue;
                        float dx = x_[j] - x_[i], dy = y_[j] - y_[i];
                        float r2 = dx * dx + dy * dy;
                        if (r2 >= HR2 || r2 < 1e-4f) continue;

                        float inv_r = frsqrt(r2);
                        float r = r2 * inv_r;
                        float q = 1.0f - r * INV_HR;
                        rho  += q * q;
                        rhon += q * q * q;
                        if (nb < NB_MAX) {
                            nb_j[nb]  = j;
                            nb_q[nb]  = q;
                            nb_ux[nb] = dx * inv_r;
                            nb_uy[nb] = dy * inv_r;
                            nb++;
                        } else {

                            neighbor_overflow_ = true;
                        }
                    }
                }
            }

            float P  = KSTIFF * (rho - rho0_);
            float PN = KNEAR  * rhon;
            float dxi = 0, dyi = 0;
            for (int k = 0; k < nb; k++) {
                float q = nb_q[k];
                float d = dt2 * (P * q + PN * q * q) * 0.5f;
                float ux = nb_ux[k], uy = nb_uy[k];
                uint16_t j = nb_j[k];
                x_[j] += ux * d;  y_[j] += uy * d;
                dxi    -= ux * d;  dyi    -= uy * d;
            }
            x_[i] += dxi; y_[i] += dyi;
        }
    }

    // Viscosity, gravity, density correction, bowl confinement and velocity recovery.
    void fluid_step(float dt, float gx, float gy)
    {

        grid_build_from_current();
        for (int i = 0; i < NP; i++) {
            int cx = (int)(x_[i] * INV_GS), cy = (int)(y_[i] * INV_GS);
            for (int oy = -1; oy <= 1; oy++) {
                int yy = cy + oy;
                if (yy < 0 || yy >= GC) continue;
                for (int ox = -1; ox <= 1; ox++) {
                    int xx = cx + ox;
                    if (xx < 0 || xx >= GC) continue;
                    for (uint16_t j = head_[yy * GC + xx]; j != 0xFFFF; j = next_[j]) {
                        if (j <= i) continue;
                        float dx = x_[j] - x_[i], dy = y_[j] - y_[i];
                        float r2 = dx * dx + dy * dy;
                        if (r2 >= HR2 || r2 < 1e-4f) continue;
                        float inv_r = frsqrt(r2);
                        float ux = dx * inv_r, uy = dy * inv_r;
                        float vr = (vx_[i] - vx_[j]) * ux + (vy_[i] - vy_[j]) * uy;
                        if (vr <= 0) continue;
                        float q = 1.0f - (r2 * inv_r) * INV_HR;

                        float imp = dt * q * (0.55f * vr) * 0.5f;
                        vx_[i] -= ux * imp; vy_[i] -= uy * imp;
                        vx_[j] += ux * imp; vy_[j] += uy * imp;
                    }
                }
            }
        }

        for (int i = 0; i < NP; i++) {
            vx_[i] += gx * dt;
            vy_[i] += gy * dt;
            px_[i] = x_[i];
            py_[i] = y_[i];
            x_[i] += vx_[i] * dt;
            y_[i] += vy_[i] * dt;
        }

        grid_build_from_current();
        neighbors_relax(dt);

        float inv = 1.0f / dt;
        for (int i = 0; i < NP; i++) {
            clamp_circle(&x_[i], &y_[i]);
            vx_[i] = (x_[i] - px_[i]) * inv;
            vy_[i] = (y_[i] - py_[i]) * inv;
            float sp2 = vx_[i] * vx_[i] + vy_[i] * vy_[i];

            if (sp2 > 1300.0f * 1300.0f) {
                float k = 1300.0f * frsqrt(sp2);
                vx_[i] *= k; vy_[i] *= k;
            }
        }
    }

    void depth_lut_build(void)
    {
        for (int d = 0; d <= 200; d++) {
            float t = d / 200.0f;
            depth_lut_[d] = rgb565((int)(0x6E + (0x0A - 0x6E) * t),
                                    (int)(0xC4 + (0x30 - 0xC4) * t),
                                    (int)(0xE8 + (0x58 - 0xE8) * t));
        }
    }

    float dens_at(float fx, int r)
    {
        if (r < 0 || r >= NROW) return 0;
        float c = fx * INV_COLW;
        int   ci = (int)c;
        float t = c - ci;
        if (ci < 0) { ci = 0; t = 0; }
        if (ci >= NCOL - 1) { ci = NCOL - 2; t = 1; }
        return dens_[r][ci] * (1 - t) + dens_[r][ci + 1] * t;
    }

    // Density and churn form connected runs, including detached droplets.
    void build_spans()
    {
        memset(dens_, 0, (size_t)NROW * NCOL);
        memset(chur_, 0, (size_t)NROW * NCOL);
        for (int i = 0; i < NP; i++) {
            int c = (int)(x_[i] * INV_COLW), r = (int)(y_[i] * INV_ROWH);

            float sp = fabsf(vx_[i]) + fabsf(vy_[i]);
            int ch = (int)(sp * 0.35f);
            if (ch > 60) ch = 60;
            for (int dr = -2; dr <= 2; dr++) {
                int rr = r + dr;
                if (rr < 0 || rr >= NROW) continue;
                for (int dc = -2; dc <= 2; dc++) {
                    int cc = c + dc;
                    if (cc < 0 || cc >= NCOL) continue;
                    int w = 5 - (dr * dr + dc * dc);
                    if (w <= 0) continue;
                    int v = dens_[rr][cc] + w;
                    dens_[rr][cc] = v > 255 ? 255 : (uint8_t)v;
                    int u = chur_[rr][cc] + ((ch * w) >> 2);
                    chur_[rr][cc] = u > 255 ? 255 : (uint8_t)u;
                }
            }
        }
        for (int x = 0; x < 466; x++) {
            int n = 0;
            float prev = dens_at(x, 0);
            int   topr = -1; float topf = 0;

            for (int r = 1; r < NROW; r++) {
                float d = dens_at(x, r);
                bool was = prev >= THRESH, now = d >= THRESH;
                if (!was && now) {
                    float f = (THRESH - prev) / (d - prev + 1e-6f);
                    topr = r - 1; topf = f;
                    if (n == 0) {

                        float yf = (topr + topf) * ROWH;
                        sfrac_[x] = (uint8_t)((1.0f - (yf - floorf(yf))) * 255.0f);
                    }
                } else if (was && !now && topr >= 0) {
                    float f = (prev - THRESH) / (prev - d + 1e-6f);
                    int16_t y0 = (int16_t)std::clamp((int)((topr + topf) * ROWH), 0, 465);
                    int16_t y1 = (int16_t)std::clamp((int)((r - 1 + f) * ROWH), 0, 465);
                    if (y1 > y0) {
                        if (n < SPANS) { sp0_[x][n] = y0; sp1_[x][n] = y1; n++; }
                        else           { sp1_[x][SPANS - 1] = y1; }
                    }
                    topr = -1;
                }
                prev = d;
            }
            if (topr >= 0) {
                if (n < SPANS) {
                    sp0_[x][n] = (int16_t)((topr + topf) * ROWH);
                    sp1_[x][n] = 465;
                    n++;
                } else {
                    sp1_[x][SPANS - 1] = 465;
                }
            }
            spn_[x] = (uint8_t)n;

            int fr = 0;
            if (n) {
                int rr = sp0_[x][0] / ROWH;
                if (rr >= 0 && rr < NROW) {
                    int cc = x / COLW;
                    if (cc >= NCOL) cc = NCOL - 1;
                    fr = chur_[rr][cc];
                }
            }
            foam_[x] = (uint8_t)fr;
        }

        for (int x = 0; x < 466; x++) {
            int a = x > 3 ? x - 4 : 0, b = x < 462 ? x + 4 : 465;
            if (!spn_[a] || !spn_[b]) { slope_[x] = 0; continue; }
            int d = (sp0_[b][0] - sp0_[a][0]) * 8 / (b - a);
            if (d > 127) d = 127;
            if (d < -127) d = -127;
            slope_[x] = (int8_t)d;
        }
    }

    void fill_tri(float x0, float y0, float x1, float y1,
                         float x2, float y2, uint16_t c)
    {
        int ymin = (int)floorf(fminf(y0, fminf(y1, y2)));
        int ymax = (int)ceilf (fmaxf(y0, fmaxf(y1, y2)));
        if (ymin < 0) ymin = 0;
        if (ymax > 465) ymax = 465;
        for (int y = ymin; y <= ymax; y++) {
            float yc = y + 0.5f;

            float xs[3]; int nx = 0;
            float px[3] = { x0, x1, x2 }, py[3] = { y0, y1, y2 };
            for (int e = 0; e < 3; e++) {
                int f = (e + 1) % 3;
                float ya = py[e], yb = py[f];
                if ((yc >= ya && yc < yb) || (yc >= yb && yc < ya)) {
                    float t = (yc - ya) / (yb - ya);
                    xs[nx++] = px[e] + (px[f] - px[e]) * t;
                }
            }
            if (nx < 2) continue;
            float xa = xs[0], xb = xs[1];
            if (xa > xb) { float t = xa; xa = xb; xb = t; }
            int ia = (int)ceilf(xa - 0.5f), ib = (int)floorf(xb - 0.5f);
            if (ia < 0) ia = 0;
            if (ib > 465) ib = 465;
            uint16_t *row = frame_->pixels.data() + (size_t)y * 466;
            for (int x = ia; x <= ib; x++) row[x] = c;
        }
    }

    void paint_boat(int *out_x0, int *out_x1, int *out_y0, int *out_y1)
    {
        float bx = boat_x_, by = boat_y_;
        float bdeg = 0;
        {
            float lft = 0, rgt = 0; int nl = 0, nr = 0;
            for (int i = 0; i < NP; i++) {
                float d = x_[i] - bx;
                if (fabsf(d) > 40 || y_[i] > by + 40) continue;
                if (d < 0) { lft += y_[i]; nl++; } else { rgt += y_[i]; nr++; }
            }
            if (nl && nr) bdeg = atanf(((rgt / nr) - (lft / nl)) / 40.0f) / DEG2RAD * 0.6f;
        }

        bdeg -= atan2f(gux_, guy_) / DEG2RAD;

        {

            if (boat_first_) { boat_angle_ = bdeg; boat_first_ = false; }
            float d = bdeg - boat_angle_;
            while (d >  180.0f) d -= 360.0f;
            while (d < -180.0f) d += 360.0f;
            boat_angle_ += d * 0.11f;
            bdeg = boat_angle_;
        }
        float bc = cosf(bdeg * DEG2RAD), bs = sinf(bdeg * DEG2RAD);

        int lo = 465, hi = 0, xlo = 465, xhi = 0;
        const auto triangle = [&](uint16_t color, float ax, float ay, float bx_, float by_, float cx, float cy) {
            const auto transform_x = [&](float x, float y) { return bx + x * bc - y * bs; };
            const auto transform_y = [&](float x, float y) { return by + x * bs + y * bc; };
            const float x0 = transform_x(ax, ay), y0 = transform_y(ax, ay);
            const float x1 = transform_x(bx_, by_), y1 = transform_y(bx_, by_);
            const float x2 = transform_x(cx, cy), y2 = transform_y(cx, cy);
            fill_tri(x0, y0, x1, y1, x2, y2, color);
            lo = std::min(lo, (int)std::min({y0, y1, y2}));
            hi = std::max(hi, (int)std::max({y0, y1, y2}) + 1);
            xlo = std::min(xlo, (int)std::min({x0, x1, x2}));
            xhi = std::max(xhi, (int)std::max({x0, x1, x2}) + 1);
        };
        const uint16_t HULL  = rgb565(0xB0, 0x70, 0x3C), HULL2 = rgb565(0xE0, 0xA4, 0x68);
        const uint16_t SAIL  = rgb565(0xFF, 0xFD, 0xF6), SAIL2 = rgb565(0xE8, 0xDC, 0xC4);
        const uint16_t FLAG  = rgb565(0xFF, 0xE0, 0x8A);
        triangle(HULL,  -30,-7,  -14,-11, -16, 6);
        triangle(HULL,  -14,-11,  10,-11, -16, 6);
        triangle(HULL,   10,-11,  14,  6, -16, 6);
        triangle(HULL,   10,-11,  33, -9,  14, 6);
        triangle(HULL2, -30,-7,   33, -9, -14,-11);
        triangle(HULL2,  -2,-52,   1,-52,   3,-11);
        triangle(HULL2,   1,-52,   3,-11,   0,-11);
        triangle(SAIL,    3,-50,  22,-24,   3,-13);
        triangle(SAIL,   22,-24,  26,-15,   3,-13);
        triangle(SAIL2,   3,-50,   9,-31,   3,-13);
        triangle(SAIL2,  -2,-46, -19,-13,  -2,-13);
        triangle(FLAG,   -6,-14,  -3,-14,  -4,-18);
        if (lo < 0) lo = 0;
        if (hi > 465) hi = 465;
        if (xlo < 0) xlo = 0;
        if (xhi > 465) xhi = 465;
        *out_x0 = xlo;  *out_x1 = xhi;
        *out_y0 = lo;
        *out_y1 = hi;
    }

    // Each image slot retains its own clearing history; pixels are written in 64-row bands.
    void paint_img()
    {

        int ny0 = 465, ny1 = 0;

        if (frame_->boat_x0 <= frame_->boat_x1 && frame_->boat_y0 <= frame_->boat_y1) {
            size_t w = (size_t)(frame_->boat_x1 - frame_->boat_x0 + 1) * 2;
            for (int y = frame_->boat_y0; y <= frame_->boat_y1; y++)
                memset(frame_->pixels.data() + (size_t)y * 466 + frame_->boat_x0, 0, w);
            if (frame_->boat_y0 < ny0) ny0 = frame_->boat_y0;
            if (frame_->boat_y1 > ny1) ny1 = frame_->boat_y1;
        }

        for (int x = 0; x < 466; x++) {
            int p0 = frame_->previous_top.data()[x], p1 = frame_->previous_bottom.data()[x];
            int nsp = spn_[x];
            int n0 = nsp ? sp0_[x][0] : 1, n1 = nsp ? sp1_[x][nsp - 1] : 0;
            if (p0 <= p1) {
                int a1 = p1 < n0 - 1 ? p1 : n0 - 1;
                for (int y = p0; y <= a1; y++) frame_->pixels.data()[(size_t)y * 466 + x] = 0;
                int b0 = p0 > n1 + 1 ? p0 : n1 + 1;
                for (int y = b0; y <= p1; y++) frame_->pixels.data()[(size_t)y * 466 + x] = 0;
                if (p0 < ny0) ny0 = p0;
                if (p1 > ny1) ny1 = p1;
            }

            for (int k = 1; k < nsp; k++) {
                int g0 = sp1_[x][k - 1] + 1, g1 = sp0_[x][k] - 1;
                for (int y = g0; y <= g1; y++) frame_->pixels.data()[(size_t)y * 466 + x] = 0;
            }
            frame_->previous_top.data()[x] = (int16_t)n0;
            frame_->previous_bottom.data()[x] = (int16_t)n1;
        }

        {
            int b0, b1;
            int bxa, bxb;
            paint_boat(&bxa, &bxb, &b0, &b1);
            if (b0 < ny0) ny0 = b0;
            if (b1 > ny1) ny1 = b1;
            frame_->boat_x0 = bxa; frame_->boat_x1 = bxb; frame_->boat_y0 = b0; frame_->boat_y1 = b1;
        }

        int wy0 = 465, wy1 = 0;
        for (int x = 0; x < 466; x++) {
            int nsp = spn_[x];
            if (!nsp) continue;
            int s0 = sp0_[x][0];
            if (s0 < wy0) wy0 = s0;
            int last = sp1_[x][nsp - 1];
            if (last > wy1) wy1 = last;

            int sl = slope_[x];
            int lit = 128 - sl * 2;
            if (lit < 40) lit = 40;
            if (lit > 255) lit = 255;
            int fo = foam_[x];
            for (int q = 0; q < 3; q++) {
                int br = (0x9A * lit) >> 8, bg = (0xD6 * lit) >> 8, bb2 = (0xF2 * lit) >> 8;
                if (q) { br = br * 3 / 4; bg = bg * 3 / 4; bb2 = bb2 * 3 / 4; }
                if (fo) {
                    int f = fo > 200 ? 200 : fo;
                    br += (255 - br) * f / 255;
                    bg += (255 - bg) * f / 255;
                    bb2 += (255 - bb2) * f / 255;
                }
                if (q == 0) {
                    int cov = sfrac_[x];
                    br = br * cov / 255; bg = bg * cov / 255; bb2 = bb2 * cov / 255;
                }
                if (br > 255) br = 255;
                if (bg > 255) bg = 255;
                if (bb2 > 255) bb2 = 255;
                scol_[x * 3 + q] = rgb565(br, bg, bb2);
            }
        }
        if (wy0 < 0) wy0 = 0;
        if (wy1 > 465) wy1 = 465;

        constexpr int BANDH = 64;
        for (int b0 = wy0; b0 <= wy1; b0 += BANDH) {
            int b1 = b0 + BANDH - 1;
            if (b1 > wy1) b1 = wy1;
            for (int x = 0; x < 466; x++) {
                int nsp = spn_[x];
                if (!nsp) continue;

                int above = 0;
                for (int k = 0; k < nsp; k++) {
                    int t0 = sp0_[x][k], t1 = sp1_[x][k];
                    int a0 = t0 < b0 ? b0 : t0;
                    int a1 = t1 > b1 ? b1 : t1;
                    if (a1 >= a0) {
                        for (int y = a0; y <= a1; y++) {
                            int q = above + (y - t0);
                            frame_->pixels.data()[(size_t)y * 466 + x] =
                                (k == 0 && q < 3) ? scol_[x * 3 + q]
                                                  : depth_lut_[q > 200 ? 200 : q];
                        }
                    }
                    above += t1 - t0 + 1;
                }
            }
        }
        if (wy1 >= wy0) {
            if (wy0 < ny0) ny0 = wy0;
            if (wy1 > ny1) ny1 = wy1;
        }
        if (ny1 < ny0) { ny0 = 0; ny1 = 0; }
        frame_->y0 = ny0;
        frame_->y1 = ny1;

    }

    // Substepped, implicit buoyancy: airborne motion, current, slope and capped displacement.
    void advance_boat(float dt)
    {
        float bC = cross(boat_x_, boat_y_), bA = along(boat_x_, boat_y_);
        float vC = boat_vx_ * guy_ - boat_vy_ * gux_;
        float vA = boat_vx_ * gux_ + boat_vy_ * guy_;

        float svc = 0; int n = 0;
        float top = 1e9f;

        float tl = 1e9f, tr = 1e9f;
        for (int i = 0; i < NP; i++) {
            float c = cross(x_[i], y_[i]) - bC;
            if (fabsf(c) > 34) continue;
            svc += vx_[i] * guy_ - vy_[i] * gux_;
            n++;
            float a = along(x_[i], y_[i]);
            if (a < top) top = a;
            if (c < 0) { if (a < tl) tl = a; }
            else       { if (a < tr) tr = a; }
        }

        float slope = 0.0f;
        if (tl < 1e8f && tr < 1e8f) {
            slope = (tr - tl) / 34.0f;

            if (slope >  0.6f) slope =  0.6f;
            if (slope < -0.6f) slope = -0.6f;
        }

        int bsub = (int)(dt / 0.02f) + 1;
        if (bsub > 8) bsub = 8;
        float bdt = dt / (float)bsub;

        for (int bs_i = 0; bs_i < bsub; bs_i++) {

            float depth = bA - top + BOAT_LIFT;
            if (depth > BOAT_SUB_MAX) depth = BOAT_SUB_MAX;
            if (n && depth > 0.0f) {

                const float K = 210.0f;

                float f = depth / BOAT_SUB_MAX;
                float C = 4.0f + 6.0f * f;

                if (vA > 0.0f) C *= 0.55f;

                float denom = 1.0f + C * bdt + K * bdt * bdt;
                vA = (vA + (BOAT_G - K * depth) * bdt) / denom;

                vC += ((svc / n) - vC) * (1.3f * bdt / (1.0f + 1.3f * bdt));

                vC += BOAT_G * slope * bdt;
            } else {
                vA += BOAT_G * bdt;

                if (n) vC += ((svc / n) - vC) * (0.35f * bdt / (1.0f + 0.35f * bdt));
            }
            bA += vA * bdt;
            bC += vC * bdt;
        }

        boat_x_ = CX + bA * gux_ + bC * guy_;
        boat_y_ = CY + bA * guy_ - bC * gux_;
        boat_vx_ = vC * guy_ + vA * gux_;
        boat_vy_ = -vC * gux_ + vA * guy_;

        float bdx = boat_x_ - CX, bdy = boat_y_ - CY;
        float bd = sqrtf(bdx * bdx + bdy * bdy);
        if (bd > R - 40) {
            float k = (R - 40) / bd;
            boat_x_ = CX + bdx * k;
            boat_y_ = CY + bdy * k;
            boat_vx_ *= -0.3f;
            boat_vy_ *= -0.3f;
        }

    }
};
Simulation::~Simulation() { release(state_); }
bool Simulation::initialize()
{
    if (state_) return false;
    state_ = allocate<State>();
    if (!state_) return false;
    state_->initialize();
    return true;
}
bool Simulation::advance(unsigned elapsed_ms, const Impulse &touch, Frame &frame,
    const std::atomic_bool &cancelled)
{
    if (!state_ || cancelled.load()) return false;
    auto &s = *state_;
    if (touch.active) {
        // A real touch stirs nearby particles; it never supplies fabricated IMU samples.
        for (int i = 0; i < NP; ++i) {
            const float dx = s.x_[i] - touch.x, dy = s.y_[i] - touch.y;
            const float d2 = dx * dx + dy * dy;
            if (d2 >= 80 * 80) continue;
            const float weight = 1 - std::sqrt(d2) / 80;
            const float inv = d2 > 1 ? frsqrt(d2) : 1;
            s.vx_[i] += weight * (touch.vx + dx * inv * touch.burst);
            s.vy_[i] += weight * (touch.vy + dy * inv * touch.burst);
        }
    }
    const float dt = std::clamp(elapsed_ms, 1u, 100u) * 0.001f;
    const int sub = std::min(10, static_cast<int>(dt / 0.010f) + 1);
    const float step_dt = std::min(0.010f, dt / sub);
    for (int i = 0; i < sub; ++i) {
        if (cancelled.load()) return false;
        s.fluid_step(step_dt, 0, BOAT_G);
    }
    if (cancelled.load()) return false;
    s.advance_boat(dt);
    s.frame_ = &frame;
    s.build_spans();
    s.paint_img();
    s.frame_ = nullptr;
    return !cancelled.load();
}
Diagnostics Simulation::diagnostics() const
{
    Diagnostics result{};
    if (!state_) { result.finite = false; return result; }
    const auto &s = *state_;
    result.boat_x = s.boat_x_; result.boat_y = s.boat_y_;
    result.finite = std::isfinite(s.boat_x_) && std::isfinite(s.boat_y_);
    result.neighbor_overflow = s.neighbor_overflow_;
    for (int i = 0; i < NP; ++i) {
        const float dx = s.x_[i] - CX, dy = s.y_[i] - CY;
        result.escaped += dx * dx + dy * dy > R * R + 1;
        result.finite &= std::isfinite(s.x_[i]) && std::isfinite(s.y_[i]) && std::isfinite(s.vx_[i]) && std::isfinite(s.vy_[i]);
        result.energy += std::fabs(s.vx_[i]) + std::fabs(s.vy_[i]);
        for (float value : {s.x_[i], s.y_[i], s.vx_[i], s.vy_[i]}) {
            result.fingerprint ^= std::bit_cast<uint32_t>(value);
            result.fingerprint *= 1099511628211ULL;
        }
    }
    return result;
}
}
