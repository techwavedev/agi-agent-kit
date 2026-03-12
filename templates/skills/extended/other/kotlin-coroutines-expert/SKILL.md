---
name: kotlin-coroutines-expert
description: "Expert patterns for Kotlin Coroutines and Flow, covering structured concurrency, error handling, and testing."
risk: safe
source: community
date_added: "2026-02-27"
---

# Kotlin Coroutines Expert

## Overview

A guide to mastering asynchronous programming with Kotlin Coroutines. Covers advanced topics like structured concurrency, `Flow` transformations, exception handling, and testing strategies.

## When to Use This Skill

- Use when implementing asynchronous operations in Kotlin.
- Use when designing reactive data streams with `Flow`.
- Use when debugging coroutine cancellations or exceptions.
- Use when writing unit tests for suspending functions or Flows.

## Step-by-Step Guide

### 1. Structured Concurrency

Always launch coroutines within a defined `CoroutineScope`. Use `coroutineScope` or `supervisorScope` to group concurrent tasks.

```kotlin
suspend fun loadDashboardData(): DashboardData = coroutineScope {
    val userDeferred = async { userRepo.getUser() }
    val settingsDeferred = async { settingsRepo.getSettings() }
    
    DashboardData(
        user = userDeferred.await(),
        settings = settingsDeferred.await()
    )
}
```

### 2. Exception Handling

Use `CoroutineExceptionHandler` for top-level scopes, but rely on `try-catch` within suspending functions for granular control.

```kotlin
val handler = CoroutineExceptionHandler { _, exception ->
    println("Caught $exception")
}

viewModelScope.launch(handler) {
    try {
        riskyOperation()
    } catch (e: IOException) {
        // Handle network error specifically
    }
}
```

### 3. Reactive Streams with Flow

Use `StateFlow` for state that needs to be retained, and `SharedFlow` for events.

```kotlin
// Cold Flow (Lazy)
val searchResults: Flow<List<Item>> = searchQuery
    .debounce(300)
    .flatMapLatest { query -> searchRepo.search(query) }
    .flowOn(Dispatchers.IO)

// Hot Flow (State)
val uiState: StateFlow<UiState> = _uiState.asStateFlow()
```

## Examples

### Example 1: Parallel Execution with Error Handling

```kotlin
suspend fun fetchDataWithErrorHandling() = supervisorScope {
    val task1 = async { 
        try { api.fetchA() } catch (e: Exception) { null } 
    }
    val task2 = async { api.fetchB() }
    
    // If task2 fails, task1 is NOT cancelled because of supervisorScope
    val result1 = task1.await()
    val result2 = task2.await() // May throw
}
```

## Best Practices

- ✅ **Do:** Use `Dispatchers.IO` for blocking I/O operations.
- ✅ **Do:** Cancel scopes when they are no longer needed (e.g., `ViewModel.onCleared`).
- ✅ **Do:** Use `TestScope` and `runTest` for unit testing coroutines.
- ❌ **Don't:** Use `GlobalScope`. It breaks structured concurrency and can lead to leaks.
- ❌ **Don't:** Catch `CancellationException` unless you rethrow it.

## Troubleshooting

**Problem:** Coroutine test hangs or fails unpredictably.
**Solution:** Ensure you are using `runTest` and injecting `TestDispatcher` into your classes so you can control virtual time.

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior test strategies, known flaky tests, and coverage gaps. Cache test infrastructure setup to avoid re-configuring test environments.

```bash
# Check for prior testing/QA context before starting
python3 execution/memory_manager.py auto --query "test patterns and coverage strategies for Kotlin Coroutines Expert"
```

### Storing Results

After completing work, store testing/QA decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Testing strategy: integration tests hit real DB (no mocks), 85% line coverage, mutation testing on critical paths" \
  --type technical --project <project> \
  --tags kotlin-coroutines-expert testing
```

### Multi-Agent Collaboration

Share test results and coverage reports with code review agents so they can verify adequate coverage on changed code.

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "QA complete — test suite expanded with 12 new integration tests, all passing" \
  --project <project>
```

### TDD Enforcement

This skill integrates with the framework's iron-law RED-GREEN-REFACTOR cycle. No production code without a failing test first.

### Agent Team: QA

Dispatch `qa_team` to generate tests and verify they pass before marking implementation complete.

<!-- AGI-INTEGRATION-END -->
