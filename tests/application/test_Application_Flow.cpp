#include "gtest/gtest.h"
#include "fff.h"

extern "C" {
    #include "line_protocol.h"
    #include "line_api.h"
    #include "line_tester.h"
}

DEFINE_FFF_GLOBALS;

FAKE_VOID_FUNC4(LINE_Transport_WriteResponse, uint8_t, uint8_t, uint8_t*, uint8_t);

class TestApplicationFlow : public testing::Test {
protected:
    void SetUp() override {
        LINE_App_Init();
    }
};

TEST_F(TestApplicationFlow, StatusResponse_Enabled) {
    l_Status.enabled = true;
    l_Status.data.bytes[0] = 0x12;
    l_Status.data.bytes[1] = 0x34;
    l_Status.data.bytes[2] = 0x56;
    BUILD_REQUEST(request_frame, L_Status_ID);

    for (int i = 0; i < sizeof(request_frame); i++) {
        LINE_Transport_Receive(LT_Network_CHANNEL, request_frame[i]);
    }

    EXPECT_EQ(LINE_Transport_WriteResponse_fake.call_count, 1);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg0_val, LT_Network_CHANNEL);
    EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg1_val, L_Status_SIZE);
    for (int i = 0; i < L_Status_SIZE; i++) {
        EXPECT_EQ(LINE_Transport_WriteResponse_fake.arg2_val[i], l_Status.data.bytes[i]);
    }
    EXPECT_EQ(l_Status.flag, true);
}

TEST_F(TestApplicationFlow, StatusResponse_Disabled) {
    l_Status.enabled = false;
    BUILD_REQUEST(request_frame, L_Status_ID);

    for (int i = 0; i < sizeof(request_frame); i++) {
        LINE_Transport_Receive(LT_Network_CHANNEL, request_frame[i]);
    }

    EXPECT_EQ(LINE_Transport_WriteResponse_fake.call_count, 0);
}

TEST_F(TestApplicationFlow, SetFrame_Update) {
    BUILD_FRAME(request_frame, L_Set_ID, 0xAA, 0xBB, 0xCC);

    for (int i = 0; i < sizeof(request_frame); i++) {
        LINE_Transport_Receive(LT_Network_CHANNEL, request_frame[i]);
    }

    EXPECT_EQ(l_Set.data.bytes[0], 0xAA);
    EXPECT_EQ(l_Set.data.bytes[1], 0xBB);
    EXPECT_EQ(l_Set.data.bytes[2], 0xCC);
    EXPECT_EQ(l_Set.flag, true);
}

int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
