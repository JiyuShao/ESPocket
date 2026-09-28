idf_component_register(
    SRCS "src/system.cpp"
    INCLUDE_DIRS "include"
    REQUIRES
        app_hello
        shell_circular
        brookesia_app_settings
        brookesia_app_store
        brookesia_gui_lvgl
        brookesia_system_core
        brookesia_service_display
        brookesia_service_helper
        brookesia_service_manager
    PRIV_REQUIRES brookesia_lib_utils
)

target_compile_features(${COMPONENT_LIB} PUBLIC cxx_std_23)
