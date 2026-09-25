idf_component_register(
    SRCS "src/system.cpp"
    INCLUDE_DIRS "include"
    REQUIRES
        shell_circular
        brookesia_gui_lvgl
        brookesia_system_core
        brookesia_service_display
        brookesia_service_helper
        brookesia_service_manager
)

target_compile_features(${COMPONENT_LIB} PUBLIC cxx_std_23)
