---
name: swiftui-concurrency-implementation
description: Implements modern SwiftUI views with Swift 6 structured concurrency, actors, and SwiftData models.
---

# SwiftUI Concurrency Implementation Procedure

1. Read mobile feature specification and design tokens.
2. Define data models with `@Model` (SwiftData) or Codable structs.
3. Implement view state using `@Observable` macro or ViewModel with `@MainActor`.
4. Handle background data fetching using structured tasks and error handling.
5. Author unit tests using Swift Testing / XCTest.
6. Verify code formatting and linting with SwiftLint: `swiftlint lint`.
7. Execute automated build and test: `swift test` (or `xcodebuild test`).
