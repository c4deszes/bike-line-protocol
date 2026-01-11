function(add_test TARGET)
    target_compile_options(${TARGET} PRIVATE $<$<COMPILE_LANGUAGE:C>:--coverage>)
    target_link_libraries(${TARGET} PRIVATE line-protocol-api)
    target_link_libraries(${TARGET} PRIVATE gtest fff gcov)
    gtest_discover_tests(${TARGET} DISCOVERY_MODE POST_BUILD)
endfunction()

################################################################################
# Coverage
################################################################################
add_custom_target(coverage_report
    COMMAND ${CMAKE_COMMAND} -E echo "Generating coverage report..."
    COMMAND ${CMAKE_COMMAND} -E make_directory coverage
    COMMAND gcovr -r ${CMAKE_SOURCE_DIR} --cobertura coverage/coverage.xml
                                         --html coverage/coverage.html
                                         --html-details coverage/coverage_details.html
)

################################################################################
# Test targets
################################################################################

add_executable(test_TransportReceive_Single EXCLUDE_FROM_ALL)
target_sources(test_TransportReceive_Single PRIVATE
    ../src/transport.c
    transport/test_TransportReceive_Single.cpp
)
add_test(test_TransportReceive_Single)

add_executable(test_TransportReceive_Multiple EXCLUDE_FROM_ALL)
target_include_directories(test_TransportReceive_Multiple PRIVATE transport/multiple)
target_sources(test_TransportReceive_Multiple PRIVATE
    ../src/transport.c
    transport/multiple/test_TransportReceive_Multiple.cpp
)
add_test(test_TransportReceive_Multiple)

add_executable(test_TransportReceive_BufSize EXCLUDE_FROM_ALL)
target_include_directories(test_TransportReceive_BufSize PRIVATE transport/bufsize)
target_sources(test_TransportReceive_BufSize PRIVATE
    ../src/transport.c
    transport/bufsize/test_TransportReceive_BufSize.cpp
)
add_test(test_TransportReceive_BufSize)

################################################################################

line_codegen(
    TARGET DiagnosticsSingleNode
    CONFIG diagnostics/single_node_codegen.json
    ADAPTER
)
add_executable(test_Diagnostics_SingleNode EXCLUDE_FROM_ALL)
target_sources(test_Diagnostics_SingleNode PRIVATE
    diagnostics/test_Diagnostics_SingleNode.cpp
)
target_link_libraries(test_Diagnostics_SingleNode PRIVATE DiagnosticsSingleNode)
add_test(test_Diagnostics_SingleNode)

line_codegen(
    TARGET DiagnosticsMultiNode
    CONFIG diagnostics/multi_node_codegen.json
    ADAPTER
)
add_executable(test_Diagnostics_MultiNode EXCLUDE_FROM_ALL)
target_sources(test_Diagnostics_MultiNode PRIVATE
    diagnostics/test_Diagnostics_MultiNode.cpp
)
target_link_libraries(test_Diagnostics_MultiNode PRIVATE DiagnosticsMultiNode)
add_test(test_Diagnostics_MultiNode)

################################################################################

line_codegen(
    TARGET ApplicationBytePackingSingleNode
    CONFIG application/single_node_codegen.json
    ADAPTER
)
add_executable(test_Application_BytePacking EXCLUDE_FROM_ALL)
target_sources(test_Application_BytePacking PRIVATE
    application/test_Application_BytePacking.cpp
)
target_link_libraries(test_Application_BytePacking PRIVATE ApplicationBytePackingSingleNode)
add_test(test_Application_BytePacking)

# add_executable(test_ApplicationInterface EXCLUDE_FROM_ALL)
# target_sources(test_ApplicationInterface PRIVATE
#     ../src/application.c
#     test_ApplicationInterface.cpp
# )
# add_test(test_ApplicationInterface)

# add_executable(test_ApplicationSignals EXCLUDE_FROM_ALL)
# target_sources(test_ApplicationSignals PRIVATE
#     test_ApplicationSignals.cpp
# )
# add_test(test_ApplicationSignals)
# target_link_libraries(test_ApplicationSignals PRIVATE test_network)
