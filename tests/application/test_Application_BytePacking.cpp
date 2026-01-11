#include "gtest/gtest.h"
#include "fff.h"

extern "C" {
    #include "line_protocol.h"
    #include "line_api.h"
    #include "line_tester.h"
}

DEFINE_FFF_GLOBALS;

FAKE_VOID_FUNC4(LINE_Transport_WriteResponse, uint8_t, uint8_t, uint8_t*, uint8_t);

class TestApplicationBytePacking : public testing::Test {
protected:
    void SetUp() override {
        LINE_App_Init();
    }
};

TEST_F(TestApplicationBytePacking, Unicast_U8) {
    L_U8.data.signals.Value = 0xAB;
    BUILD_REQUEST(diag_frame, L_U8_ID);

    for (int i = 0; i < sizeof(diag_frame); i++) {
        LINE_Transport_Receive(LT_Network_CHANNEL, diag_frame[i]);
    }

    EXPECT_EQ(LINE_Transport_WriteResponse_fake.call_count, 1);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg0_val, LT_Network_CHANNEL);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg1_val, 1);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[0], 0xAB);
}

TEST_F(TestApplicationBytePacking, Unicast_U32) {
    L_U32.data.signals.Value = 0x12345678;
    BUILD_REQUEST(diag_frame, L_U32_ID);

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

TEST_F(TestApplicationBytePacking, Unicast_U8U16) {
    L_U8U16.data.signals.First = 0xCD;
    L_U8U16.data.signals.Second = 0x3456;
    BUILD_REQUEST(diag_frame, L_U8U16_ID);

    for (int i = 0; i < sizeof(diag_frame); i++) {
        LINE_Transport_Receive(LT_Network_CHANNEL, diag_frame[i]);
    }

    EXPECT_EQ(LINE_Transport_WriteResponse_fake.call_count, 1);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg0_val, LT_Network_CHANNEL);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg1_val, 3);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[0], 0xCD);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[1], 0x56);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[2], 0x34);
}

TEST_F(TestApplicationBytePacking, Unicast_U8U16U8) {
    L_U8U16U8.data.signals.First = 0xEF;
    L_U8U16U8.data.signals.Second = 0x789A;
    L_U8U16U8.data.signals.Third = 0x12;
    BUILD_REQUEST(diag_frame, L_U8U16U8_ID);

    for (int i = 0; i < sizeof(diag_frame); i++) {
        LINE_Transport_Receive(LT_Network_CHANNEL, diag_frame[i]);
    }

    EXPECT_EQ(LINE_Transport_WriteResponse_fake.call_count, 1);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg0_val, LT_Network_CHANNEL);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg1_val, 4);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[0], 0xEF);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[1], 0x9A);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[2], 0x78);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[3], 0x12);
}

int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
