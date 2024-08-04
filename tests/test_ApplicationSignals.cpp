#include "gtest/gtest.h"
#include "fff.h"

extern "C" {
    #include "line_protocol.h"
    #include "line_api.h"
}

DEFINE_FFF_GLOBALS;

class TestApplicationSignals : public testing::Test {
protected:
    void SetUp() override {
        
    }
};

void LINE_Transport_WriteRequest(uint16_t request) {
    return;
}

FAKE_VALUE_FUNC0(uint8_t, LINE_Diag_GetOperationStatus);
FAKE_VALUE_FUNC0(LINE_Diag_PowerStatus_t*, LINE_Diag_GetPowerStatus);
FAKE_VALUE_FUNC0(uint32_t, LINE_Diag_GetSerialNumber);
FAKE_VALUE_FUNC0(LINE_Diag_SoftwareVersion_t*, LINE_Diag_GetSoftwareVersion);

FAKE_VOID_FUNC3(LINE_Transport_WriteResponse, uint8_t, uint8_t*, uint8_t);

TEST_F(TestApplicationSignals, ListenToAlignedRequest) {
    uint8_t payload[] = {0x01, 0x02, 0x03, 0x04};
    LINE_App_OnRequest(LINE_REQUEST_Aligned_ID, LINE_REQUEST_Aligned_SIZE, payload);

    EXPECT_EQ(LINE_Request_Aligned_data.fields.First, 0x01);
    EXPECT_EQ(LINE_Request_Aligned_data.fields.Second, 0x02);
    EXPECT_EQ(LINE_Request_Aligned_data.fields.Third, 0x0403);
}

TEST_F(TestApplicationSignals, PrepareWideResponse) {
    uint8_t payload[] = {0, 0, 0, 0};
    uint8_t size = 0;

    LINE_Request_Wide_data.fields.First = 0x01020304;

    LINE_App_PrepareResponse(LINE_REQUEST_Wide_ID, &size, payload);

    EXPECT_EQ(payload[0], 0x04);
    EXPECT_EQ(payload[1], 0x03);
    EXPECT_EQ(payload[2], 0x02);
    EXPECT_EQ(payload[3], 0x01);
}

int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
