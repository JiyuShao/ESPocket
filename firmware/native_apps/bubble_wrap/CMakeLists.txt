configure_file("${CMAKE_CURRENT_LIST_DIR}/resources/gui.json" "${CMAKE_CURRENT_BINARY_DIR}/bubble_wrap_gui.json" COPYONLY)
idf_component_register(
    SRCS "src/bubble_wrap_app.cpp" "src/bubble_model.cpp" "src/bubble_content.cpp" "src/bubble_sound.cpp"
    INCLUDE_DIRS "include"
    EMBED_TXTFILES "${CMAKE_CURRENT_BINARY_DIR}/bubble_wrap_gui.json"
    REQUIRES brookesia_system_core espocket_navigation
    PRIV_REQUIRES brookesia_gui_lvgl brookesia_service_audio brookesia_service_helper esp_timer lvgl
)
target_compile_features(${COMPONENT_LIB} PUBLIC cxx_std_23)
