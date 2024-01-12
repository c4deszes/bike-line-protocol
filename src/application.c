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

bool _LINE_API_RespondsTo_default(uint16_t request) {
    return false;
}
bool LINE_API_RespondsTo(uint16_t request) __attribute__((weak,alias("_LINE_API_RespondsTo_default")));

bool _LINE_API_PrepareResponse_default(uint16_t request, uint8_t* size, uint8_t* payload) {
    return false;
}
bool LINE_API_PrepareResponse(uint16_t request, uint8_t* size, uint8_t* payload) __attribute__((weak,alias("_LINE_API_PrepareResponse_default")));

bool _LINE_API_ListensTo_default(uint16_t request) {
    return false;
}
bool LINE_API_ListensTo(uint16_t request) __attribute__((weak,alias("_LINE_API_ListensTo_default")));

void _LINE_API_OnRequest_default(uint16_t request, uint8_t size, uint8_t* payload) {
    return;
}
void LINE_API_OnRequest(uint16_t request, uint8_t size, uint8_t* payload) __attribute__((weak,alias("_LINE_API_OnRequest_default")));
