/*
 * SPDX-License-Identifier: Apache-2.0
 */
// Affected: Waveshare brookesia_hal_custom 0.1.0 with Brookesia HAL 0.8.x.
// Upstream issue: the generated board HAL uses the removed DisplayBacklightIface
// name and does not initialize the required LCD backlight group. No upstream
// issue number has been assigned in this repository.
// Remove when the board package uses display::BacklightIface with LCD_GROUP_ID
// and compiles against the locked HAL without this forced include.
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
