configure_file("${CMAKE_CURRENT_LIST_DIR}/resources/gui.json" "${CMAKE_CURRENT_BINARY_DIR}/ble_remote_gui.json" COPYONLY)
idf_component_register(
    SRCS "src/ble_remote_app.cpp" "src/ble_remote_content.cpp"
    INCLUDE_DIRS "include"
    EMBED_TXTFILES "${CMAKE_CURRENT_BINARY_DIR}/ble_remote_gui.json"
    REQUIRES brookesia_system_core espocket_navigation espocket_hid espocket_imu
    PRIV_REQUIRES brookesia_gui_lvgl esp_timer lvgl
)
target_compile_features(${COMPONENT_LIB} PUBLIC cxx_std_23)
