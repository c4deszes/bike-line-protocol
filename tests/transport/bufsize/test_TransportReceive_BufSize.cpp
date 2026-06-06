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

LINE_TRANSPORT_INST(Transport, 32, 32, TWOWIRE);

class TestTransportLayerReceiveBufSize : public testing::Test {
protected:
    void SetUp() override {
        
    }
};

TEST_F(TestTransportLayerReceiveBufSize, Configuration) {
    EXPECT_EQ(LINE_TRANSPORT_CHANNEL_COUNT, 1);
}

TEST_F(TestTransportLayerReceiveBufSize, ReceiveData_ValidSize) {
    
}

int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
