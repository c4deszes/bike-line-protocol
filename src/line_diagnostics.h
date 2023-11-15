#if !defined(LINE_DIAGNOSTICS_H_)
#define LINE_DIAGNOSTICS_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdint.h>
#include <stdbool.h>

#define LINE_DIAG_BROADCAST_ID_MIN 0x0100
#define LINE_DIAG_BROADCAST_ID_MAX 0x01FF
#define LINE_DIAG_UNICAST_ID_MIN   0x0200
#define LINE_DIAG_UNICAST_ID_MAX   0x0FFF
#define LINE_DIAG_UNICAST_ID(request, id) (request | id)
#define LINE_DIAG_UNICAST_UNASSIGNED_ID 0x0

// Broadcast frames
#define LINE_DIAG_REQUEST_WAKEUP 0x0000
#define LINE_DIAG_REQUEST_SLEEP  0x0100
#define LINE_DIAG_REQUEST_SHUTDOWN 0x0101

// Unicast frames
#define LINE_DIAG_REQUEST_OP_STATUS 0x0110
#define LINE_DIAG_REQUEST_POWER_STATUS 0x0120
#define LINE_DIAG_REQUEST_SERIAL_NUMBER 0x0130
#define LINE_DIAG_REQUEST_SW_NUMBER 0x0140
#define LINE_DIAG_REQUEST_SW_RESET 0x0150

#define LINE_DIAG_REQUEST_OP_STATUS_OK 0
#define LINE_DIAG_REQUEST_OP_STATUS_WARN 1
#define LINE_DIAG_REQUEST_OP_STATUS_ERROR 2

#define LINE_DIAG_POWER_STATUS_VOLTAGE_OK 0
#define LINE_DIAG_POWER_STATUS_VOLTAGE_LOW 1
#define LINE_DIAG_POWER_STATUS_VOLTAGE_HIGH 2
#define LINE_DIAG_POWER_STATUS_BOD_NONE 0
#define LINE_DIAG_POWER_STATUS_BOD_DETECTED 1
#define LINE_DIAG_POWER_STATUS_OP_CURRENT(millis) (millis / 25)
#define LINE_DIAG_POWER_STATUS_SLEEP_CURRENT(micros) (micros / 10)

typedef struct {
    uint8_t U_status;
    uint8_t BOD_status;
    uint8_t I_operating;
    uint8_t I_sleep;
} LINE_Diag_PowerStatus_t;

typedef struct {
    uint8_t major;
    uint8_t minor;
    uint8_t patch;
} LINE_Diag_SoftwareVersion_t;

/**
 * @brief Initializes the diagnostic layer, without it the peripheral won't listen or respond to
 *        unicast requests only broadcast ones.
 * 
 * @param diag_address Diagnostic address
 */
void LINE_Diag_Init(uint8_t diag_address);

/**
 * @brief Returns whether the peripheral is responding to the diagnostic (unicast) request
 * 
 * @param request Request code
 * @return true When a respond will be sent
 * @return false When a response won't be sent by the peripheral
 */
bool LINE_Diag_RespondsTo(uint16_t request);

/**
 * @brief Prepares the response to a diagnostic request
 * 
 * @param request Request code
 * @param size Pointer to the size
 * @param payload Pointer to the payload content
 * @return true When the response was successfully prepared
 * @return false When not responding or errors during response preparation
 */
bool LINE_Diag_PrepareResponse(uint16_t request, uint8_t* size, uint8_t* payload);

/**
 * @brief Returns whether the peripheral is listening to the request
 * 
 * @param request Request code
 * @return true If the callback for the request should be called
 * @return false Otherwise
 */
bool LINE_Diag_ListensTo(uint16_t request);

/**
 * @brief Called when a diagnostic request is received, only called in case of broadcast requests
 *        and unicast requests that the peripheral is listening to
 * 
 * @param request Request code
 * @param size Size of the payload
 * @param payload Payload
 */
void LINE_Diag_OnRequest(uint16_t request, uint8_t size, uint8_t* payload);

void LINE_Diag_OnWakeup(void);

void LINE_Diag_OnSleep(void);

void LINE_Diag_OnShutdown(void);

uint8_t LINE_Diag_GetOperationStatus(void);

LINE_Diag_PowerStatus_t* LINE_Diag_GetPowerStatus(void);

uint32_t LINE_Diag_GetSerialNumber(void);

LINE_Diag_SoftwareVersion_t* LINE_Diag_GetSoftwareVersion(void);

#ifdef __cplusplus
}
#endif

#endif // LINE_DIAGNOSTICS_H_
