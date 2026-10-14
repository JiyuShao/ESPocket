idf_component_register(
    SRCS "src/imu_source.cpp"
    INCLUDE_DIRS "include"
)

target_compile_features(${COMPONENT_LIB} PUBLIC cxx_std_23)
