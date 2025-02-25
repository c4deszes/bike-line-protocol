#include "line_transport.h"
#include "line_transport_priv.h"

/* Transport layer configuration */
#if LINE_TRANSPORT_CHANNEL_COUNT < 1
#error "LINE Protocol transport layer requires at least one channel"
#endif

#if LINE_TRANSPORT_RX_BUFFER_SIZE < LINE_TRANSPORT_DATA_MAX
#warning "LINE Protocol transport layer has limited receive buffer size"
#endif

/* Transport layer constants */

#define LINE_REQUEST_TIMEOUT 5
#define LINE_DATA_TIMEOUT 5

typedef enum {
    protocol_state_wait_sync,
    protocol_state_wait_request_msb,
    protocol_state_wait_request_lsb,
    protocol_state_wait_size,
    protocol_state_wait_data,
    protocol_state_wait_data_checksum
} protocol_state;

typedef struct {
    bool isOneWire;

    protocol_state currentState;

    uint32_t timestamp;
    uint32_t lastReceived;

    uint16_t currentRequest;
    bool currentResponding;
    uint8_t currentSize;
    uint8_t currentSizeCounter;
    uint8_t calculatedChecksum;
    uint8_t rxBuffer[LINE_TRANSPORT_RX_BUFFER_SIZE];
    uint8_t outSize;
    uint8_t txBuffer[LINE_TRANSPORT_TX_BUFFER_SIZE];
} channel_state;

static channel_state channels[LINE_TRANSPORT_CHANNEL_COUNT];

void LINE_Transport_Init(uint8_t channel, bool one_wire) {
    if (channel >= LINE_TRANSPORT_CHANNEL_COUNT) return;
    channels[channel].currentState = protocol_state_wait_sync;
    channels[channel].lastReceived = 0;
    channels[channel].timestamp = 0;
    channels[channel].isOneWire = one_wire;
}

void LINE_Transport_Update(uint8_t channel, uint8_t elapsed) {
    if (channel >= LINE_TRANSPORT_CHANNEL_COUNT) return;
    channel_state *ch = &channels[channel];
    
    ch->timestamp += elapsed;

    if (ch->currentState == protocol_state_wait_request_msb ||
        ch->currentState == protocol_state_wait_request_lsb) {
        if (ch->timestamp - ch->lastReceived > LINE_REQUEST_TIMEOUT) {
            ch->currentState = protocol_state_wait_sync;
            LINE_Transport_OnError(channel, ch->currentResponding, ch->currentRequest, line_transport_error_timeout);
        }
    }
    else if(ch->currentState == protocol_state_wait_size ||
            ch->currentState == protocol_state_wait_data ||
            ch->currentState == protocol_state_wait_data_checksum) {
        if (ch->timestamp - ch->lastReceived > LINE_DATA_TIMEOUT) {
            ch->currentState = protocol_state_wait_sync;
            LINE_Transport_OnError(channel, ch->currentResponding, ch->currentRequest, line_transport_error_timeout);
        }
    }
}

void LINE_Transport_Receive(uint8_t channel, uint8_t data) {
    if (channel >= LINE_TRANSPORT_CHANNEL_COUNT) return;
    channel_state *ch = &channels[channel];
    ch->lastReceived = ch->timestamp;

    if (ch->currentState == protocol_state_wait_sync && data == LINE_SYNC_BYTE) {
        ch->currentState = protocol_state_wait_request_msb;
    }
    else if(ch->currentState == protocol_state_wait_request_msb) {
        ch->currentRequest = (data << 8);
        ch->currentState = protocol_state_wait_request_lsb;
    }
    else if(ch->currentState == protocol_state_wait_request_lsb) {
        ch->currentRequest |= data;
        uint16_t calculatedParity = request_code(ch->currentRequest & LINE_REQUEST_PARITY_MASK);
        if (ch->currentRequest == calculatedParity) {
            ch->currentRequest = (ch->currentRequest & (LINE_REQUEST_PARITY_MASK));
            ch->currentResponding = LINE_Transport_RespondsTo(channel, ch->currentRequest);

            if (ch->currentResponding) {
                bool willRespond = LINE_Transport_PrepareResponse(channel, ch->currentRequest, &ch->outSize, ch->txBuffer);
                if (willRespond) {
                    uint8_t checksum = ch->outSize + LINE_DATA_CHECKSUM_OFFSET;
                    for (int i = 0; i < ch->outSize; i++) {
                        checksum += ch->txBuffer[i];
                    }

                    if (!ch->isOneWire && ch->currentResponding) {
                        ch->currentState = protocol_state_wait_sync;
                        LINE_Transport_WriteResponse(channel, ch->outSize, ch->txBuffer, checksum);
                    }
                    else if(ch->currentResponding) {
                        ch->currentState = protocol_state_wait_size;
                        LINE_Transport_WriteResponse(channel, ch->outSize, ch->txBuffer, checksum);
                    }
                }
                else {
                    ch->currentState = protocol_state_wait_size;
                }
            }
            else {
                ch->currentState = protocol_state_wait_size;
            }
        }
        else {
            ch->currentState = protocol_state_wait_sync;
            LINE_Transport_OnError(channel, false, ch->currentRequest, line_transport_error_header_invalid);
        }
    }
    else if(ch->currentState == protocol_state_wait_size) {
        ch->currentSize = data;
        ch->currentSizeCounter = 0;
        ch->calculatedChecksum = data + LINE_DATA_CHECKSUM_OFFSET;

        if(ch->currentSize == 0) {
            ch->currentState = protocol_state_wait_data_checksum;
        }
        else {
            ch->currentState = protocol_state_wait_data;
        }
    }
    else if(ch->currentState == protocol_state_wait_data) {
        if (ch->currentSize <= LINE_TRANSPORT_RX_BUFFER_SIZE) {
            ch->rxBuffer[ch->currentSizeCounter] = data;
            ch->calculatedChecksum += data;
            ch->currentSizeCounter++;
        }

        if (ch->currentSizeCounter >= ch->currentSize) {
            ch->currentState = protocol_state_wait_data_checksum;
        }
    }
    else if(ch->currentState == protocol_state_wait_data_checksum) {
        uint8_t checksum = data;

        if (ch->currentSize > LINE_TRANSPORT_RX_BUFFER_SIZE) {
            ch->currentState = protocol_state_wait_sync;
            LINE_Transport_OnError(channel, ch->currentResponding, ch->currentRequest, line_transport_error_partial_data);
        }
        else if (checksum == ch->calculatedChecksum) {
            ch->currentState = protocol_state_wait_sync;
            LINE_Transport_OnData(channel, ch->currentResponding, ch->currentRequest, ch->currentSize, ch->rxBuffer);
        }
        else {
            ch->currentState = protocol_state_wait_sync;
            LINE_Transport_OnError(channel, ch->currentResponding, ch->currentRequest, line_transport_error_data_invalid);
        }
    }
}

void LINE_Transport_Request(uint8_t channel, uint16_t request) {
    if (channel >= LINE_TRANSPORT_CHANNEL_COUNT) return;
    channel_state *ch = &channels[channel];
    if (ch->currentState != protocol_state_wait_sync) {
        return;
    }

    LINE_Transport_WriteRequest(channel, request_code(request));

    if (!ch->isOneWire) {
        ch->currentState = protocol_state_wait_size;
    }
}


static void _no_handler(uint8_t channel, uint16_t request) {
    // Empty function for not implemented callbacks
}

void LINE_Transport_WriteRequest(uint8_t channel, uint16_t request) __attribute__((weak, alias("_no_handler")));

static void _no_handler1(uint8_t channel, bool response, uint16_t request, line_transport_error error_type) {
    // Empty function for not implemented callbacks
}

void LINE_Transport_OnError(uint8_t channel, bool response, uint16_t request, line_transport_error error_type) __attribute__((weak, alias("_no_handler1")));

static void _no_handler2(uint8_t channel, bool response, uint16_t request, uint8_t size, uint8_t* payload) {
    // Empty function for not implemented callbacks
}

void LINE_Transport_OnData(uint8_t channel, bool response, uint16_t request, uint8_t size, uint8_t* payload) __attribute__((weak, alias("_no_handler2")));
