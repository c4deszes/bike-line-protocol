#include "gtest/gtest.h"
#include "fff.h"

extern "C" {
    #include "line_transport.h"
    #include "line_tester.h"
}

DEFINE_FFF_GLOBALS;

FAKE_VOID_FUNC5(LINE_Transport_OnData, uint8_t, bool, uint16_t, uint8_t, uint8_t*);
FAKE_VOID_FUNC4(LINE_Transport_OnError, uint8_t, bool, uint16_t, line_transport_error);
FAKE_VOID_FUNC4(LINE_Transport_WriteResponse, uint8_t, uint8_t, uint8_t*, uint8_t);
FAKE_VOID_FUNC2(LINE_Transport_WriteRequest, uint8_t, uint16_t);

FAKE_VALUE_FUNC4(bool, LINE_Transport_PrepareResponse, uint8_t, uint16_t, uint8_t*, uint8_t*);
FAKE_VALUE_FUNC2(bool, LINE_Transport_RespondsTo, uint8_t, uint16_t);

LINE_TRANSPORT_INST(Transport1, 128, 128, TWOWIRE);
LINE_TRANSPORT_INST(Transport2, 128, 128, TWOWIRE);

class TestTransportLayerReceiveMultiple : public testing::Test {
protected:
    void SetUp() override {
        
    }
};

TEST_F(TestTransportLayerReceiveMultiple, Configuration) {
    EXPECT_EQ(LINE_TRANSPORT_CHANNEL_COUNT, 2);
}

TEST_F(TestTransportLayerReceiveMultiple, MultichannelReceive) {
    BUILD_FRAME(data1, 0x0012, 0x34, 0x56, 0x78);
    BUILD_FRAME(data2, 0x0034, 0x9A, 0xBC, 0xDE);

    LINE_Transport_Init(0, &Transport1);
    LINE_Transport_Init(1, &Transport2);

    for (int i = 0; i < sizeof(data1); i++) {
        LINE_Transport_Receive(0, data1[i]);
    }

    for (int i = 0; i < sizeof(data2); i++) {
        LINE_Transport_Receive(1, data2[i]);
    }

    EXPECT_EQ(LINE_Transport_RespondsTo_fake.call_count, 2);
    EXPECT_EQ(LINE_Transport_OnData_fake.call_count, 2);
    EXPECT_EQ(LINE_Transport_OnError_fake.call_count, 0);
}

int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
