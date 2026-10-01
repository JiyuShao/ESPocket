# Unique generated name avoids ESP-IDF basename symbol collisions.
configure_file("${CMAKE_CURRENT_LIST_DIR}/resources/gui.json" "${CMAKE_CURRENT_BINARY_DIR}/hello_gui.json" COPYONLY)

idf_component_register(
    SRCS "src/hello_app.cpp"
    INCLUDE_DIRS "include"
    EMBED_TXTFILES "${CMAKE_CURRENT_BINARY_DIR}/hello_gui.json"
    REQUIRES brookesia_system_core espocket_navigation
)

target_compile_features(${COMPONENT_LIB} PUBLIC cxx_std_23)
