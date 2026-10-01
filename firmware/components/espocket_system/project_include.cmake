# Configure upstream staging before any component stages its GUI resources.
idf_component_get_property(espocket_core_component_dir espressif__brookesia_system_core COMPONENT_DIR)
include("${espocket_core_component_dir}/cmake/runtime_paths.cmake")
brookesia_system_core_set_esp_runtime_paths(
    INTERNAL_ROOT "/littlefs"
    RESOURCE_STAGE_ROOT "${CMAKE_BINARY_DIR}/littlefs-root"
)
