/**
 * @file line_transport_priv.h
 * @author Eszes Balazs
 * @brief Private functions for the LINE Transport protocol
 * @version 0.1
 * @date 2025-03-02
 * 
 * @copyright Copyright (c) 2025
 * 
 * This file contains the private functions for the LINE Transport protocol, should not be included
 * in any public header or outside this library.
 */
#if !defined(LINE_LINE_TRANSPORT_PRIV_H_)
#define LINE_LINE_TRANSPORT_PRIV_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdint.h>

#define LINE_TRANSPORT_DATA_MAX 255

#define LINE_SYNC_BYTE 0x55
#define LINE_REQUEST_PARITY_MASK 0x3FFF
#define LINE_REQUEST_PARITY_POS 14
#define LINE_DATA_CHECKSUM_OFFSET 0xA3

/**
 * @brief Calculates the request code with parity bits for the given request identifier
 * 
 * @param request_id Request identifier 
 * @return uint16_t Request code with parity bits
 */
static uint16_t request_code(uint16_t request_id) {
    uint8_t parity1 = 0;
    uint16_t tempData = request_id;
    // TODO: potentially wrong result if request_id goes outside of the 14bit range
    while (tempData != 0) {
        parity1 ^= (tempData & 1);
        tempData >>= 1;
    }

    uint8_t parity2 = 0;
    tempData = request_id;
    for (int i = 0; i < 6; i++) {
        parity2 ^= (tempData & 1);
        tempData >>= 2;
    }

    return (((parity1 << 1) | parity2) << LINE_REQUEST_PARITY_POS) | request_id;
}

/**
 * @brief Calculates the checksum for the given payload
 * 
 * @param data Payload data
 * @param size Payload size
 * @return uint8_t Checksum value
 */
static uint8_t calculate_checksum(uint8_t* data, uint8_t size) {
    uint8_t checksum = size;
    for (int i = 0; i < size; i++) {
        // TODO: either ignore overflow to change it to manually wrap around
        checksum += data[i];
    }
    checksum += LINE_DATA_CHECKSUM_OFFSET;
    return checksum;
}

#ifdef __cplusplus
}
#endif

#endif // LINE_LINE_TRANSPORT_PRIV_H_
