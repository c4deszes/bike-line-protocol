#include "line_transport.h"
#include "line_application.h"

bool LINE_Transport_RespondsTo(uint16_t request) {
  return LINE_App_RespondsTo(request);
}

bool LINE_Transport_PrepareResponse(uint16_t request, uint8_t* size, uint8_t* payload) {
  return LINE_App_PrepareResponse(request, size, payload);
}

void LINE_Transport_OnData(bool response, uint16_t request, uint8_t size, uint8_t* payload) {
  if (!response) {
    LINE_App_OnRequest(request, size, payload);
  }
}
