configure_file("${CMAKE_CURRENT_LIST_DIR}/resources/dark_theme.json" "${CMAKE_CURRENT_BINARY_DIR}/espocket_dark_theme.json" COPYONLY)
configure_file("${CMAKE_CURRENT_LIST_DIR}/resources/light_theme.json" "${CMAKE_CURRENT_BINARY_DIR}/espocket_light_theme.json" COPYONLY)

idf_component_register(
    SRCS "src/system.cpp" "src/system_lifecycle.cpp" "src/system_navigation.cpp"
        "src/system_display.cpp" "src/system_message_dialog.cpp" "src/system_timeout.cpp" "src/system_power.cpp" "src/power_key_monitor.cpp" "src/settings_navigation_adapter.cpp"
        "src/native_page_installation.cpp" "src/system_test_input.cpp"
        "src/system_runtime_navigation.cpp" "src/runtime_navigation_provider.cpp"
        "src/system_cards.cpp" "src/card_document.cpp" "src/system_package_acceptance.cpp" "src/runtime_render_probe.cpp"
    EMBED_TXTFILES "${CMAKE_CURRENT_BINARY_DIR}/espocket_dark_theme.json" "${CMAKE_CURRENT_BINARY_DIR}/espocket_light_theme.json"
    INCLUDE_DIRS "include"
    REQUIRES brookesia_system_core brookesia_service_manager espocket_navigation espocket_semantics freertos
    PRIV_REQUIRES
        hello espocket_test_adapter shell_circular esp_lvgl_adapter lvgl
        brookesia_app_settings brookesia_app_store brookesia_gui_lvgl
        brookesia_service_display brookesia_service_helper brookesia_lib_utils
        esp_driver_gpio esp_timer esp_app_format brookesia_runtime_manager nvs_flash
)

target_compile_features(${COMPONENT_LIB} PUBLIC cxx_std_23)

if(CONFIG_ESPOCKET_PACKAGE_ACCEPTANCE_TEST)
    if(NOT EXISTS "${CONFIG_ESPOCKET_PACKAGE_ACCEPTANCE_INPUTS}/package_acceptance_inputs.hpp")
        message(FATAL_ERROR "Package acceptance requires explicit external public test inputs")
    endif()
    target_include_directories(${COMPONENT_LIB} PRIVATE "${CONFIG_ESPOCKET_PACKAGE_ACCEPTANCE_INPUTS}")
endif()

idf_component_get_property(espocket_settings_component_dir espressif__brookesia_app_settings COMPONENT_DIR)

# Reject dependency upgrades that no longer match the Settings compatibility map.
execute_process(
    COMMAND "${CMAKE_COMMAND}" -E env "ESPOCKET_SETTINGS_COMPONENT_DIR=${espocket_settings_component_dir}"
        "${PYTHON}" "${CMAKE_CURRENT_LIST_DIR}/test/test_settings_adapter.py"
        SettingsCompatibility.test_locked_resources_match_adapter
    RESULT_VARIABLE settings_compatibility_result
    OUTPUT_VARIABLE settings_compatibility_output
    ERROR_VARIABLE settings_compatibility_error
)
if(NOT settings_compatibility_result EQUAL 0)
    message(FATAL_ERROR "Settings adapter compatibility failed:\n${settings_compatibility_output}${settings_compatibility_error}")
endif()

# Explicit build allowlist: exact maintained Runtime bytes, never a directory-name exemption.
set(espocket_builtin_root "${PROJECT_DIR}/runtime_apps/hello/src")
file(GLOB_RECURSE espocket_builtin_files CONFIGURE_DEPENDS "${espocket_builtin_root}/*")
set(espocket_builtin_header "${CMAKE_CURRENT_BINARY_DIR}/espocket_builtin_packages.hpp")
file(WRITE "${espocket_builtin_header}" "#pragma once\ninline void configure_builtin_packages(esp_brookesia::system::core::RuntimePackagePolicy &policy) {\n")
foreach(espocket_builtin_file IN LISTS espocket_builtin_files)
    if(NOT IS_DIRECTORY "${espocket_builtin_file}")
        file(RELATIVE_PATH espocket_builtin_member "${espocket_builtin_root}" "${espocket_builtin_file}")
        file(SHA256 "${espocket_builtin_file}" espocket_builtin_digest)
        set_property(DIRECTORY APPEND PROPERTY CMAKE_CONFIGURE_DEPENDS "${espocket_builtin_file}")
        file(APPEND "${espocket_builtin_header}" "policy.built_in_members[\"espocket.app.hello_runtime\"][\"${espocket_builtin_member}\"] = \"${espocket_builtin_digest}\";\n")
    endif()
endforeach()
file(APPEND "${espocket_builtin_header}" "}\n")
target_include_directories(${COMPONENT_LIB} PRIVATE "${CMAKE_CURRENT_BINARY_DIR}")
