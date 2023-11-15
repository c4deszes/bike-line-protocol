#if !defined(LINE_LINE_APP_H_)
#define LINE_LINE_APP_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdint.h>
#include <stdbool.h>

void LINE_App_Init(void);

// Called from transport layer, wiring done in the application
void LINE_App_OnRequest(uint16_t request, uint8_t size, uint8_t* payload);

// Called from transport layer to determine if the device is responding
bool LINE_App_RespondsTo(uint16_t request);

// Called from transport layer
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
