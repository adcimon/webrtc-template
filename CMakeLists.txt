cmake_minimum_required(VERSION 4.0.3)

project(webrtc-template)

# ================================================
# Compiler Options
# ================================================

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(WIN32)
	set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded") # /MT
	# set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreadedDLL") # /MD
endif()

# ================================================
# Directories
# ================================================

# External

set(EXTERNAL_DIR ${CMAKE_SOURCE_DIR}/external CACHE PATH "Path to external dependencies")

# WebRTC

set(WEBRTC_DIR ${EXTERNAL_DIR}/webrtc)
set(WEBRTC_INC_DIR ${WEBRTC_DIR}/include)
set(WEBRTC_LIB_DIR ${WEBRTC_DIR}/lib)

include_directories(
	${WEBRTC_INC_DIR}
	${WEBRTC_INC_DIR}/third_party/abseil-cpp
	${WEBRTC_INC_DIR}/third_party/abseil-cpp/absl
	${WEBRTC_INC_DIR}/third_party/libyuv/include
)

link_directories(
	${WEBRTC_LIB_DIR}
)

# ================================================
# Targets
# ================================================

set(
	SOURCES
	src/main.cpp
)

add_executable(${PROJECT_NAME} ${SOURCES})

# WebRTC

target_compile_definitions(${PROJECT_NAME}
	PRIVATE
		WEBRTC_ALLOW_DEPRECATED_NAMESPACES
)

if(UNIX)
	target_compile_definitions(${PROJECT_NAME}
		PRIVATE
			WEBRTC_LINUX
			WEBRTC_POSIX=1
			__STDC_CONSTANT_MACROS=1
	)
	target_link_libraries(${PROJECT_NAME}
		PRIVATE
			dl
			Dmoguids
			libwebrtc.a
			Msdmo
			pthread
			Secur32
			wmcodecdspuuid
			Winmm
	)
endif()

if(APPLE)
	target_compile_definitions(${PROJECT_NAME}
		PRIVATE
			WEBRTC_MAC
			WEBRTC_POSIX=1
	)
	target_link_libraries(${PROJECT_NAME}
		PRIVATE
			libwebrtc.a
	)
endif()

if(WIN32)
	target_compile_definitions(${PROJECT_NAME}
		PRIVATE
			ABSL_ALLOCATOR_NOTHROW=1
			CERT_CHAIN_PARA_HAS_EXTRA_FIELDS
			DYNAMIC_ANNOTATIONS_ENABLED=0
			HAVE_SCTP
			NOMINMAX
			NTDDI_VERSION=NTDDI_WIN10_RS2
			NVALGRIND
			PSAPI_VERSION=2
			RTC_ENABLE_VP9
			UNIQUE
			USE_AURA=1
			WEBRTC_ENABLE_PROTOBUF=0
			WEBRTC_INCLUDE_INTERNAL_AUDIO_DEVICE
			WEBRTC_LIBRARY_IMPL
			WEBRTC_NON_STATIC_TRACE_EVENT_HANDLERS=0
			WEBRTC_WIN
			WIN10=_WIN32_WINNT_WIN10
			WIN32
			WIN32_LEAN_AND_MEAN
			WINAPI_FAMILY=WINAPI_FAMILY_PC_APP
			WINUWP
			WINVER=0x0A00
			__STD_C
			__WRL_NO_DEFAULT_LIB__
			_HAS_EXCEPTIONS=0
			_ITERATOR_DEBUG_LEVEL=0
			_SILENCE_ALL_CXX20_DEPRECATION_WARNINGS
			_ATL_NO_OPENGL
			_CRT_RAND_S
			_CRT_SECURE_NO_WARNINGS
			_SECURE_ATL
			_UNICODE
			_WINDOWS
			_WIN32_WINNT=0x0A00
	)
	target_link_libraries(${PROJECT_NAME}
		PRIVATE
			dmoguids.lib
			msdmo.lib
			secur32.lib
			Strmiids.lib
			webrtc.lib
			winmm.lib
			wmcodecdspuuid.lib
			WS2_32
	)
endif()
