configure_file("${CMAKE_CURRENT_LIST_DIR}/resources/gui.json" "${CMAKE_CURRENT_BINARY_DIR}/solar_system_gui.json" COPYONLY)
idf_component_register(
    SRCS "src/solar_system_app.cpp" "src/orbit_motion.cpp" "src/orbit_renderer.cpp" "src/orbit_textures.cpp" "src/orbit_worker.cpp" "src/orbit_content.cpp"
    INCLUDE_DIRS "include"
    EMBED_TXTFILES "${CMAKE_CURRENT_BINARY_DIR}/solar_system_gui.json"
    REQUIRES brookesia_system_core espocket_navigation
    PRIV_REQUIRES brookesia_gui_lvgl esp_timer lvgl pthread heap
)
target_compile_features(${COMPONENT_LIB} PUBLIC cxx_std_23)
