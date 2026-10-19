---
name: modern-cpp-sanitizer-verification
description: Compiles and tests modern C++20 code with AddressSanitizer and UndefinedBehaviorSanitizer enabled to guarantee memory safety.
---

# Modern C++ Sanitizer Verification Procedure

1. Read feature specification and review component header declarations.
2. Implement classes adhering to the Rule of Zero / Rule of Five and modern smart pointers (`std::unique_ptr`, `std::shared_ptr`).
3. Configure CMake with sanitizers: `-DCMAKE_BUILD_TYPE=Debug -DENABLE_ASAN=ON -DENABLE_UBSAN=ON`.
4. Build targets using Ninja: `cmake --build build -- -j$(nproc)`.
5. Execute CTest suite: `ctest --test-dir build --output-on-failure`.
6. Run Clang-Tidy: `clang-tidy -p build src/*.cpp`.
7. Confirm zero memory leaks, buffer overflows, or undefined behavior reports.
