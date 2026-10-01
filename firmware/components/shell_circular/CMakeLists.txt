# Unique generated name avoids ESP-IDF basename symbol collisions.
configure_file("${CMAKE_CURRENT_LIST_DIR}/resources/gui.json" "${CMAKE_CURRENT_BINARY_DIR}/shell_gui.json" COPYONLY)

idf_component_register(
    SRCS "src/circular_shell.cpp" "src/shell_document.cpp"
        "src/shell_navigation.cpp" "src/shell_gesture.cpp" "src/shell_keyboard.cpp" "src/shell_status.cpp"
    INCLUDE_DIRS "include"
    EMBED_TXTFILES "${CMAKE_CURRENT_BINARY_DIR}/shell_gui.json"
    REQUIRES brookesia_system_core brookesia_service_manager brookesia_lib_utils
    PRIV_REQUIRES
        esp_lvgl_adapter lvgl brookesia_service_display brookesia_service_device
        brookesia_service_wifi brookesia_service_sntp brookesia_service_helper esp_timer
)

target_compile_features(${COMPONENT_LIB} PUBLIC cxx_std_23)
