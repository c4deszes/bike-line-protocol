#include "gtest/gtest.h"
#include "fff.h"

extern "C" {
    #include "line_protocol.h"
    #include "line_api.h"
    #include "line_tester.h"
}

DEFINE_FFF_GLOBALS;

FAKE_VOID_FUNC4(LINE_Transport_WriteResponse, uint8_t, uint8_t, uint8_t*, uint8_t);

FAKE_VOID_FUNC0(ld_Network_Peripheral1_OnWakeup);
FAKE_VOID_FUNC0(ld_Network_Peripheral1_OnIdle);
FAKE_VOID_FUNC0(ld_Network_Peripheral1_OnShutdown);
FAKE_VOID_FUNC2(ld_Network_Peripheral1_OnConditionalChangeAddress, uint8_t, uint8_t);
FAKE_VALUE_FUNC0(uint8_t, ld_Network_Peripheral1_GetOperationStatus);
FAKE_VALUE_FUNC0(LINE_Diag_PowerStatus_t*, ld_Network_Peripheral1_GetPowerStatus);
FAKE_VALUE_FUNC0(uint32_t, ld_Network_Peripheral1_GetSerialNumber);
FAKE_VALUE_FUNC0(LINE_Diag_SoftwareVersion_t*, ld_Network_Peripheral1_GetSoftwareVersion);

FAKE_VOID_FUNC0(ld_Network_Peripheral2_OnWakeup);
FAKE_VOID_FUNC0(ld_Network_Peripheral2_OnIdle);
FAKE_VOID_FUNC0(ld_Network_Peripheral2_OnShutdown);
FAKE_VOID_FUNC2(ld_Network_Peripheral2_OnConditionalChangeAddress, uint8_t, uint8_t);
FAKE_VALUE_FUNC0(uint8_t, ld_Network_Peripheral2_GetOperationStatus);
FAKE_VALUE_FUNC0(LINE_Diag_PowerStatus_t*, ld_Network_Peripheral2_GetPowerStatus);
FAKE_VALUE_FUNC0(uint32_t, ld_Network_Peripheral2_GetSerialNumber);
FAKE_VALUE_FUNC0(LINE_Diag_SoftwareVersion_t*, ld_Network_Peripheral2_GetSoftwareVersion);

class TestDiagnosticsMultiNode : public testing::Test {
protected:
    void SetUp() override {
        LINE_App_Init();
    }
};

TEST_F(TestDiagnosticsMultiNode, Broadcast_Wakeup) {
    BUILD_EMPTY_FRAME(diag_frame, LINE_DIAG_REQUEST_WAKEUP);
    for (int i = 0; i < sizeof(diag_frame); i++) {
        LINE_Transport_Receive(LT_Network_CHANNEL, diag_frame[i]);
    }

    EXPECT_EQ(ld_Network_Peripheral1_OnWakeup_fake.call_count, 1);
    EXPECT_EQ(ld_Network_Peripheral2_OnWakeup_fake.call_count, 1);
}

int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
