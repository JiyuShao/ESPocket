configure_file("${CMAKE_CURRENT_LIST_DIR}/resources/gui.json" "${CMAKE_CURRENT_BINARY_DIR}/water_gui.json" COPYONLY)
idf_component_register(
    SRCS "src/water_app.cpp" "src/water_simulation.cpp" "src/water_worker.cpp" "src/water_content.cpp"
    INCLUDE_DIRS "include"
    EMBED_TXTFILES "${CMAKE_CURRENT_BINARY_DIR}/water_gui.json"
    REQUIRES brookesia_system_core espocket_navigation
    PRIV_REQUIRES brookesia_gui_lvgl esp_timer lvgl pthread heap
)
target_compile_features(${COMPONENT_LIB} PUBLIC cxx_std_23)
