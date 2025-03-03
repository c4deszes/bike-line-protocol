/**
 * @file line_tester.h
 * @author Eszes Balazs
 * @brief Test helper macros for generating frames and requests
 * @version 0.1
 * @date 2025-03-02
 * 
 * @copyright Copyright (c) 2025
 * 
 * This file contains helper macros for generating frames and requests for testing purposes.
 * Should only be included in tests for the LINE protocol library and protocol extensions.
 */
#if !defined(LINE_LINE_TESTER_H_)
#define LINE_LINE_TESTER_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdint.h>
#include "line_transport.h"
#include "line_transport_priv.h"

/*
 * @brief Generates an array of bytes containing a frame with the given id and payload
 * @example BUILD_FRAME(frame, 0x10A4, 0x01, 0x02, 0x03);
 */
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

/*
 * @brief Generates an array of bytes containing a request with the given id
 * @example BUILD_REQUEST(request, 0x10A4);
 */
#define BUILD_REQUEST(array, id) \
    uint16_t array##_req_code = request_code(id); \
    uint8_t array[] = { \
        LINE_SYNC_BYTE, \
        (uint8_t)((array##_req_code >> 8) & 0xFF), \
        (uint8_t)(array##_req_code & 0xFF) \
    };

#ifdef __cplusplus
}
#endif

#endif // LINE_LINE_TESTER_H_
