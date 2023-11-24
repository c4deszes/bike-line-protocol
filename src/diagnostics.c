#include "line_diagnostics.h"

uint8_t assignedAddress = LINE_DIAG_UNICAST_UNASSIGNED_ID;

void LINE_Diag_Init(uint8_t diag_address) {
    assignedAddress = diag_address;
}

bool LINE_Diag_RespondsTo(uint16_t request) {
    if (assignedAddress == LINE_DIAG_UNICAST_UNASSIGNED_ID) {
        return false;
    }

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

    return false;
}

bool LINE_Diag_PrepareResponse(uint16_t request, uint8_t* size, uint8_t* payload) {
    if (request == LINE_DIAG_UNICAST_ID(LINE_DIAG_REQUEST_OP_STATUS, assignedAddress)) {
        uint8_t status = LINE_Diag_GetOperationStatus();
        *size = sizeof(uint8_t);
        payload[0] = status;
        return true;
    }
    else if (request == LINE_DIAG_UNICAST_ID(LINE_DIAG_REQUEST_POWER_STATUS, assignedAddress)) {
        LINE_Diag_PowerStatus_t* status = LINE_Diag_GetPowerStatus();
        *size = sizeof(LINE_Diag_PowerStatus_t);
        payload[0] = status->U_status;
        payload[1] = status->BOD_status;
        payload[2] = status->I_operating;
        payload[3] = status->I_sleep;
        return true;
    }
    else if (request == LINE_DIAG_UNICAST_ID(LINE_DIAG_REQUEST_SERIAL_NUMBER, assignedAddress)) {
        uint32_t serial = LINE_Diag_GetSerialNumber();
        *size = sizeof(uint32_t);
        payload[0] = (uint8_t)(serial & 0xFF);
        payload[1] = (uint8_t)((serial >> 8) & 0xFF);
        payload[2] = (uint8_t)((serial >> 16) & 0xFF);
        payload[3] = (uint8_t)((serial >> 24) & 0xFF);
        return true;
    }
    else if (request == LINE_DIAG_UNICAST_ID(LINE_DIAG_REQUEST_SW_NUMBER, assignedAddress)) {
        LINE_Diag_SoftwareVersion_t* sw_number = LINE_Diag_GetSoftwareVersion();
        *size = sizeof(LINE_Diag_SoftwareVersion_t);
        payload[0] = sw_number->major;
        payload[1] = sw_number->minor;
        payload[2] = sw_number->patch;
        payload[3] = sw_number->reserved;
        return true;
    }
    return false;
}

bool LINE_Diag_ListensTo(uint16_t request) {
    if (request == LINE_DIAG_REQUEST_WAKEUP) {
        return true;
    }
    if (request > LINE_DIAG_BROADCAST_ID_MIN && request < LINE_DIAG_BROADCAST_ID_MAX) {
        return true;
    }
    if (request > LINE_DIAG_UNICAST_ID_MIN && request < LINE_DIAG_UNICAST_ID_MAX) {
        return true;
    }

    return false;
}

void LINE_Diag_OnRequest(uint16_t request, uint8_t size, uint8_t* payload) {
    if (request == LINE_DIAG_REQUEST_WAKEUP) {
        LINE_Diag_OnWakeup();
    }
    else if (request == LINE_DIAG_REQUEST_SLEEP) {
        LINE_Diag_OnSleep();
    }
    else if (request == LINE_DIAG_REQUEST_SHUTDOWN) {
        LINE_Diag_OnShutdown();
    }
}

static void _no_handler(void) {
    // Empty function for not implemented callbacks
}

void LINE_Diag_OnWakeup(void) __attribute__((weak, alias("_no_handler")));

void LINE_Diag_OnSleep(void) __attribute__((weak, alias("_no_handler")));

void LINE_Diag_OnShutdown(void) __attribute__((weak, alias("_no_handler")));
