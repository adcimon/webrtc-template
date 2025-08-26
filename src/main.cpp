#define WEBRTC_ALLOW_DEPRECATED_NAMESPACES

#include "rtc_base/logging.h"
#include "rtc_base/log_sinks.h"
#include "rtc_base/ssl_adapter.h"

int main()
{
	rtc::InitializeSSL();

	rtc::LogMessage::LogToDebug(rtc::LS_INFO);
	rtc::LogMessage::LogTimestamps();
	RTC_LOG(LS_INFO) << "Hello WebRTC!";

	return 0;
}
