---
name: expo-ui-jetpack-compose
description: expo-ui-jetpack-compose
---

---
name: expo-ui-jetpack-compose
description: `@expo/ui/jetpack-compose` package lets you use Jetpack Compose Views and modifiers in your app.
---

> The instructions in this skill apply to SDK 55 only. For other SDK versions, refer to the Expo UI Jetpack Compose docs for that version for the most accurate information.

## Installation

```bash
npx expo install @expo/ui
```

A native rebuild is required after installation (`npx expo run:android`).

## Instructions

- Expo UI's API mirrors Jetpack Compose's API. Use Jetpack Compose and Material Design 3 knowledge to decide which components or modifiers to use.
- Components are imported from `@expo/ui/jetpack-compose`, modifiers from `@expo/ui/jetpack-compose/modifiers`.
- When about to use a component, fetch its docs to confirm the API - https://docs.expo.dev/versions/v55.0.0/sdk/ui/jetpack-compose/{component-name}/index.md
- When unsure about a modifier's API, refer to the docs - https://docs.expo.dev/versions/v55.0.0/sdk/ui/jetpack-compose/modifiers/index.md
- Every Jetpack Compose tree must be wrapped in `Host`. Use `<Host matchContents>` for intrinsic sizing, or `<Host style={{ flex: 1 }}>` when you need explicit size (e.g. as a parent of `LazyColumn`). Example:

```jsx
import { Host, Column, Button, Text } from "@expo/ui/jetpack-compose";
import { fillMaxWidth, paddingAll } from "@expo/ui/jetpack-compose/modifiers";

<Host matchContents>
  <Column verticalArrangement={{ spacedBy: 8 }} modifiers={[fillMaxWidth(), paddingAll(16)]}>
    <Text style={{ typography: "titleLarge" }}>Hello</Text>
    <Button onPress={() => alert("Pressed!")}>Press me</Button>
  </Column>
</Host>;
```

## Key Components

- **LazyColumn** — Use instead of react-native `ScrollView`/`FlatList` for scrollable lists. Wrap in `<Host style={{ flex: 1 }}>`.
- **Icon** — Use `<Icon source={require('./icon.xml')} size={24} />` with Android XML vector drawables from [Material Symbols](https://fonts.google.com/icons).

---

<!-- AGI-INTEGRATION-START -->

## 🧠 AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Qdrant Memory Integration

Before executing complex tasks with this skill:
```bash
python3 execution/memory_manager.py auto --query "<task summary>"
```
- **Cache hit?** Use cached response directly — no need to re-process.
- **Memory match?** Inject `context_chunks` into your reasoning.
- **No match?** Proceed normally, then store results:
```bash
python3 execution/memory_manager.py store \\
  --content "Description of what was decided/solved" \\
  --type decision \\
  --tags expo-ui-jetpack-compose <relevant-tags>
```

### Agent Team Collaboration

- This skill can be invoked by the `orchestrator` agent via intelligent routing.
- In **Agent Teams mode**, results are shared via Qdrant shared memory for cross-agent context.
- In **Subagent mode**, this skill runs in isolation with its own memory namespace.

### Local LLM Support

When available, use local Ollama models for embedding and lightweight inference:
- Embeddings: `nomic-embed-text` via Qdrant memory system
- Lightweight analysis: Local models reduce API costs for repetitive patterns

<!-- AGI-INTEGRATION-END -->
