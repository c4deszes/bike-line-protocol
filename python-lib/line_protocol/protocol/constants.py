
LINE_SYNC_BYTE = 0x55
LINE_REQUEST_PARITY_MASK = 0x3FFF
LINE_REQUEST_PARITY_POS = 14
LINE_DATA_CHECKSUM_OFFSET = 0xA3

LINE_REQUEST_TIMEOUT = 0.100
LINE_DATA_TIMEOUT = 0.100

# Diagnostic codes
LINE_DIAG_REQUEST_WAKEUP = 0x0000
LINE_DIAG_REQUEST_SLEEP = 0x0100
LINE_DIAG_REQUEST_SHUTDOWN = 0x0101

LINE_DIAG_REQUEST_OP_STATUS = 0x200
LINE_DIAG_REQUEST_POWER_STATUS = 0x210
LINE_DIAG_REQUEST_SERIAL_NUMBER = 0x220
LINE_DIAG_REQUEST_SW_NUMBER = 0x230

LINE_DIAG_OP_STATUS_OK = 0
LINE_DIAG_OP_STATUS_WARN = 1
LINE_DIAG_OP_STATUS_ERROR = 2

LINE_DIAG_POWER_STATUS_VOLTAGE_OK = 0
LINE_DIAG_POWER_STATUS_VOLTAGE_LOW = 1
LINE_DIAG_POWER_STATUS_VOLTAGE_HIGH = 2
LINE_DIAG_POWER_STATUS_BOD_NONE = 0
LINE_DIAG_POWER_STATUS_BOD_DETECTED = 1
