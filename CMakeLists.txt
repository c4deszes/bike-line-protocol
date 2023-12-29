cmake_minimum_required(VERSION 3.20)
project(
    line-protocol
    VERSION "0.1.0"
    LANGUAGES C CXX)

option(LINE_PROTOCOL_BUILD_TESTS "Enables library test cases" OFF)

find_package(Python REQUIRED)
add_library(line-protocol-api INTERFACE)
target_include_directories(line-protocol-api INTERFACE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

add_library(line-protocol-sources INTERFACE)
target_sources(line-protocol-sources INTERFACE
    ${CMAKE_CURRENT_SOURCE_DIR}/src/transport.c
    ${CMAKE_CURRENT_SOURCE_DIR}/src/application.c
    ${CMAKE_CURRENT_SOURCE_DIR}/src/diagnostics.c
)

add_library(line-protocol-adapter-sources INTERFACE)
target_sources(line-protocol-adapter-sources INTERFACE
    ${CMAKE_CURRENT_SOURCE_DIR}/src/app_adapter.c
)

function(line_codegen)

cmake_parse_arguments(
    ""
    "ADAPTER"
    "TARGET;NETWORK;NODE"
    ""
    ${ARGN}
)

    set(line_codegen_dir ${CMAKE_CURRENT_BINARY_DIR}/${_TARGET}_gencode)
    add_custom_target(
        line-codegen-${_TARGET}
        COMMAND ${Python_EXECUTABLE} -m line_protocol.codegen ${_NETWORK} --node ${_NODE} --output ${line_codegen_dir}
        DEPENDS ${_NETWORK}
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
        BYPRODUCTS ${line_codegen_dir}/line_api.c ${line_codegen_dir}/line_api.h
    )
    add_library(${_TARGET} INTERFACE)
    target_sources(${_TARGET} INTERFACE ${line_codegen_dir}/line_api.c)
    target_include_directories(${_TARGET} INTERFACE ${line_codegen_dir})
    target_link_libraries(${_TARGET} INTERFACE line-protocol-sources line-protocol-api)
    if(${_ADAPTER})
        target_link_libraries(${_TARGET} INTERFACE line-protocol-adapter-sources)
    endif()
    add_dependencies(${_TARGET} line-codegen-${_TARGET})
endfunction()

if(LINE_PROTOCOL_BUILD_TESTS)
    enable_testing()
    include(FetchContent)
    include(GoogleTest)

    FetchContent_Declare(
        googletest
        GIT_REPOSITORY https://github.com/google/googletest.git
        GIT_TAG        release-1.12.0
    )
    FetchContent_Declare(
        fff
        GIT_REPOSITORY https://github.com/meekrosoft/fff.git
        GIT_TAG        5111c61e1ef7848e3afd3550044a8cf4405f4199
    )

    FetchContent_MakeAvailable(googletest fff)
    add_subdirectory(tests)

    add_custom_target(
        coverage
        COMMAND ${Python_EXECUTABLE} -m gcovr --html-self-contained --html-details ${CMAKE_BINARY_DIR}/coverage.html
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    )

    add_custom_target(
        docs
        COMMAND ${Python_EXECUTABLE} -m sphinx -b html -E ${CMAKE_CURRENT_SOURCE_DIR}/docs ${CMAKE_CURRENT_SOURCE_DIR}/docs/_build
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    )
endif()
