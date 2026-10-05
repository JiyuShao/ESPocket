idf_component_register(
    SRCS "src/developer_mode.cpp" "src/developer_mode_nvs.cpp" "src/test_protocol.cpp"
         "src/interaction_test_adapter.cpp" "src/test_input_queue.cpp" "src/touch_input_sequence.cpp"
         "src/owner_snapshot_queue.cpp" "src/screenshot.cpp" "src/display_screenshot.cpp"
    INCLUDE_DIRS "include"
    REQUIRES freertos
    PRIV_REQUIRES espressif__brookesia_service_helper esp_driver_usb_serial_jtag esp_app_format espressif__esp-boost
        lvgl esp_lvgl_adapter mbedtls
)

target_compile_features(${COMPONENT_LIB} PUBLIC cxx_std_23)
