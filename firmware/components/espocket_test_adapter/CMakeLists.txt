idf_component_register(
    SRCS "src/developer_mode.cpp" "src/developer_mode_nvs.cpp" "src/test_protocol.cpp"
         "src/interaction_test_adapter.cpp"
    INCLUDE_DIRS "include"
    PRIV_REQUIRES nvs_flash esp_driver_usb_serial_jtag esp_app_format espressif__esp-boost
)

target_compile_features(${COMPONENT_LIB} PUBLIC cxx_std_23)
