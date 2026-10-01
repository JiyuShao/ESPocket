idf_component_register(
    SRCS "app_main.cpp"
    REQUIRES espocket_system
)

target_compile_features(${COMPONENT_LIB} PRIVATE cxx_std_23)

idf_component_get_property(
    brookesia_system_core_dir
    espressif__brookesia_system_core
    COMPONENT_DIR
)
include("${brookesia_system_core_dir}/cmake/runtime_app_stage.cmake")
brookesia_system_core_get_esp_runtime_app_stage_root(runtime_app_stage_root)
brookesia_stage_runtime_app_package(
    PACKAGE_ID "espocket.app.hello_runtime"
    SOURCE_DIR "${PROJECT_DIR}/runtime_apps/hello/src"
    STAGE_ROOT "${runtime_app_stage_root}"
    NO_INDEX
)

get_property(runtime_app_stage_targets GLOBAL PROPERTY BROOKESIA_RUNTIME_APP_STAGE_TARGETS)
list(REMOVE_DUPLICATES runtime_app_stage_targets)
littlefs_create_partition_image(
    littlefs_data
    "${CMAKE_BINARY_DIR}/littlefs-root"
    FLASH_IN_PROJECT
    DEPENDS ${runtime_app_stage_targets}
)
