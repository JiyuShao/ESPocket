idf_component_register(
    SRCS "src/page_navigator.cpp" "src/card_registry.cpp" "src/card_session.cpp" "src/page_declaration_codec.cpp"
        "src/runtime_page_adapter.cpp" "src/navigation_request_queue.cpp"
    INCLUDE_DIRS "include"
    PRIV_REQUIRES espressif__esp-boost
)

target_compile_features(${COMPONENT_LIB} PUBLIC cxx_std_23)
