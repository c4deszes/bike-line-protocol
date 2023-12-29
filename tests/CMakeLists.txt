function(add_test TARGET)
    target_compile_options(${TARGET} PRIVATE $<$<COMPILE_LANGUAGE:C>:--coverage>)
    target_link_libraries(${TARGET} PRIVATE line-protocol-api)
    target_link_libraries(${TARGET} PRIVATE gtest fff gcov)
    gtest_discover_tests(${TARGET} DISCOVERY_MODE POST_BUILD)
endfunction()

add_executable(test_TransportReceive EXCLUDE_FROM_ALL)
target_sources(test_TransportReceive PRIVATE
    ../src/transport.c
    test_TransportReceive.cpp
)
add_test(test_TransportReceive)

add_executable(test_ApplicationInterface EXCLUDE_FROM_ALL)
target_sources(test_ApplicationInterface PRIVATE
    ../src/application.c
    test_ApplicationInterface.cpp
)
add_test(test_ApplicationInterface)

line_codegen(
    TARGET test_network
    NETWORK test_network.json
    NODE Peripheral_1
    ADAPTER
)
add_executable(test_ApplicationSignals EXCLUDE_FROM_ALL)
target_sources(test_ApplicationSignals PRIVATE
    test_ApplicationSignals.cpp
)
add_test(test_ApplicationSignals)
target_link_libraries(test_ApplicationSignals PRIVATE test_network)
