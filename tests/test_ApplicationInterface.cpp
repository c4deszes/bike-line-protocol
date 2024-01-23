#include "gtest/gtest.h"
#include "fff.h"

extern "C" {
    #include "line_application.h"
    #include "line_diagnostics.h"
}

DEFINE_FFF_GLOBALS;

bool LINE_Diag_ListensTo(uint16_t request) {
    if (request == LINE_DIAG_BROADCAST_ID_MIN) {
        return true;
    }
    return false;
}

bool LINE_Diag_RespondsTo(uint16_t request) {
    if (request == LINE_DIAG_UNICAST_ID_MIN) {
        return true;
    }
    return false;
}

bool LINE_API_ListensTo(uint16_t request) {
    if (request == 0x2000) {
        return true;
    }
    return false;
}

bool LINE_API_RespondsTo(uint16_t request) {
    if (request == 0x2001) {
        return true;
    }
    return false;
}

FAKE_VOID_FUNC0(LINE_Diag_Init);

FAKE_VOID_FUNC3(LINE_Diag_OnRequest, uint16_t, uint8_t, uint8_t*);
FAKE_VOID_FUNC3(LINE_API_OnRequest, uint16_t, uint8_t, uint8_t*);

FAKE_VALUE_FUNC3(bool, LINE_Diag_PrepareResponse, uint16_t, uint8_t*, uint8_t*);
FAKE_VALUE_FUNC3(bool, LINE_API_PrepareResponse, uint16_t, uint8_t*, uint8_t*);

class TestApplicationSignals : public testing::Test {
protected:
    void SetUp() override {
        RESET_FAKE(LINE_Diag_OnRequest);
        RESET_FAKE(LINE_API_OnRequest);
    }
};

TEST_F(TestApplicationSignals, HandleDiagnosticRequest) {
    uint8_t payload[] = {0};
    LINE_App_OnRequest(LINE_DIAG_BROADCAST_ID_MIN, 1, payload);

    EXPECT_EQ(LINE_Diag_OnRequest_fake.call_count, 1);
    EXPECT_EQ(LINE_API_OnRequest_fake.call_count, 0);
}

TEST_F(TestApplicationSignals, HandleApplicationRequest) {
    uint8_t payload[] = {0};
    LINE_App_OnRequest(0x2000, 1, payload);

    EXPECT_EQ(LINE_Diag_OnRequest_fake.call_count, 0);
    EXPECT_EQ(LINE_API_OnRequest_fake.call_count, 1);
}

int main(int argc, char **argv) {
    ::testing::InitGoogleTest(&argc, argv);
    return RUN_ALL_TESTS();
}
