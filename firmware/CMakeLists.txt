cmake_minimum_required(VERSION 3.16)

include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(espocket)

# ESP-IDF 6.0.1 + Picolibc exposes a false-positive attribute warning through hal/assert.h.
idf_build_set_property(COMPILE_OPTIONS "-Wno-error=attributes" APPEND)

# The released Waveshare 1.75C custom HAL still uses the pre-0.8 backlight type name.
# Board Manager adds this component only after generating the selected board configuration.
if(TARGET idf::brookesia_hal_custom)
    idf_component_get_property(brookesia_hal_custom_lib brookesia_hal_custom COMPONENT_LIB)
    target_compile_options(
        ${brookesia_hal_custom_lib} PRIVATE
        "SHELL:-include ${CMAKE_CURRENT_LIST_DIR}/compat/brookesia_hal_custom_0_1_backlight.hpp"
    )
endif()
