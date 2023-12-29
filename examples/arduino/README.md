# Arduino example

## Building

1. Run code generation `line-codegen network.json --output . --node Arduino`
2. Run build `arduino-cli compile -b SparkFun:avr:promicro --board-options cpu=16MHzatmega32U4 --library ../.. --clean`

## Uploading

1. `arduino-cli.exe compile -b SparkFun:avr:promicro --board-options cpu=16MHzatmega32U4 --library C:\Workspace\bicycle\protocol --clean --upload --port COM11`
