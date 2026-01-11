#include "gtest/gtest.h"
#include "fff.h"

extern "C" {
    #include "line_protocol.h"
    #include "line_api.h"
    #include "line_tester.h"
}

DEFINE_FFF_GLOBALS;

FAKE_VOID_FUNC4(LINE_Transport_WriteResponse, uint8_t, uint8_t, uint8_t*, uint8_t);

FAKE_VOID_FUNC0(ld_Network_Peripheral_OnWakeup);
FAKE_VOID_FUNC0(ld_Network_Peripheral_OnIdle);
FAKE_VOID_FUNC0(ld_Network_Peripheral_OnShutdown);
FAKE_VOID_FUNC2(ld_Network_Peripheral_OnConditionalChangeAddress, uint8_t, uint8_t);

FAKE_VALUE_FUNC0(uint8_t, ld_Network_Peripheral_GetOperationStatus);
FAKE_VALUE_FUNC0(LINE_Diag_PowerStatus_t*, ld_Network_Peripheral_GetPowerStatus);
FAKE_VALUE_FUNC0(uint32_t, ld_Network_Peripheral_GetSerialNumber);
FAKE_VALUE_FUNC0(LINE_Diag_SoftwareVersion_t*, ld_Network_Peripheral_GetSoftwareVersion);

class TestDiagnosticsSingleNode : public testing::Test {
protected:
    void SetUp() override {
        LINE_App_Init();
    }
};

TEST_F(TestDiagnosticsSingleNode, Broadcast_Wakeup) {
    BUILD_EMPTY_FRAME(diag_frame, LINE_DIAG_REQUEST_WAKEUP);
    for (int i = 0; i < sizeof(diag_frame); i++) {
        LINE_Transport_Receive(LT_Network_CHANNEL, diag_frame[i]);
    }

    EXPECT_EQ(ld_Network_Peripheral_OnWakeup_fake.call_count, 1);
}

TEST_F(TestDiagnosticsSingleNode, Broadcast_Idle) {
    BUILD_EMPTY_FRAME(diag_frame, LINE_DIAG_REQUEST_IDLE);
    for (int i = 0; i < sizeof(diag_frame); i++) {
        LINE_Transport_Receive(LT_Network_CHANNEL, diag_frame[i]);
    }
    EXPECT_EQ(ld_Network_Peripheral_OnIdle_fake.call_count, 1);
}

TEST_F(TestDiagnosticsSingleNode, Broadcast_Shutdown) {
    BUILD_EMPTY_FRAME(diag_frame, LINE_DIAG_REQUEST_SHUTDOWN);
    for (int i = 0; i < sizeof(diag_frame); i++) {
        LINE_Transport_Receive(LT_Network_CHANNEL, diag_frame[i]);
    }
    EXPECT_EQ(ld_Network_Peripheral_OnShutdown_fake.call_count, 1);
}

TEST_F(TestDiagnosticsSingleNode, Broadcast_ConditionalChangeAddress_Set) {
    ld_Network_Peripheral_GetSerialNumber_fake.return_val = 0x04030201;
    BUILD_FRAME(diag_frame, LINE_DIAG_REQUEST_CONDITIONAL_CHANGE_ADDRESS, 0x01, 0x02, 0x03, 0x4, 0x01);

    for (int i = 0; i < sizeof(diag_frame); i++) {
        LINE_Transport_Receive(LT_Network_CHANNEL, diag_frame[i]);
    }

    EXPECT_EQ(ld_Network_Peripheral_OnConditionalChangeAddress_fake.call_count, 1);
    EXPECT_EQ(ld_Network_Peripheral_OnConditionalChangeAddress_fake.arg0_val, 0x01);
    EXPECT_EQ(ld_Network_Peripheral_OnConditionalChangeAddress_fake.arg1_val, 0x01);
}

TEST_F(TestDiagnosticsSingleNode, Broadcast_ConditionalChangeAddress_Unassign) {
    BUILD_FRAME(diag_frame, LINE_DIAG_REQUEST_CONDITIONAL_CHANGE_ADDRESS, 0x05, 0x06, 0x07, 0x8, 0x01);

    for (int i = 0; i < sizeof(diag_frame); i++) {
        LINE_Transport_Receive(LT_Network_CHANNEL, diag_frame[i]);
    }

    EXPECT_EQ(ld_Network_Peripheral_OnConditionalChangeAddress_fake.call_count, 1);
    EXPECT_EQ(ld_Network_Peripheral_OnConditionalChangeAddress_fake.arg0_val, 0x01);
    EXPECT_EQ(ld_Network_Peripheral_OnConditionalChangeAddress_fake.arg1_val, LINE_DIAG_UNICAST_UNASSIGNED_ID);
}

TEST_F(TestDiagnosticsSingleNode, Broadcast_ConditionalChangeAddress_Reassign) {
    ld_Network_Peripheral_GetSerialNumber_fake.return_val = 0x04030201;
    BUILD_FRAME(diag_frame, LINE_DIAG_REQUEST_CONDITIONAL_CHANGE_ADDRESS, 0x01, 0x02, 0x03, 0x4, 0x0E);

    for (int i = 0; i < sizeof(diag_frame); i++) {
        LINE_Transport_Receive(LT_Network_CHANNEL, diag_frame[i]);
    }

    EXPECT_EQ(ld_Network_Peripheral_OnConditionalChangeAddress_fake.call_count, 1);
    EXPECT_EQ(ld_Network_Peripheral_OnConditionalChangeAddress_fake.arg0_val, 0x01);
    EXPECT_EQ(ld_Network_Peripheral_OnConditionalChangeAddress_fake.arg1_val, 0x0E);
}

TEST_F(TestDiagnosticsSingleNode, Unicast_OpStatus) {
    ld_Network_Peripheral_GetOperationStatus_fake.return_val = LINE_DIAG_OP_STATUS_OK;
    BUILD_REQUEST(diag_frame, LINE_DIAG_UNICAST_ID(LINE_DIAG_REQUEST_OP_STATUS, LD_Peripheral_ADDRESS));

    for (int i = 0; i < sizeof(diag_frame); i++) {
        LINE_Transport_Receive(LT_Network_CHANNEL, diag_frame[i]);
    }

    EXPECT_EQ(LINE_Transport_WriteResponse_fake.call_count, 1);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg0_val, LT_Network_CHANNEL);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg1_val, 1);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[0], LINE_DIAG_OP_STATUS_OK);
}

// TODO: test when operation status is not implemented

TEST_F(TestDiagnosticsSingleNode, Unicast_PowerStatus) {
    LINE_Diag_PowerStatus_t power_status = {
        .U_measured = LINE_DIAG_POWER_STATUS_VOLTAGE(23000),
        .I_operating = LINE_DIAG_POWER_STATUS_OP_CURRENT(500),
        .I_sleep = LINE_DIAG_POWER_STATUS_SLEEP_CURRENT(100)
    };
    ld_Network_Peripheral_GetPowerStatus_fake.return_val = &power_status;
    BUILD_REQUEST(diag_frame, LINE_DIAG_UNICAST_ID(LINE_DIAG_REQUEST_POWER_STATUS, LD_Peripheral_ADDRESS));

    for (int i = 0; i < sizeof(diag_frame); i++) {
        LINE_Transport_Receive(LT_Network_CHANNEL, diag_frame[i]);
    }

    EXPECT_EQ(LINE_Transport_WriteResponse_fake.call_count, 1);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg0_val, LT_Network_CHANNEL);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg1_val, 4);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[0], 230);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[1], 500 & 0xFF);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[2], (500 >> 8) & 0xFF);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[3], 100);
}

TEST_F(TestDiagnosticsSingleNode, Unicast_SerialNumber) {
    ld_Network_Peripheral_GetSerialNumber_fake.return_val = 0x12345678;
    BUILD_REQUEST(diag_frame, LINE_DIAG_UNICAST_ID(LINE_DIAG_REQUEST_SERIAL_NUMBER, LD_Peripheral_ADDRESS));

    for (int i = 0; i < sizeof(diag_frame); i++) {
        LINE_Transport_Receive(LT_Network_CHANNEL, diag_frame[i]);
    }

    EXPECT_EQ(LINE_Transport_WriteResponse_fake.call_count, 1);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg0_val, LT_Network_CHANNEL);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg1_val, 4);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[0], 0x78);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[1], 0x56);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[2], 0x34);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[3], 0x12);
}

TEST_F(TestDiagnosticsSingleNode, Unicast_SoftwareVersion) {
    LINE_Diag_SoftwareVersion_t sw_version = {
        .major = 1,
        .minor = 2,
        .patch = 3,
        .reserved = 0
    };
    ld_Network_Peripheral_GetSoftwareVersion_fake.return_val = &sw_version;
    BUILD_REQUEST(diag_frame, LINE_DIAG_UNICAST_ID(LINE_DIAG_REQUEST_SW_NUMBER, LD_Peripheral_ADDRESS));

    for (int i = 0; i < sizeof(diag_frame); i++) {
        LINE_Transport_Receive(LT_Network_CHANNEL, diag_frame[i]);
    }

    EXPECT_EQ(LINE_Transport_WriteResponse_fake.call_count, 1);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg0_val, LT_Network_CHANNEL);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg1_val, 4);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[0], sw_version.major);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[1], sw_version.minor);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[2], sw_version.patch);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[3], sw_version.reserved);
}

int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
