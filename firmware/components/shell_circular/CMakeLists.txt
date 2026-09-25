idf_component_register(
    SRCS "src/circular_shell.cpp"
    INCLUDE_DIRS "include"
    REQUIRES
        brookesia_system_core
        brookesia_service_display
        brookesia_service_device
        brookesia_service_wifi
        brookesia_service_sntp
        brookesia_service_helper
        brookesia_service_manager
)

target_compile_features(${COMPONENT_LIB} PUBLIC cxx_std_23)
