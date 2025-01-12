#if !defined(LINE_LINE_TESTER_H_)
#define LINE_LINE_TESTER_H_

#include <stdint.h>
#include "line_transport.h"
#include "line_transport_priv.h"

#define BUILD_FRAME(array, id, ...) \
    uint8_t array##_frame[] = {__VA_ARGS__}; \
    uint8_t array##_size = sizeof(array##_frame); \
    uint16_t array##_req_code = request_code(id); \
    uint8_t array[] = { \
        LINE_SYNC_BYTE, \
        (uint8_t)((array##_req_code >> 8) & 0xFF), \
        (uint8_t)(array##_req_code & 0xFF), \
        array##_size, \
        __VA_ARGS__, \
        calculate_checksum(array##_frame, array##_size) \
    };

#define BUILD_REQUEST(array, id) \
    uint16_t array##_req_code = request_code(id); \
    uint8_t array[] = { \
        LINE_SYNC_BYTE, \
        (uint8_t)((array##_req_code >> 8) & 0xFF), \
        (uint8_t)(array##_req_code & 0xFF) \
    };

#endif // LINE_LINE_TESTER_H_
