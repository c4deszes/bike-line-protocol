cmake_minimum_required(VERSION 3.20)
project(line-protocol LANGUAGES C CXX)

enable_testing()
set(CMAKE_EXPORT_COMPILE_COMMANDS TRUE)

find_package(Python REQUIRED)

include(GoogleTest)
add_subdirectory(lib/googletest)
add_subdirectory(lib/fff)

# Target
add_library(line-protocol-api INTERFACE)
target_include_directories(line-protocol-api INTERFACE
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

add_library(line-protocol-sources INTERFACE)
target_sources(line-protocol-sources INTERFACE
    src/transport.c
    src/application.c
    src/diagnostics.c
)

add_library(line-protocol-adapter-sources INTERFACE)
target_sources(line-protocol-sources INTERFACE
    src/app_adapter.c
)

add_library(line-protocol-lib STATIC EXCLUDE_FROM_ALL)
target_link_libraries(line-protocol-lib PRIVATE line-protocol-sources)
target_link_libraries(line-protocol-lib PUBLIC line-protocol-api)

function(line_codegen)

cmake_parse_arguments(
    ""
    ""
    "TARGET;NETWORK;NODE"
    ""
    ${ARGN}
)

    set(line_codegen_dir ${CMAKE_CURRENT_BINARY_DIR}/${_TARGET}_gencode)
    add_custom_target(
        line-codegen-${_TARGET}
        COMMAND ${Python_EXECUTABLE} -m line_protocol.codegen ${_NETWORK} --node ${_NODE} --output ${line_codegen_dir}
        WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
        BYPRODUCTS ${line_codegen_dir}/line_api.c ${line_codegen_dir}/line_api.h
    )
    add_library(${_TARGET} INTERFACE)
    target_sources(${_TARGET} INTERFACE ${line_codegen_dir}/line_api.c)
    target_include_directories(${_TARGET} INTERFACE ${line_codegen_dir})
    add_dependencies(${_TARGET} line-codegen-${_TARGET})
endfunction()

# Testing
function(add_test TARGET)
    target_compile_options(${TARGET} PRIVATE $<$<COMPILE_LANGUAGE:C>:--coverage>)
    target_link_libraries(${TARGET} PRIVATE line-protocol-api)
    target_link_libraries(${TARGET} PRIVATE gtest fff gcov)
    gtest_discover_tests(${TARGET} DISCOVERY_MODE POST_BUILD)
endfunction()

add_executable(test_TransportReceive EXCLUDE_FROM_ALL)
target_sources(test_TransportReceive PRIVATE
    src/transport.c
    tests/test_TransportReceive.cpp
)
add_test(test_TransportReceive)

add_executable(test_ApplicationInterface EXCLUDE_FROM_ALL)
target_sources(test_ApplicationInterface PRIVATE
    src/application.c
    tests/test_ApplicationInterface.cpp
)
add_test(test_ApplicationInterface)

line_codegen(
    TARGET test_network
    NETWORK tests/test_network.json
    NODE Peripheral_1
)
add_executable(test_ApplicationSignals EXCLUDE_FROM_ALL)
target_sources(test_ApplicationSignals PRIVATE
    src/application.c
    tests/test_ApplicationSignals.cpp
)
add_test(test_ApplicationSignals)
target_link_libraries(test_ApplicationSignals PRIVATE test_network)

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
