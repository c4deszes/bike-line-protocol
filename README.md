# LINE protocol

> LINE is a bus type protocol that uses a single controller, it's based on the LIN protocol used in
> automotive products and extends the frame length and number of frames.

## Usage

The project includes a CMake based environment that can be included as a subproject. A function call is used to instantiate the library in a way
that's unique to the application.

```cmake
include(tools/cmake/CPM.cmake)
CPMAddPackage("gh:c4deszes/bike-line-protocol#master")

line_codegen(TARGET protocol-stack
             CONFIG config
             ADAPTER
)

add_executable(MyApp src/main.c)
target_link_libraries(MyApp PUBLIC protocol-stack)
```

A code generation configuration is required, a single instance multiple
network definitions and multiple nodes can be used.

```json
{
    "Network": {
        "channel": 0,
        "rxBufferSize": 128,
        "txBufferSize": 128,
        "oneWire": true,
        "network": "multi_node_network.json",
        "nodes": {
            "Peripheral1": {
                "enabled": true,
                "diagnostics": {
                    "channel": 0,
                    "enabled": true,
                    "initAddress": true
                }
            },
            "Peripheral2": {
                "enabled": true,
                "diagnostics": {
                    "channel": 1,
                    "enabled": true,
                    "initAddress": true
                }
            }
        }
    }
}
```

## Building

The library only has interface and test targets, run the C library tests using
`cmake --workflow --preset workflow-test`.

Documentation is built using Sphinx with doxygen, that can be generated using
cmake as well by running `cmake --workflow --preset workflow-docs`.
