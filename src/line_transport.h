#if !defined(LINE_LINE_TRANSPORT_H_)
#define LINE_LINE_TRANSPORT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdint.h>
#include <stdbool.h>

#define LINE_SYNC_BYTE 0x55
#define LINE_REQUEST_PARITY_MASK 0x3FFF
#define LINE_REQUEST_PARITY_POS 13

#define LINE_HEADER_TIMEOUT 1
#define LINE_DATA_TIMEOUT 5

typedef enum {
    protocol_transport_error_timeout,
    protocol_transport_error_header_invalid,
    protocol_transport_error_data_invalid
} protocol_transport_error;

/**
 * @brief Initializes the transport layer
 */
void LINE_Transport_Init(bool one_wire);

/**
 * @brief Updates the transport layer state, called by the physical layer or the scheduler
 * 
 * When using it from the scheduler it should be called from a 1ms or higher rate tasks, the task
 * should process all available bytes in a single cycle.
 * 
 * When calling it from interrupts note that the duration of this method might be long especially
 * if the application layer is directly tied to transport callbacks.
 * 
 * @param data Byte received
 */
void LINE_Transport_Receive(uint8_t data);

/**
 * @brief Updates the transport layer state based on the time elapsed, called by the scheduler
 * 
 * The transport layer keeps track of time using this function, if the time elapsed since the byte
 * 
 * @param elapsed Time elapsed since the last call in milliseconds
 */
void LINE_Transport_Update(uint8_t elapsed);

/**
 * @brief Called when a valid request ID is received, the consumer should then decide whether it
 * should respond
 * 
 * @param request 
 * @return true if the consumer is responding to this request
 * @return false if the consumer is listening to this request
 */
bool LINE_Transport_RespondsTo(uint16_t request);

bool LINE_Transport_PrepareResponse(uint16_t request, uint8_t* size, uint8_t* payload);

void LINE_Transport_WriteResponse(uint8_t size, uint8_t* payload, uint8_t checksum);

/**
 * @brief Called when the data body is received, the consumer should then decide how it should
 *        interpret the data
 * 
 * @param response true if this data was sent by the consumer
 * @param request Request identifier
 * @param size Data size
 * @param payload Data pointer
 */
void LINE_Transport_OnData(bool response, uint16_t request, uint8_t size, uint8_t* payload);

/**
 * @brief Called when an error occurs, which can be
 * - No response received
 * - Request header parity is invalid
 * - Data checksum is invalid
 * 
 * @param response Whether the 
 * @param request Request identifier
 * @param error_type Error code
 */
void LINE_Transport_OnError(bool response, uint16_t request, protocol_transport_error error_type);

#ifdef __cplusplus
}
#endif

#endif // LINE_LINE_TRANSPORT_H_
