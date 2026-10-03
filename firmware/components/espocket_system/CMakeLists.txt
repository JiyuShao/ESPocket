configure_file("${CMAKE_CURRENT_LIST_DIR}/resources/dark_theme.json" "${CMAKE_CURRENT_BINARY_DIR}/espocket_dark_theme.json" COPYONLY)
configure_file("${CMAKE_CURRENT_LIST_DIR}/resources/light_theme.json" "${CMAKE_CURRENT_BINARY_DIR}/espocket_light_theme.json" COPYONLY)

idf_component_register(
    SRCS "src/system.cpp" "src/system_lifecycle.cpp" "src/system_navigation.cpp"
        "src/system_display.cpp" "src/system_timeout.cpp" "src/system_power.cpp" "src/power_key_monitor.cpp" "src/settings_navigation_adapter.cpp"
        "src/native_page_installation.cpp" "src/system_test_input.cpp"
        "src/system_runtime_navigation.cpp" "src/runtime_navigation_provider.cpp"
        "src/system_cards.cpp" "src/card_document.cpp"
    EMBED_TXTFILES "${CMAKE_CURRENT_BINARY_DIR}/espocket_dark_theme.json" "${CMAKE_CURRENT_BINARY_DIR}/espocket_light_theme.json"
    INCLUDE_DIRS "include"
    REQUIRES brookesia_system_core brookesia_service_manager espocket_navigation espocket_semantics freertos
    PRIV_REQUIRES
        hello espocket_test_adapter shell_circular
        brookesia_app_settings brookesia_app_store brookesia_gui_lvgl
        brookesia_service_display brookesia_service_helper brookesia_lib_utils
        esp_driver_gpio esp_timer esp_app_format brookesia_runtime_manager nvs_flash
)

target_compile_features(${COMPONENT_LIB} PUBLIC cxx_std_23)

idf_component_get_property(espocket_settings_component_dir espressif__brookesia_app_settings COMPONENT_DIR)

# Reject dependency upgrades that no longer match the Settings compatibility map.
execute_process(
    COMMAND "${CMAKE_COMMAND}" -E env "ESPOCKET_SETTINGS_COMPONENT_DIR=${espocket_settings_component_dir}"
        "${PYTHON}" "${CMAKE_CURRENT_LIST_DIR}/test/test_settings_adapter.py"
        SettingsCompatibility.test_locked_resources_match_adapter
    RESULT_VARIABLE settings_compatibility_result
    OUTPUT_VARIABLE settings_compatibility_output
    ERROR_VARIABLE settings_compatibility_error
)
if(NOT settings_compatibility_result EQUAL 0)
    message(FATAL_ERROR "Settings adapter compatibility failed:\n${settings_compatibility_output}${settings_compatibility_error}")
endif()
