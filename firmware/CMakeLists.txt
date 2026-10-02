cmake_minimum_required(VERSION 3.16)

set(PROJECT_VER "0.3.0")
set(EXTRA_COMPONENT_DIRS "${CMAKE_CURRENT_LIST_DIR}/native_apps")

include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(espocket)

# The released Waveshare 1.75C custom HAL still uses the pre-0.8 backlight type name.
# Board Manager adds this component only after generating the selected board configuration.
if(TARGET idf::brookesia_hal_custom)
    idf_component_get_property(brookesia_hal_custom_lib brookesia_hal_custom COMPONENT_LIB)
    target_compile_options(
        ${brookesia_hal_custom_lib} PRIVATE
        "-Wno-error=attributes"
        "SHELL:-include ${CMAKE_CURRENT_LIST_DIR}/compat/brookesia_hal_custom_0_1_backlight.hpp"
    )
endif()

# Repair IDF/Picolibc attribute spelling in the affected board-header TUs.
# This does not relax warnings or modify managed component sources.
idf_component_get_property(espocket_hal_adaptor_lib espressif__brookesia_hal_adaptor COMPONENT_LIB)
idf_component_get_property(espocket_hal_adaptor_dir espressif__brookesia_hal_adaptor COMPONENT_DIR)
foreach(espocket_hal_source IN ITEMS src/display/device.cpp src/audio/device.cpp src/audio/codec_player_impl.cpp)
    set_property(SOURCE "${espocket_hal_adaptor_dir}/${espocket_hal_source}"
        TARGET_DIRECTORY ${espocket_hal_adaptor_lib}
        APPEND PROPERTY COMPILE_OPTIONS
        "-include" "${CMAKE_CURRENT_LIST_DIR}/compat/idf_6_0_1_picolibc_noreturn.hpp")
endforeach()
