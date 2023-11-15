#include "line_application.h"
#include "line_diagnostics.h"

void LINE_App_Init(void) {

}

void LINE_App_OnRequest(uint16_t request, uint8_t size, uint8_t* payload) {
    if (LINE_Diag_ListensTo(request)) {
        LINE_Diag_OnRequest(request, size, payload);
    }
    else if (LINE_API_ListensTo(request)) {
        LINE_API_OnRequest(request, size, payload);
    }
}

bool LINE_App_RespondsTo(uint16_t request) {
    return LINE_API_RespondsTo(request) || LINE_Diag_RespondsTo(request);
}

bool LINE_App_PrepareResponse(uint16_t request, uint8_t* size, uint8_t* payload) {
    if (LINE_Diag_RespondsTo(request)) {
        return LINE_Diag_PrepareResponse(request, size, payload);
    }
    else if (LINE_API_RespondsTo(request)) {
        return LINE_API_PrepareResponse(request, size, payload);
    }
    return false;
}
