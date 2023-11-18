#include "line_transport.h"

typedef enum {
    protocol_state_wait_sync,
    protocol_state_wait_request_msb,
    protocol_state_wait_request_lsb,
    protocol_state_wait_size,
    protocol_state_wait_data,
    protocol_state_wait_data_checksum
} protocol_state;

static uint32_t timestamp;

static bool isOneWire;
static uint32_t lastReceived;
static protocol_state currentState;
static uint16_t currentRequest;
static bool currentResponding;
static uint8_t currentSize;
static uint8_t currentSizeCounter;
static uint8_t calculatedChecksum;
static uint8_t dataBuffer[255];

static uint8_t outSize;
static uint8_t outData[255];

static uint16_t request_code(uint16_t data) {
    // TODO: should return the whole request code
    uint8_t parity1 = 0;
    uint16_t tempData = data;
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

void LINE_Transport_Init(bool one_wire) {
    currentState = protocol_state_wait_sync;
    timestamp = 0;
    lastReceived = 0;
    isOneWire = one_wire;
}

void LINE_Transport_Update(uint8_t elapsed) {
    timestamp += elapsed;

    if (currentState == protocol_state_wait_request_msb ||
        currentState == protocol_state_wait_request_lsb) {
        if (timestamp - lastReceived > LINE_REQUEST_TIMEOUT) {
            // TODO: error?
            LINE_Transport_OnError(currentResponding, currentRequest, line_transport_error_timeout);
            currentState = protocol_state_wait_sync;
        }
    }
    else if(currentState == protocol_state_wait_size ||
            currentSize == protocol_state_wait_data ||
            currentState == protocol_state_wait_data_checksum) {
        if (timestamp - lastReceived > LINE_DATA_TIMEOUT) {
            LINE_Transport_OnError(currentResponding, currentRequest, line_transport_error_timeout);
            currentState = protocol_state_wait_sync;
        }
    }
}

void LINE_Transport_Receive(uint8_t data) {
    lastReceived = timestamp;

    if (currentState == protocol_state_wait_sync && data == LINE_SYNC_BYTE) {
        currentState = protocol_state_wait_request_msb;
    }
    else if(currentState == protocol_state_wait_request_msb) {
        currentRequest = (data << 8);

        currentState = protocol_state_wait_request_lsb;
    }
    else if(currentState == protocol_state_wait_request_lsb) {
        currentRequest |= data;

        uint16_t calculatedParity = request_code(currentRequest & LINE_REQUEST_PARITY_MASK);
        if (currentRequest == calculatedParity) {
            currentRequest = (currentRequest & (LINE_REQUEST_PARITY_MASK));
            currentResponding = LINE_Transport_RespondsTo(currentRequest);

            if (currentResponding) {
                LINE_Transport_PrepareResponse(currentRequest, &outSize, outData);
                uint8_t checksum = outSize + LINE_DATA_CHECKSUM_OFFSET;
                for (int i = 0; i<outSize;i++) {
                    checksum += outData[i];
                }

                if (!isOneWire && currentResponding) {
                    // In Two-wire mode when responding
                    LINE_Transport_WriteResponse(outSize, outData, checksum);
                    currentState = protocol_state_wait_sync;
                }
                else if(currentResponding) {
                    // In One-wire mode it receives the data sent out so the statemachine has to continue
                    currentState = protocol_state_wait_size;
                    LINE_Transport_WriteResponse(outSize, outData, checksum);
                }
            }
            else {
                currentState = protocol_state_wait_size;
            }
        }
        else {
            LINE_Transport_OnError(false, currentRequest, line_transport_error_header_invalid);
            currentState = protocol_state_wait_sync;
        }
    }
    else if(currentState == protocol_state_wait_size) {
        currentSize = data;
        currentSizeCounter = 0;
        calculatedChecksum = data + LINE_DATA_CHECKSUM_OFFSET;

        if(currentSize == 0) {
            currentState = protocol_state_wait_data_checksum;
        }
        else {
            currentState = protocol_state_wait_data;
        }
    }
    else if(currentState == protocol_state_wait_data) {
        dataBuffer[currentSizeCounter] = data;
        calculatedChecksum += data;
        currentSizeCounter++;

        if (currentSizeCounter >= currentSize) {
            currentState = protocol_state_wait_data_checksum;
        }
    }
    else if(currentState == protocol_state_wait_data_checksum) {
        uint8_t checksum = data;

        // if check
        if (checksum == calculatedChecksum) {
            // TODO: call with null pointer if no data was sent
            LINE_Transport_OnData(currentResponding, currentRequest, currentSize, dataBuffer);
            currentState = protocol_state_wait_sync;
        }
        else {
            LINE_Transport_OnError(currentResponding, currentRequest, line_transport_error_data_invalid);
            currentState = protocol_state_wait_sync;
        }
    }
}

static void _no_handler(void) {
    // Empty function for not implemented callbacks
}

void LINE_Transport_OnError(bool response, uint16_t request, line_transport_error error_type) __attribute__((weak, alias("_no_handler")));

void LINE_Transport_OnData(bool response, uint16_t request, uint8_t size, uint8_t* payload) __attribute__((weak, alias("_no_handler")));
