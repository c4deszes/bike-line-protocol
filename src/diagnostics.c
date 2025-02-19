#include "line_diagnostics.h"
#include "line_transport.h"

#include <stdlib.h>

typedef struct {
    uint16_t request;
    LINE_Diag_ListenerCallback_t callback;
} diag_service_listener_entry_t;

typedef struct {
    uint16_t request;
    LINE_Diag_PublisherCallback_t callback;
} diag_service_publisher_entry_t;

static LINE_Diag_Config_t* diagnosticChannels[LINE_DIAG_CHANNEL_COUNT];
static diag_service_listener_entry_t diagServiceListeners[LINE_DIAG_CHANNEL_COUNT][LINE_DIAG_SERVICE_MAX_UNICAST_LISTENERS];
static uint8_t diagServiceListenerIndex[LINE_DIAG_CHANNEL_COUNT];
static diag_service_publisher_entry_t diagServicePublishers[LINE_DIAG_CHANNEL_COUNT][LINE_DIAG_SERVICE_MAX_UNICAST_PUBLISHERS];
static uint8_t diagServicePublisherIndex[LINE_DIAG_CHANNEL_COUNT];

void LINE_Diag_Init(uint8_t diag_channel, LINE_Diag_Config_t* diag_config) {
    diagnosticChannels[diag_channel] = diag_config;
}

void LINE_Diag_RegisterUnicastListener(uint8_t diag_channel, uint16_t request, LINE_Diag_ListenerCallback_t callback) {
    // TODO: validate index, inputs
    diagServiceListeners[diag_channel][diagServiceListenerIndex[diag_channel]].request = request;
    diagServiceListeners[diag_channel][diagServiceListenerIndex[diag_channel]].callback = callback;
    diagServiceListenerIndex[diag_channel]++;
}

void LINE_Diag_RegisterUnicastPublisher(uint8_t diag_channel, uint16_t request, LINE_Diag_PublisherCallback_t callback) {
    // TODO: validate index, inputs
    diagServicePublishers[diag_channel][diagServicePublisherIndex[diag_channel]].request = request;
    diagServicePublishers[diag_channel][diagServicePublisherIndex[diag_channel]].callback = callback;
    diagServicePublisherIndex[diag_channel]++;
}

bool LINE_Diag_RespondsTo(uint8_t transport_channel, uint16_t request) {
    for (uint8_t i = 0; i < LINE_DIAG_CHANNEL_COUNT; i++) {
        if (diagnosticChannels[i] != NULL && diagnosticChannels[i]->transport_channel == transport_channel) {
            uint8_t assignedAddress = diagnosticChannels[i]->address;
            if (request == LINE_DIAG_UNICAST_ID(LINE_DIAG_REQUEST_OP_STATUS, assignedAddress)) {
                return true;
            }
            else if (request == LINE_DIAG_UNICAST_ID(LINE_DIAG_REQUEST_POWER_STATUS, assignedAddress)) {
                return true;
            }
            else if (request == LINE_DIAG_UNICAST_ID(LINE_DIAG_REQUEST_SERIAL_NUMBER, assignedAddress)) {
                return true;
            }
            else if (request == LINE_DIAG_UNICAST_ID(LINE_DIAG_REQUEST_SW_NUMBER, assignedAddress)) {
                return true;
            }
            else {
                for (uint8_t j = 0; j < diagServicePublisherIndex[i]; j++) {
                    if (request == LINE_DIAG_UNICAST_ID(diagServicePublishers[i][j].request, assignedAddress)) {
                        return true;
                    }
                }
            }
        }
    }

    return false;
}

bool LINE_Diag_PrepareResponse(uint8_t transport_channel, uint16_t request, uint8_t* size, uint8_t* payload) {
    for (uint8_t i = 0; i < LINE_DIAG_CHANNEL_COUNT; i++) {
        if (diagnosticChannels[i] != NULL && diagnosticChannels[i]->transport_channel == transport_channel) {
            uint8_t assignedAddress = diagnosticChannels[transport_channel]->address;
            if (request == LINE_DIAG_UNICAST_ID(LINE_DIAG_REQUEST_OP_STATUS, assignedAddress)) {
                if (diagnosticChannels[transport_channel]->op_status == NULL) {
                    return false;
                }
                uint8_t status = diagnosticChannels[transport_channel]->op_status();
                *size = sizeof(uint8_t);
                payload[0] = status;
                return true;
            }
            else if (request == LINE_DIAG_UNICAST_ID(LINE_DIAG_REQUEST_POWER_STATUS, assignedAddress)) {
                if (diagnosticChannels[transport_channel]->power_status == NULL) {
                    return false;
                }
                LINE_Diag_PowerStatus_t* status = diagnosticChannels[transport_channel]->power_status();
                if (status == NULL) {
                    return false;
                }
                else {
                    *size = sizeof(LINE_Diag_PowerStatus_t);
                    payload[0] = status->U_measured;
                    payload[1] = (status->I_operating) & 0xFF;
                    payload[2] = (status->I_operating) >> 8;
                    payload[3] = status->I_sleep;
                    return true;
                }
            }
            else if (request == LINE_DIAG_UNICAST_ID(LINE_DIAG_REQUEST_SERIAL_NUMBER, assignedAddress)) {
                if (diagnosticChannels[transport_channel]->serial_number == NULL) {
                    return false;
                }
                uint32_t serial = diagnosticChannels[transport_channel]->serial_number();
                *size = sizeof(uint32_t);
                payload[0] = (uint8_t)(serial & 0xFF);
                payload[1] = (uint8_t)((serial >> 8) & 0xFF);
                payload[2] = (uint8_t)((serial >> 16) & 0xFF);
                payload[3] = (uint8_t)((serial >> 24) & 0xFF);
                return true;
            }
            else if (request == LINE_DIAG_UNICAST_ID(LINE_DIAG_REQUEST_SW_NUMBER, assignedAddress)) {
                if (diagnosticChannels[transport_channel]->software_version == NULL) {
                    return false;
                }
                LINE_Diag_SoftwareVersion_t* sw_number = diagnosticChannels[transport_channel]->software_version();
                if (sw_number == NULL) {
                    return false;
                }
                else {
                    *size = sizeof(LINE_Diag_SoftwareVersion_t);
                    payload[0] = sw_number->major;
                    payload[1] = sw_number->minor;
                    payload[2] = sw_number->patch;
                    payload[3] = sw_number->reserved;
                    return true;
                }
            }
            else if (assignedAddress != LINE_DIAG_UNICAST_UNASSIGNED_ID) {
                for (int j = 0; j < diagServicePublisherIndex[i]; j++) {
                    if (request == LINE_DIAG_UNICAST_ID(diagServicePublishers[i][j].request, assignedAddress)) {
                        return diagServicePublishers[i][j].callback(request, size, payload);
                    }
                }
            }
        }
    }
    return false;
}

bool LINE_Diag_ListensTo(uint8_t transport_channel, uint16_t request) {
    // TODO: implement
    return true;
}

void LINE_Diag_OnRequest(uint8_t transport_channel, uint16_t request, uint8_t size, uint8_t* payload) {
    for (int i=0; i < LINE_DIAG_CHANNEL_COUNT; i++) {
        if (diagnosticChannels[i] != NULL && diagnosticChannels[i]->transport_channel == transport_channel) {
            uint8_t assignedAddress = diagnosticChannels[i]->address;
            if (request == LINE_DIAG_REQUEST_WAKEUP) {
                if (diagnosticChannels[i]->on_wakeup != NULL) {
                    diagnosticChannels[i]->on_wakeup();
                }
            }
            else if (request == LINE_DIAG_REQUEST_IDLE) {
                if (diagnosticChannels[i]->on_idle != NULL) {
                    diagnosticChannels[i]->on_idle();
                }
            }
            else if (request == LINE_DIAG_REQUEST_SHUTDOWN) {
                if (diagnosticChannels[i]->on_shutdown != NULL) {
                    diagnosticChannels[i]->on_shutdown();
                }
            }
            else if (request == LINE_DIAG_REQUEST_CONDITIONAL_CHANGE_ADDRESS) {
                if (size == 5) {
                    uint32_t targetSerial = payload[0] | (((uint32_t)payload[1]) << 8) | (((uint32_t)payload[2]) << 16) | (((uint32_t)payload[3]) << 24);
                    if (diagnosticChannels[i]->serial_number != NULL) {
                        if (targetSerial == diagnosticChannels[i]->serial_number()) {
                            uint8_t oldAddress = assignedAddress;
                            // TODO: validate new address
                            diagnosticChannels[i]->address = payload[4];
                            if (diagnosticChannels[i]->on_conditional_change_address != NULL) {
                                diagnosticChannels[i]->on_conditional_change_address(oldAddress, payload[4]);
                            }
                        }
                        else if(payload[4] == assignedAddress) {
                            diagnosticChannels[i]->address = LINE_DIAG_UNICAST_UNASSIGNED_ID;
                            // TODO: callout unassign
                        }
                    }
                }
            }
            else if (assignedAddress != LINE_DIAG_UNICAST_UNASSIGNED_ID) {
                for (int j = 0; j < diagServiceListenerIndex; j++) {
                    if (request == LINE_DIAG_UNICAST_ID(diagServiceListeners[i][j].request, assignedAddress)) {
                        diagServiceListeners[i][j].callback(request, size, payload);
                        break;
                    }
                }
            }
        }
    }
}
