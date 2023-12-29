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
 * @param request Request code
 * @param size Payload size
 * @param payload Payload
 */
void LINE_App_OnRequest(uint16_t request, uint8_t size, uint8_t* payload);

/**
 * @brief Called externally to determine whether the application intends to respond to a request,
 *        the function propagates calls to diagnostics and the application specific handlers
 * 
 * @param request Request code
 * @return true When the peripheral is responding
 * @return false Otherwise
 */
bool LINE_App_RespondsTo(uint16_t request);

/**
 * @brief Called to prepare the response content for the given request, the function propagates
 *        calls to the diagnostic and application specific handlers
 * 
 * @param request Request code
 * @param size Payload size
 * @param payload Payload
 * @return true When the response was successfully prepared
 * @return false Otherwise
 */
bool LINE_App_PrepareResponse(uint16_t request, uint8_t* size, uint8_t* payload);

// generated stuff
bool LINE_API_RespondsTo(uint16_t request);

bool LINE_API_PrepareResponse(uint16_t request, uint8_t* size, uint8_t* payload);

bool LINE_API_ListensTo(uint16_t request);

void LINE_API_OnRequest(uint16_t request, uint8_t size, uint8_t* payload);

#ifdef __cplusplus
}
#endif

#endif // LINE_LINE_APP_H_
