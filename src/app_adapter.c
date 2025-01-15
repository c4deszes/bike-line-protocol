#include "line_transport.h"
#include "line_application.h"

bool LINE_Transport_RespondsTo(uint8_t channel, uint16_t request) {
  return LINE_App_RespondsTo(channel, request);
}

bool LINE_Transport_PrepareResponse(uint8_t channel, uint16_t request, uint8_t* size, uint8_t* payload) {
  return LINE_App_PrepareResponse(channel, request, size, payload);
}

void LINE_Transport_OnData(uint8_t channel, bool response, uint16_t request, uint8_t size, uint8_t* payload) {
  if (!response) {
    LINE_App_OnRequest(channel, request, size, payload);
  }
}
