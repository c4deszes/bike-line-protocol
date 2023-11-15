#include "line_protocol.h"
#include "line_api.h"

uint8_t LINE_Diag_GetOperationStatus(void) {
  return LINE_DIAG_REQUEST_OP_STATUS_OK;
}

void LINE_Transport_OnError(bool response, uint16_t request, protocol_transport_error error_type) {
  if (error_type == protocol_transport_error_timeout) {
    Serial.println("Timeout.");
  }
  else if (error_type == protocol_transport_error_header_invalid) {
    Serial.println("Header error.");
  }
  else if (error_type == protocol_transport_error_data_invalid) {
    Serial.println("Checksum error.");
  }
  else {
    Serial.println("Unknown error.");
  }
}

void LINE_Transport_OnData(bool response, uint16_t request, uint8_t size, uint8_t* payload) {
  if (!response) {
    LINE_App_OnRequest(request, size, payload);

    Serial.println("Received frame.");
  }
  else {
    Serial.println("Sent frame.");
  }
}

bool LINE_Transport_PrepareResponse(uint16_t request, uint8_t* size, uint8_t* payload) {
  LINE_App_PrepareResponse(request, size, payload);
  Serial.println("Prepared response.");
}

void LINE_Transport_WriteResponse(uint8_t size, uint8_t* payload, uint8_t checksum) {
  Serial1.write(size);
  for (int i=0;i<size;i++) {
    Serial1.write(payload[i]);
  }
  Serial1.write(checksum);
  Serial1.flush();
  Serial.println("Sent response.");
}

bool LINE_Transport_RespondsTo(uint16_t request) {
  return LINE_App_RespondsTo(request);
}

void setup() {
  Serial.begin(9600);
  while(!Serial);

  Serial1.begin(19200);

  LINE_App_Init();
  LINE_Transport_Init(true);

  pinMode(8, OUTPUT);
  Serial.println("Initialized.");
}

uint32_t transport_timer = 0;

void loop() {
  while(Serial1.available() > 0) {
    uint8_t data = Serial1.read();
    Serial.print("Received: ");
    Serial.print(data, HEX);
    Serial.println();
    LINE_Transport_Receive(data);
  }
  uint32_t currentTime = millis();
  uint32_t diff = currentTime - transport_timer;
  if (diff > 5) {
    LINE_Transport_Update(diff);
    transport_timer = currentTime;
  }

  if (LINE_Request_DigitalWrite_data.fields.Bit0 == 1) {
    digitalWrite(8, HIGH);
  }
  else {
    digitalWrite(8, LOW);
  }
}