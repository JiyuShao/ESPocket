idf_component_register(
    SRCS "app_main.cpp"
    REQUIRES espocket_system
)

target_compile_features(${COMPONENT_LIB} PRIVATE cxx_std_23)
