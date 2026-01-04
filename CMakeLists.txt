cmake_minimum_required(VERSION 3.20)

file(READ "${CMAKE_CURRENT_SOURCE_DIR}/library.properties" LIBRARY_PROPERTIES_CONTENT)
string(REGEX MATCH "version=([^\n\r]+)" _ ${LIBRARY_PROPERTIES_CONTENT})
set(LIBRARY_VERSION "${CMAKE_MATCH_1}")

project(
    line-protocol
    VERSION ${LIBRARY_VERSION}
    LANGUAGES C CXX)

################################################################################
# Options
################################################################################
option(LINE_PROTOCOL_BUILD_TESTS "Enables library test cases" OFF)
option(LINE_PROTOCOL_BUILD_DOCS "Enables documentation generation" OFF)

find_package(Python REQUIRED)

################################################################################
# Sources
################################################################################
add_library(line-protocol-api INTERFACE)
target_include_directories(line-protocol-api INTERFACE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

add_library(line-protocol-sources INTERFACE)
target_sources(line-protocol-sources INTERFACE
    ${CMAKE_CURRENT_SOURCE_DIR}/src/transport.c
    ${CMAKE_CURRENT_SOURCE_DIR}/src/diagnostics.c
)

add_library(line-protocol-adapter-sources INTERFACE)
target_sources(line-protocol-adapter-sources INTERFACE
    ${CMAKE_CURRENT_SOURCE_DIR}/src/app_adapter.c
)

################################################################################
# Functions
################################################################################

#[=======================================================================[.rst:
LINE protocol code generation
=============================

This function provides a way to generate the LINE protocol API
header and source files from the Python code generator.

.. command:: line_codegen

  Generate the LINE protocol API header and source files from the Python code generator::

    line_codegen([ADAPTER]
                 [TARGET target]
                 [CONFIG config]
    )

  ``line_codegen()`` will collect all necessary information and generate the
  required files in the specified output directory.

  The options are:

    - ``ADAPTER``: If specified, the generated code will include the adapter
        sources. This is useful if you want to use the LINE protocol with an
        adapter.

    - ``TARGET``: The name of the target to create. This is used to create the
        target name for the generated code. If not specified, the target name
        will be derived from the current directory name.

    - ``CONFIG``: The configuration to use for the code generation. This is
        passed to the Python code generator. If not specified, the default
        configuration will be used.

    If specified, the parameter is passed along with ``--junitxml=<test name>``
    to test executable. The actual file name is the same as the test target,
    including prefix and suffix.

#]=======================================================================]
function(line_codegen)

cmake_parse_arguments(
    ""
    "ADAPTER"
    "TARGET;CONFIG"
    ""
    ${ARGN}
)

    set(line_codegen_dir ${CMAKE_CURRENT_BINARY_DIR}/${_TARGET}_gencode)
    add_custom_target(
        line-codegen-${_TARGET}
        COMMAND ${Python_EXECUTABLE} -m line_protocol.codegen ${_CONFIG} --output ${line_codegen_dir}
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

################################################################################
# Testing
################################################################################
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
endif()

################################################################################
# Documentation
################################################################################
if(LINE_PROTOCOL_BUILD_DOCS)
    add_subdirectory(docs)
endif()
