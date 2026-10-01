idf_component_register(
    SRCS "src/system.cpp" "src/power_key_monitor.cpp"
    INCLUDE_DIRS "include"
    REQUIRES
        app_hello
        espocket_navigation
        shell_circular
        brookesia_app_settings
        brookesia_app_store
        brookesia_gui_lvgl
        brookesia_system_core
        brookesia_service_display
        brookesia_service_helper
        brookesia_service_manager
    PRIV_REQUIRES brookesia_lib_utils esp_driver_gpio esp_timer
)

target_compile_features(${COMPONENT_LIB} PUBLIC cxx_std_23)
