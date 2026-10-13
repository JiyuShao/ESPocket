configure_file("${CMAKE_CURRENT_LIST_DIR}/resources/gui.json" "${CMAKE_CURRENT_BINARY_DIR}/bubble_wrap_gui.json" COPYONLY)
idf_component_register(
    SRCS "src/bubble_wrap_app.cpp" "src/bubble_model.cpp" "src/bubble_content.cpp"
    INCLUDE_DIRS "include"
    EMBED_TXTFILES "${CMAKE_CURRENT_BINARY_DIR}/bubble_wrap_gui.json"
    REQUIRES brookesia_system_core espocket_navigation espocket_app_effects
    PRIV_REQUIRES brookesia_gui_lvgl esp_timer lvgl
)
target_compile_features(${COMPONENT_LIB} PUBLIC cxx_std_23)
