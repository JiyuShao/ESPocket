// SPDX-License-Identifier: MIT
// Sphere projection, shade and UV cache adapted from locked The-Badge orb.c.
#include "espocket/orbit_renderer.hpp"
#include "orbit_textures.hpp"
#include <cmath>
#include <cstring>
#include <new>
#ifdef ESP_PLATFORM
#include "esp_heap_caps.h"
#endif
namespace espocket::orbit {
namespace {
constexpr int CX = center, CY = center, ORB_R = radius, TEX_W = 512, TEX_H = 256;
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
static inline float atan2_fast(float y, float x)
{
    float ax = fabsf(x), ay = fabsf(y);
    float d = (ax > ay ? ax : ay) + 1e-12f;
    float a = (ax > ay ? ay : ax) / d;
    float ss = a * a;
    float r = ((-0.0464964749f * ss + 0.15931422f) * ss - 0.327622764f) * ss * a + a;
    if (ay > ax) r = 1.57079637f - r;
    if (x < 0)   r = 3.14159274f - r;
    return y < 0 ? -r : r;
}
}
std::shared_ptr<Frame> Frame::create() { return {allocate<Frame>(), [](Frame *p) { release(p); }}; }
struct Renderer::State {
    static constexpr int stride = 2 * radius + 1, pixels = stride * stride;
    std::array<uint16_t, TEX_W * TEX_H> texture_{};
    const uint16_t *tex_ = texture_.data();
    int16_t lut_z_[pixels]{};
    uint8_t lut_shade_[pixels]{};
    uint16_t lut_tu_[pixels]{}, lut_tv_[pixels]{};
    int32_t span0_[stride]{}, span1_[stride]{};
    float col_x_[stride]{}, asin_tab_[1025]{};
    float lon_ = 0, tilt_ = 0, lean_ = 0, uv_tilt_ = 0, uv_lean_ = 0;
    bool coarse_ = false, uv_ok_ = false, has_frame_ = false;
    Kind kind_ = Kind::Moon;
    uint16_t *fb_ = nullptr;
    void initialize(Kind kind)
    {
        kind_ = kind; uv_ok_ = false;
        std::memcpy(texture_.data(), texture(kind), sizeof(texture_));
        for (int i = 0; i <= 2 * ORB_R; i++) col_x_[i] = (float)(i - ORB_R) / ORB_R;
        for (int i = 0; i <= 1024; i++) {
            float t = (float)i / 512.0f - 1.0f;
            if (t >  1) t =  1;
            if (t < -1) t = -1;
            asin_tab_[i] = asinf(t);
        }

        const float lx = -0.45f, ly = 0.42f, lz = 0.79f;

        for (int j2 = 0; j2 <= 2 * ORB_R; j2++) {
            int dy = j2 - ORB_R;
            float yy = -(float)dy / ORB_R;
            float rowr2 = 1.0f - yy * yy;
            if (rowr2 <= 0) { span0_[j2] = 1; span1_[j2] = 0; continue; }
            int half = (int)(ORB_R * sqrtf(rowr2));
            span0_[j2] = ORB_R - half;
            span1_[j2] = ORB_R + half;

            for (int i2 = span0_[j2]; i2 <= span1_[j2]; i2++) {
                int dx = i2 - ORB_R;
                float xx = (float)dx / ORB_R;
                float zz2 = 1.0f - xx * xx - yy * yy;
                if (zz2 < 0) zz2 = 0;
                float zz = sqrtf(zz2);

                if (kind_ == Kind::Sun) {
                    lut_shade_[(size_t)j2 * (2 * ORB_R + 1) + i2] =
                        (uint8_t)((0.88f + 0.12f * zz) * 255.0f);
                    lut_z_[(size_t)j2 * (2 * ORB_R + 1) + i2] = (int16_t)(zz * 32767.0f);
                    continue;
                }
                float nl = xx * lx + yy * ly + zz * lz;
                if (nl < 0) nl = 0;

                float amb = (kind_ == Kind::Earth) ? 0.50f : 0.42f;
                float rim = (kind_ == Kind::Earth) ? 0.78f : 0.74f;
                float sh = amb + (1.0f - amb) * nl;
                sh *= rim + (1.0f - rim) * zz;
                if (sh > 1.0f) sh = 1.0f;
                size_t idx = (size_t)j2 * (2 * ORB_R + 1) + i2;
                lut_shade_[idx] = (uint8_t)(sh * 255.0f);
                lut_z_[idx] = (int16_t)(zz * 32767.0f);
            }
        }
    }
    bool render(const Attitude &pose, Frame &frame, const std::atomic_bool &cancelled)
    {
        lon_ = pose.longitude; tilt_ = pose.tilt; lean_ = pose.lean;
        // orb_start draws a sharp initial image before its first motion tick.
        // Preserve that even when a later pose replaces the initial queued request.
        coarse_ = pose.moving && has_frame_;
        fb_ = frame.pixels.data();
        float ct = cosf(tilt_), st = sinf(tilt_);

        float cl = cosf(lean_), sl = sinf(lean_);
        bool  leaning = (lean_ != 0.0f);
        int   rot = (int)(lon_ * TEX_W);
        int   stride = 2 * ORB_R + 1;

        const float U2TEX = TEX_W / 6.2831853f;
        const float V2TEX = TEX_H / 3.1415927f;

        bool use_uv = (uv_ok_ && uv_tilt_ == tilt_ && uv_lean_ == lean_);
        bool fill_uv = (!use_uv && !coarse_);
        int step = (coarse_ && !use_uv) ? 2 : 1;

        for (int j = 0; j <= 2 * ORB_R; j += step) {
            if (cancelled) return false;
            int y = CY - ORB_R + j;
            if (y < 0 || y >= 466) continue;
            int i0 = span0_[j], i1 = span1_[j];
            if (i0 > i1) continue;
            uint16_t *out = fb_ + (size_t)y * 466;
            const uint8_t *sd = lut_shade_ + (size_t)j * stride;
            const int16_t *zl = lut_z_     + (size_t)j * stride;

            float yy = -(float)(j - ORB_R) / ORB_R;
            float yc = yy * ct, ys = yy * st;

            float oy = (float)(j - ORB_R), ox0 = (float)(i0 - ORB_R);
            float inv_R = 1.0f / ORB_R;
            float xr = (ox0 * cl + oy * sl) * inv_R, xr_d =  cl * inv_R;
            float yr = -(-ox0 * sl + oy * cl) * inv_R, yr_d = sl * inv_R;

            uint16_t *ru = lut_tu_ + (size_t)j * stride;
            uint16_t *rv = lut_tv_ + (size_t)j * stride;

            if (use_uv) {
                for (int i = i0; i <= i1; i++) {
                    int x = CX - ORB_R + i;
                    if (x < 0 || x >= 466) continue;
                    int tu = (ru[i] + rot) & (TEX_W - 1);
                    uint16_t c = tex_[(size_t)rv[i] * TEX_W + tu];
                    uint32_t sh = sd[i];
                    uint32_t r = ((c >> 11) & 0x1F) * sh >> 8;
                    uint32_t g = ((c >> 5)  & 0x3F) * sh >> 8;
                    uint32_t b = ( c        & 0x1F) * sh >> 8;
                    out[x] = (uint16_t)((r << 11) | (g << 5) | b);
                }
                continue;
            }

            uint16_t first_px = 0, last_px = 0;
            for (int i = i0; i <= i1; i += step, xr += xr_d * step, yr += yr_d * step) {
                int x = CX - ORB_R + i;
                if (x < 0 || x >= 466) continue;

                float cx = col_x_[i];
                if (leaning) { cx = xr; yc = yr * ct; ys = yr * st; }

                float zz = zl[i] * (1.0f / 32767.0f);

                float y2 = yc - zz * st;
                float z2 = ys + zz * ct;

                int tu0 = (int)(atan2_fast(cx, z2) * U2TEX) & (TEX_W - 1);
                int tu = (tu0 + rot) & (TEX_W - 1);

                float fa = (y2 + 1.0f) * 512.0f;
                int   ia = (int)fa;
                if (ia < 0) ia = 0;
                if (ia > 1023) ia = 1023;
                float lat = asin_tab_[ia] + (asin_tab_[ia + 1] - asin_tab_[ia]) * (fa - ia);
                int tv = (int)(TEX_H * 0.5f - lat * V2TEX);
                if (tv < 0) tv = 0;
                if (tv >= TEX_H) tv = TEX_H - 1;

                if (fill_uv) { ru[i] = (uint16_t)tu0; rv[i] = (uint16_t)tv; }

                uint16_t c = tex_[(size_t)tv * TEX_W + tu];
                uint32_t sh = sd[i];
                uint32_t r = ((c >> 11) & 0x1F) * sh >> 8;
                uint32_t g = ((c >> 5)  & 0x3F) * sh >> 8;
                uint32_t b = ( c        & 0x1F) * sh >> 8;
                uint16_t px = (uint16_t)((r << 11) | (g << 5) | b);
                out[x] = px;
                if (i == i0) first_px = px;
                last_px = px;
                if (step == 2) {
                    if (x + 1 < 466 && i + 1 <= i1) out[x + 1] = px;
                    if (y + 1 < 466) {
                        uint16_t *o2 = fb_ + (size_t)(y + 1) * 466;
                        int j2 = j + 1;
                        if (j2 <= 2 * ORB_R && i >= span0_[j2] && i <= span1_[j2]) {
                            o2[x] = px;
                            if (x + 1 < 466 && i + 1 <= span1_[j2]) o2[x + 1] = px;
                        }
                    }
                }
            }

            if (step == 2 && j + 1 <= 2 * ORB_R) {
                int j2 = j + 1, y2 = y + 1;
                if (y2 < 466 && span0_[j2] <= span1_[j2]) {
                    uint16_t *o2 = fb_ + (size_t)y2 * 466;
                    for (int i = span0_[j2]; i < i0; i++) {
                        int x2 = CX - ORB_R + i;
                        if (x2 >= 0 && x2 < 466) o2[x2] = first_px;
                    }
                    for (int i = i1 + 1; i <= span1_[j2]; i++) {
                        int x2 = CX - ORB_R + i;
                        if (x2 >= 0 && x2 < 466) o2[x2] = last_px;
                    }
                }
            }
        }
        if (fill_uv) { uv_ok_ = true; uv_tilt_ = tilt_; uv_lean_ = lean_; }
        has_frame_ = true;
        return !cancelled;
    }
};
Renderer::~Renderer() { release(state_); }
bool Renderer::initialize(Kind kind)
{
    if (state_ || !texture(kind)) return false;
    state_ = allocate<State>();
    if (!state_) return false;
    state_->initialize(kind);
    return true;
}
bool Renderer::paint(Attitude pose, Frame &frame, const std::atomic_bool &cancelled)
{
    if (!state_ || cancelled || !std::isfinite(pose.longitude) || !std::isfinite(pose.tilt) || !std::isfinite(pose.lean)) return false;
    // Bound conversions even for diagnostic callers; normal Motion is already wrapped.
    pose.longitude -= std::floor(pose.longitude);
    pose.tilt = std::remainder(pose.tilt, 6.2831853f);
    pose.lean = std::remainder(pose.lean, 6.2831853f);
    return state_->render(pose, frame, cancelled);
}
}
