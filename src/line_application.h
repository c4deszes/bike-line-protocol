#if !defined(LINE_LINE_APP_H_)
#define LINE_LINE_APP_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdint.h>
#include <stdbool.h>

/**
 * @brief Initializes the application layer
 */
void LINE_App_Init(void);

/**
 * @brief Called externally when a request is received, the function then propagates the call to
 *        diagnostics or the application specific handler
 * 
 * @param channel Transport channel
 * @param request Request code
 * @param size Payload size
 * @param payload Payload
 */
void LINE_App_OnRequest(uint8_t channel, uint16_t request, uint8_t size, uint8_t* payload);

/**
 * @brief Called externally to determine whether the application intends to respond to a request,
 *        the function propagates calls to diagnostics and the application specific handlers
 * 
 * @param channel Transport channel
 * @param request Request code
 * @return true When the peripheral is responding
 * @return false Otherwise
 */
bool LINE_App_RespondsTo(uint8_t channel, uint16_t request);

/**
 * @brief Called to prepare the response content for the given request, the function propagates
 *        calls to the diagnostic and application specific handlers
 * 
 * @param channel Transport channel
 * @param request Request code
 * @param size Payload size
 * @param payload Payload
 * @return true When the response was successfully prepared
 * @return false Otherwise
 */
bool LINE_App_PrepareResponse(uint8_t channel, uint16_t request, uint8_t* size, uint8_t* payload);

#ifdef __cplusplus
}
#endif

#endif // LINE_LINE_APP_H_
