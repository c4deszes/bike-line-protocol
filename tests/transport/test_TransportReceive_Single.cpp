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

LINE_TRANSPORT_INST(Transport, 128, 128, TWOWIRE);

class TestTransportLayerReceive : public testing::Test {
protected:
    void SetUp() override {
        LINE_Transport_Init(0, &Transport);
    }
};

TEST_F(TestTransportLayerReceive, NotRespondingNoData) {
    LINE_Transport_RespondsTo_fake.return_val = false;
    BUILD_EMPTY_FRAME(data, 0x0000);

    for (int i = 0; i < sizeof(data); i++) {
        LINE_Transport_Receive(0, data[i]);
    }

    EXPECT_EQ(LINE_Transport_RespondsTo_fake.call_count, 1);
    EXPECT_EQ(LINE_Transport_RespondsTo_fake.arg1_val, 0x0000);

    EXPECT_EQ(LINE_Transport_OnData_fake.call_count, 1);
    EXPECT_EQ(LINE_Transport_OnData_fake.arg1_val, false);
    EXPECT_EQ(LINE_Transport_OnData_fake.arg2_val, 0x0000);
    EXPECT_EQ(LINE_Transport_OnData_fake.arg3_val, 0);

    EXPECT_EQ(LINE_Transport_OnError_fake.call_count, 0);
}

TEST_F(TestTransportLayerReceive, NotRespondingWithData) {
    LINE_Transport_RespondsTo_fake.return_val = false;
    BUILD_FRAME(data, 0x0000, 0x00, 0x00, 0x00, 0x00);

    for (int i = 0; i < sizeof(data); i++) {
        LINE_Transport_Receive(0, data[i]);
    }

    EXPECT_EQ(LINE_Transport_RespondsTo_fake.call_count, 1);
    EXPECT_EQ(LINE_Transport_OnData_fake.call_count, 1);
    EXPECT_EQ(LINE_Transport_OnError_fake.call_count, 0);
}

TEST_F(TestTransportLayerReceive, NotRespondingRequestError) {
    LINE_Transport_RespondsTo_fake.return_val = false;
    BUILD_REQUEST(data, 0x0000);
    data[sizeof(data) - 2] ^= 0xC0; // Corrupt the header

    for (int i = 0; i < sizeof(data); i++) {
        LINE_Transport_Receive(0, data[i]);
    }

    EXPECT_EQ(LINE_Transport_RespondsTo_fake.call_count, 0);
    EXPECT_EQ(LINE_Transport_OnData_fake.call_count, 0);
    EXPECT_EQ(LINE_Transport_OnError_fake.call_count, 1);
    EXPECT_EQ(LINE_Transport_OnError_fake.arg3_val, line_transport_error_header_invalid);
}

TEST_F(TestTransportLayerReceive, NotRespondingDataError) {
    LINE_Transport_RespondsTo_fake.return_val = false;
    BUILD_FRAME(data, 0x0000, 0x00, 0x00, 0x00, 0x00);
    data[sizeof(data) - 1] ^= 0xFF; // Corrupt checksum

    for (int i = 0; i < sizeof(data); i++) {
        LINE_Transport_Receive(0, data[i]);
    }

    EXPECT_EQ(LINE_Transport_RespondsTo_fake.call_count, 1);
    EXPECT_EQ(LINE_Transport_OnData_fake.call_count, 0);
    EXPECT_EQ(LINE_Transport_OnError_fake.call_count, 1);
    EXPECT_EQ(LINE_Transport_OnError_fake.arg3_val, line_transport_error_data_invalid);
}

TEST_F(TestTransportLayerReceive, NotRespondingHeaderTimeout) {
    LINE_Transport_RespondsTo_fake.return_val = false;
    uint8_t data[] = {LINE_SYNC_BYTE, 0x00};

    for (int i = 0; i < sizeof(data); i++) {
        LINE_Transport_Receive(0, data[i]);
    }

    LINE_Transport_Update(0, 100);

    EXPECT_EQ(LINE_Transport_RespondsTo_fake.call_count, 0);
    EXPECT_EQ(LINE_Transport_OnData_fake.call_count, 0);
    EXPECT_EQ(LINE_Transport_OnError_fake.call_count, 1);
    EXPECT_EQ(LINE_Transport_OnError_fake.arg3_val, line_transport_error_timeout);
}

TEST_F(TestTransportLayerReceive, NotRespondingLateHeader) {
    LINE_Transport_RespondsTo_fake.return_val = false;
    BUILD_FRAME(data, 0x0000, 0x00, 0x00, 0x00, 0x00);

    for (int i = 0; i < 2; i++) {
        LINE_Transport_Receive(0, data[i]);
    }

    LINE_Transport_Update(0, 100);

    for (int i = 2; i < sizeof(data); i++) {
        LINE_Transport_Receive(0, data[i]);
    }

    EXPECT_EQ(LINE_Transport_RespondsTo_fake.call_count, 0);
    EXPECT_EQ(LINE_Transport_OnData_fake.call_count, 0);
    EXPECT_EQ(LINE_Transport_OnError_fake.call_count, 1);
    EXPECT_EQ(LINE_Transport_OnError_fake.arg3_val, line_transport_error_timeout);
}

TEST_F(TestTransportLayerReceive, NotRespondingDataTimeout) {
    LINE_Transport_RespondsTo_fake.return_val = false;
    uint8_t data[] = {LINE_SYNC_BYTE, 0x00, 0x00};

    for (int i = 0; i < sizeof(data); i++) {
        LINE_Transport_Receive(0, data[i]);
    }

    LINE_Transport_Update(0, 100);

    EXPECT_EQ(LINE_Transport_RespondsTo_fake.call_count, 1);
    EXPECT_EQ(LINE_Transport_OnData_fake.call_count, 0);
    EXPECT_EQ(LINE_Transport_OnError_fake.call_count, 1);
    EXPECT_EQ(LINE_Transport_OnError_fake.arg3_val, line_transport_error_timeout);
}

int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
