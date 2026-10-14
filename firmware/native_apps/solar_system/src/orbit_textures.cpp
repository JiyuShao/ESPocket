// NASA maps copied byte-for-byte from the locked source. See ../NOTICE.
#include "orbit_textures.hpp"
#include "../resources/orb_tex_moon.h"
#include "../resources/orb_tex_earth.h"
#include "../resources/orb_tex_sun.h"
#include "../resources/orb_tex_jupiter.h"
namespace espocket::orbit {
const uint16_t *texture(Kind kind)
{
    switch (kind) {
    case Kind::Moon: return ORB_TEX_MOON;
    case Kind::Earth: return ORB_TEX_EARTH;
    case Kind::Sun: return ORB_TEX_SUN;
    case Kind::Jupiter: return ORB_TEX_JUPITER;
    }
    return nullptr;
}
}
