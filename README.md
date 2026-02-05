# WebRTC Template

Template to bootstrap a C++ application with WebRTC.

📦 Requirements:
- [CMake](https://cmake.org/)
- [Python](https://www.python.org/)

🧪 Tested:
- [ ] Linux
- [ ] Mac
- [x] Windows

Build WebRTC.
```
python ./scripts/build_webrtc.py run --branch "branch-heads/7204"
```
* Output: `./external/webrtc/`

Build application.
```
python ./scripts/build.py
```
* Output: `./build/Release/webrtc-template.exe`
