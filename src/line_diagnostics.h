#if !defined(LINE_DIAGNOSTICS_H_)
#define LINE_DIAGNOSTICS_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdint.h>
#include <stdbool.h>

#ifndef LINE_DIAG_CHANNEL_COUNT
#define LINE_DIAG_CHANNEL_COUNT 1
#endif

#ifndef LINE_DIAG_SERVICE_MAX_UNICAST_LISTENERS
#define LINE_DIAG_SERVICE_MAX_UNICAST_LISTENERS 8
#endif

#ifndef LINE_DIAG_SERVICE_MAX_UNICAST_PUBLISHERS
#define LINE_DIAG_SERVICE_MAX_UNICAST_PUBLISHERS 8
#endif

#define LINE_DIAG_BROADCAST_ID_MIN 0x0100
#define LINE_DIAG_BROADCAST_ID_MAX 0x01FF
#define LINE_DIAG_UNICAST_ID_MIN   0x0200
#define LINE_DIAG_UNICAST_ID_MAX   0x0FFF
#define LINE_DIAG_UNICAST_ID(request, id) (request | id)
#define LINE_DIAG_UNICAST_UNASSIGNED_ID 0x0
#define LINE_DIAG_UNICAST_BROADCAST_ID 0xF

// Broadcast frames
#define LINE_DIAG_REQUEST_WAKEUP 0x0000
#define LINE_DIAG_REQUEST_IDLE  0x0100
#define LINE_DIAG_REQUEST_SHUTDOWN 0x0101
#define LINE_DIAG_REQUEST_CONDITIONAL_CHANGE_ADDRESS 0x01E0

// Unicast frames (mandatory)
#define LINE_DIAG_REQUEST_OP_STATUS 0x0200
#define LINE_DIAG_REQUEST_POWER_STATUS 0x0210
#define LINE_DIAG_REQUEST_SERIAL_NUMBER 0x0220
#define LINE_DIAG_REQUEST_SW_NUMBER 0x0230

// Unicast frames (optional)
//#define LINE_DIAG_REQUEST_SW_RESET 0x0240

#define LINE_DIAG_OP_STATUS_INIT 0x00
#define LINE_DIAG_OP_STATUS_OK 0x01
#define LINE_DIAG_OP_STATUS_WARN 0x02
#define LINE_DIAG_OP_STATUS_ERROR 0x03
#define LINE_DIAG_OP_STATUS_BOOT 0x40
#define LINE_DIAG_OP_STATUS_BOOT_ERROR 0x41

#define LINE_DIAG_POWER_STATUS_VOLTAGE(millis) (millis/100)
#define LINE_DIAG_POWER_STATUS_OP_CURRENT(millis) (millis)
#define LINE_DIAG_POWER_STATUS_SLEEP_CURRENT(micros) (micros / 10)

/**
 * @brief Structure representing the power status of the device.
 * This structure contains the measured voltage, operating current, and sleep current of the device.
 *
 * U_measured: Measured voltage in 100mV units (e.g., 120 means 12.0V).
 * I_operating: Operating current in mA (e.g., 1000 means 1.0A).
 * I_sleep: Sleep current in uA (e.g., 100 means 100uA).
 */
typedef struct {
    uint8_t U_measured;
    uint16_t I_operating;
    uint8_t I_sleep;
} LINE_Diag_PowerStatus_t;

/**
 * @brief Structure representing the software version of the device.
 * This structure contains the major, minor, and patch version numbers of the software.
 *
 * major: Major version number (e.g., 1).
 * minor: Minor version number (e.g., 0).
 * patch: Patch version number (e.g., 3).
 * reserved: Reserved for future use, should be set to 0.
 */
typedef struct {
    uint8_t major;
    uint8_t minor;
    uint8_t patch;
    uint8_t reserved;
} LINE_Diag_SoftwareVersion_t;

/**
 * @brief Configuration structure for the LINE diagnostic layer.
 * This structure contains the configuration parameters for the diagnostic layer,
 * including transport channel, address, and various callback functions.
 * 
 * When the callbacks are not set, the default behavior is to do nothing, that means in the case of
 * op status the peripheral will not respond. In the case of wakeup, idle, shutdown, and
 * conditional change address, the peripheral will not perform any action.
 *
 * transport_channel: The transport channel used for diagnostics.
 * address: The address of the device in the diagnostic layer.
 * on_wakeup: Callback function called when the device wakes up.
 * on_idle: Callback function called when the device goes idle.
 * on_shutdown: Callback function called when the device shuts down.
 * on_conditional_change_address: Callback function called when the address changes conditionally.
 * op_status: Function pointer to get the operational status of the device.
 * power_status: Function pointer to get the power status of the device.
 * serial_number: Function pointer to get the serial number of the device.
 * software_version: Function pointer to get the software version of the device.
 */
typedef struct {
    uint8_t transport_channel;
    uint8_t address;
    void (*on_wakeup)(void);
    void (*on_idle)(void);
    void (*on_shutdown)(void);
    void (*on_conditional_change_address)(uint8_t old_address, uint8_t new_address);
    uint8_t (*op_status)(void);
    LINE_Diag_PowerStatus_t* (*power_status)(void);
    uint32_t (*serial_number)(void);
    LINE_Diag_SoftwareVersion_t* (*software_version)(void);
} LINE_Diag_Config_t;

typedef void (*LINE_Diag_ListenerCallback_t)(uint16_t request, uint8_t size, uint8_t* payload);
typedef bool (*LINE_Diag_PublisherCallback_t)(uint16_t request, uint8_t* size, uint8_t* payload);

/**
 * @brief Initializes the diagnostic layer, without it the peripheral won't listen or respond to
 *        any diagnostic requests.
 */
void LINE_Diag_Init(uint8_t diag_channel, LINE_Diag_Config_t* diag_config);

void LINE_Diag_RegisterUnicastListener(uint8_t diag_channel, uint16_t request, LINE_Diag_ListenerCallback_t callback);

void LINE_Diag_RegisterUnicastPublisher(uint8_t diag_channel, uint16_t request, LINE_Diag_PublisherCallback_t callback);

/**
 * @brief Returns whether the peripheral is responding to the diagnostic (unicast) request
 * 
 * @param transport_layer Transport layer used
 * @param request Request code
 * @return true When a respond will be sent
 * @return false When a response won't be sent by the peripheral
 */
bool LINE_Diag_RespondsTo(uint8_t transport_layer, uint16_t request);

/**
 * @brief Prepares the response to a diagnostic request
 * 
 * @param transport_layer Transport layer used
 * @param request Request code
 * @param size Pointer to the size
 * @param payload Pointer to the payload content
 * @return true When the response was successfully prepared
 * @return false When not responding or errors during response preparation
 */
bool LINE_Diag_PrepareResponse(uint8_t transport_layer, uint16_t request, uint8_t* size, uint8_t* payload);

/**
 * @brief Returns whether the peripheral is listening to the request
 * 
 * @param transport_layer Transport layer used
 * @param request Request code
 * @return true If the callback for the request should be called
 * @return false Otherwise
 */
bool LINE_Diag_ListensTo(uint8_t transport_layer, uint16_t request);

/**
 * @brief Called when a diagnostic request is received, only called in case of broadcast requests
 *        and unicast requests that the peripheral is listening to
 * 
 * @param transport_layer Transport layer used
 * @param request Request code
 * @param size Size of the payload
 * @param payload Payload
 */
void LINE_Diag_OnRequest(uint8_t transport_layer, uint16_t request, uint8_t size, uint8_t* payload);

#ifdef __cplusplus
}
#endif

#endif // LINE_DIAGNOSTICS_H_
