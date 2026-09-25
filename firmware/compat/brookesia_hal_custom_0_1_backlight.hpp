/*
 * SPDX-License-Identifier: Apache-2.0
 */
#pragma once

#include "brookesia/hal_adaptor/display/device.hpp"
#include "brookesia/hal_interface/interfaces/display/backlight.hpp"

namespace esp_brookesia::hal {

// brookesia_hal_custom 0.1.0 still uses the pre-0.8 display backlight type name.
class DisplayBacklightIface : public display::BacklightIface {
public:
    DisplayBacklightIface()
        : display::BacklightIface(display::BacklightIface::Info{
            .group_id = DisplayDevice::LCD_GROUP_ID,
        })
    {
    }
};

} // namespace esp_brookesia::hal
