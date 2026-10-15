idf_component_register(
    SRCS "src/mouse_endpoint.cpp" "src/mouse_model.cpp"
    INCLUDE_DIRS "include"
    REQUIRES espocket_imu
)
target_compile_features(${COMPONENT_LIB} PUBLIC cxx_std_23)
