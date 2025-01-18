#if !defined(LINE_LINE_TRANSPORT_PRIV_H_)
#define LINE_LINE_TRANSPORT_PRIV_H_

#include <stdint.h>

#define LINE_TRANSPORT_DATA_MAX 255

#define LINE_SYNC_BYTE 0x55
#define LINE_REQUEST_PARITY_MASK 0x3FFF
#define LINE_REQUEST_PARITY_POS 14
#define LINE_DATA_CHECKSUM_OFFSET 0xA3

static uint16_t request_code(uint16_t data) {
    uint8_t parity1 = 0;
    uint16_t tempData = data;
    // TODO: potentially wrong result if data goes outside of the 14bit range
    while (tempData != 0) {
        parity1 ^= (tempData & 1);
        tempData >>= 1;
    }

    uint8_t parity2 = 0;
    tempData = data;
    for (int i = 0; i < 6; i++) {
        parity2 ^= (tempData & 1);
        tempData >>= 2;
    }

    return (((parity1 << 1) | parity2) << LINE_REQUEST_PARITY_POS) | data;
}

static uint8_t calculate_checksum(uint8_t* data, uint8_t size) {
    uint8_t checksum = size;
    for (int i = 0; i < size; i++) {
        checksum += data[i];
    }
    checksum += LINE_DATA_CHECKSUM_OFFSET;
    return checksum;
}

#endif // LINE_LINE_TRANSPORT_PRIV_H_
