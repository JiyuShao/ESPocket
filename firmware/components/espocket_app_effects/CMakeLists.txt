idf_component_register(SRCS "src/short_effect.cpp" INCLUDE_DIRS "include"
    REQUIRES brookesia_service_audio brookesia_service_manager
    PRIV_REQUIRES brookesia_service_helper esp_timer)
target_compile_features(${COMPONENT_LIB} PUBLIC cxx_std_23)
