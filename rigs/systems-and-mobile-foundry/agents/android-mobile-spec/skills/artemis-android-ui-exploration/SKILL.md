---
name: artemis-android-ui-exploration
description: Deploys APK to containerized docker-android emulator and executes automated dynamic UI exploration using Google Artemis to catch crashes and ANRs.
---

# Artemis Android UI Exploration Procedure

1. Assemble debug APK: `./gradlew assembleDebug`.
2. Connect to containerized emulator via ADB: `adb connect ${ANDROID_ADB_HOST:-docker-android}:5555`.
3. Install debug APK and grant testing permissions.
4. Launch automated dynamic exploration via Google Artemis test runner:
   `artemis explore --apk app/build/outputs/apk/debug/app-debug.apk --timeout 180s --output-dir docs/evidence/android-artemis/`.
5. Capture emulator screenshots and UI hierarchy via `mobile-mcp` on any unhandled exception or visual anomaly.
6. Verify logcat for zero FATAL EXCEPTION or ANR (Application Not Responding) traces:
   `adb logcat -d *:E | grep -E "FATAL|ANR"`.
