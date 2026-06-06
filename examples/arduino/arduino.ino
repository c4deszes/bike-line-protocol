#include "line_protocol.h"
#include "line_api.h"

LINE_Diag_SoftwareVersion_t sw_version = {
  .major = 0,
  .minor = 1,
  .patch = 0,
  .reserved = 0
};

LINE_Diag_PowerStatus_t power_status = {
  .U_measured = LINE_DIAG_POWER_STATUS_VOLTAGE(12000),    // 12V
  .I_operating = LINE_DIAG_POWER_STATUS_OP_CURRENT(100),  // 100mA
  .I_sleep = LINE_DIAG_POWER_STATUS_SLEEP_CURRENT(100)    // 100uA
};

uint8_t ld_Network_Arduino_GetOperationStatus(void) {
  return LINE_DIAG_OP_STATUS_OK;
}
LINE_Diag_PowerStatus_t* ld_Network_Arduino_GetPowerStatus(void) {
  return &power_status;
}
uint32_t ld_Network_Arduino_GetSerialNumber(void) {
  return 0xDEADBEEF;
}
LINE_Diag_SoftwareVersion_t* ld_Network_Arduino_GetSoftwareVersion(void) {
  return &sw_version;
}

void ld_Network_Arduino_OnWakeup(void) {
  Serial.println("Wakeup.");
}
void ld_Network_Arduino_OnIdle(void) {
  Serial.println("Go to idle.");
}
void ld_Network_Arduino_OnShutdown(void) {
  Serial.println("Shutting down.");
}
void ld_Network_Arduino_OnConditionalChangeAddress(uint8_t old_address, uint8_t new_address) {

}

void LINE_Transport_OnError(uint8_t channel, bool response, uint16_t request, line_transport_error error_type) {
  if (error_type == line_transport_error_timeout) {
    Serial.println("Timeout.");
  }
  else if (error_type == line_transport_error_header_invalid) {
    Serial.println("Header error.");
  }
  else if (error_type == line_transport_error_data_invalid) {
    Serial.println("Checksum error.");
  }
  else {
    Serial.println("Unknown error.");
  }
}

void LINE_Transport_WriteResponse(uint8_t channel, uint8_t size, uint8_t* payload, uint8_t checksum) {
  Serial1.write(size);
  for (int i=0;i<size;i++) {
    Serial1.write(payload[i]);
  }
  Serial1.write(checksum);
  Serial1.flush();
  Serial.println("Sent response.");
}

void setup() {
  Serial.begin(9600);
  while(!Serial);

  Serial1.begin(19200);

  LINE_App_Init();

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
    LINE_Transport_Receive(LT_Network_CHANNEL, data);
  }
  uint32_t currentTime = millis();
  uint32_t diff = currentTime - transport_timer;
  if (diff >= 1) {
    LINE_Transport_Update(LT_Network_CHANNEL, diff);
    transport_timer = currentTime;
  }

  if (l_rd_DigitalWrite_Bit0() == 1) {
    digitalWrite(8, HIGH);
  }
  else {
    digitalWrite(8, LOW);
  }

  l_wr_AnalogRead_Value(analogRead(A0));

}
