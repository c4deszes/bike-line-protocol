#if !defined(LINE_LINE_TRANSPORT_H_)
#define LINE_LINE_TRANSPORT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdint.h>
#include <stdbool.h>

#ifndef LINE_TRANSPORT_CHANNEL_COUNT
#define LINE_TRANSPORT_CHANNEL_COUNT 1
#endif

#ifndef LINE_TRANSPORT_RX_BUFFER_SIZE
#define LINE_TRANSPORT_RX_BUFFER_SIZE 255
#endif

#ifndef LINE_TRANSPORT_TX_BUFFER_SIZE
#define LINE_TRANSPORT_TX_BUFFER_SIZE 255
#endif

typedef enum {
    line_transport_error_timeout,
    line_transport_error_header_invalid,
    line_transport_error_data_invalid,
    line_transport_error_partial_data
} line_transport_error;

/**
 * @brief Initializes the transport layer
 */
void LINE_Transport_Init(uint8_t channel, bool one_wire);

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
void LINE_Transport_Receive(uint8_t channel, uint8_t data);

/**
 * @brief Updates the transport layer state based on the time elapsed, called by the scheduler
 * 
 * The transport layer keeps track of time using this function, if the time elapsed since the byte
 * 
 * @param elapsed Time elapsed since the last call in milliseconds
 */
void LINE_Transport_Update(uint8_t channel, uint8_t elapsed);

/**
 * @brief Called when a valid request code is received, the consumer should then decide whether it
 * should respond
 * 
 * @param request Request code
 * @return true if the consumer is responding to this request
 * @return false if the consumer is listening to this request
 */
bool LINE_Transport_RespondsTo(uint8_t channel, uint16_t request);

/**
 * @brief Called when a request is received and the peripheral is responding to, the function
 * should then prepare the payload contents for the given request
 * 
 * @param request Request code
 * @param size Payload size
 * @param payload Payload
 * @return true When the response was successfully prepared
 * @return false Otherwise
 */
bool LINE_Transport_PrepareResponse(uint8_t channel, uint16_t request, uint8_t* size, uint8_t* payload);

/**
 * @brief Writes the response to the physical layer (implemented at target)
 * 
 * @param size Payload size
 * @param payload Payload
 * @param checksum Checksum value
 */
void LINE_Transport_WriteResponse(uint8_t channel, uint8_t size, uint8_t* payload, uint8_t checksum);

void LINE_Transport_Request(uint8_t channel, uint16_t request);

/**
 * @brief Requests a frame on the bus (implemented at the target)
 * 
 * The function shall write the sync byte and request header to the bus.
 * 
 * @param request 
 */
void LINE_Transport_WriteRequest(uint8_t channel, uint16_t request);

/**
 * @brief Called when the data body is received, the consumer should then decide how it should
 *        interpret the data
 * 
 * @param response Whether the peripheral is the one responding to this request
 * @param request Request code
 * @param size Data size
 * @param payload Data pointer
 */
void LINE_Transport_OnData(uint8_t channel, bool response, uint16_t request, uint8_t size, uint8_t* payload);

/**
 * @brief Called when an error occurs, which can be
 * - No response received
 * - Request header parity is invalid
 * - Data checksum is invalid
 * 
 * @param response Whether the peripheral is the one responding to this request
 * @param request Request code
 * @param error_type Error code
 */
void LINE_Transport_OnError(uint8_t channel, bool response, uint16_t request, line_transport_error error_type);

#ifdef __cplusplus
}
#endif

#endif // LINE_LINE_TRANSPORT_H_
