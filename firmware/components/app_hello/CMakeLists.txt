idf_component_register(
    SRCS "src/hello_app.cpp"
    INCLUDE_DIRS "include"
    REQUIRES brookesia_system_core
)

target_compile_features(${COMPONENT_LIB} PUBLIC cxx_std_23)
