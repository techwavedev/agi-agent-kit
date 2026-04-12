---
name: expo-ui-jetpack-compose
description: expo-ui-jetpack-compose
risk: unknown
source: community
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

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior design decisions (color palettes, typography, spacing scales) to maintain visual consistency across sessions. Cache generated design tokens.

```bash
# Check for prior frontend/design context before starting
python3 execution/memory_manager.py auto --query "design system decisions and component patterns for Expo Ui Jetpack Compose"
```

### Storing Results

After completing work, store frontend/design decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Design system: adopted 8px grid, Inter font family, HSL color tokens with dark mode support" \
  --type decision --project <project> \
  --tags expo-ui-jetpack-compose frontend
```

### Multi-Agent Collaboration

Share design decisions with backend agents (API contract changes) and QA agents (visual regression baselines).

```bash
python3 execution/cross_agent_context.py store \
  --agent "<your-agent>" \
  --action "Implemented UI components — new design system with accessibility compliance (WCAG 2.1 AA)" \
  --project <project>
```

### Design Memory Persistence

Store design system tokens and component decisions in Qdrant so any agent on any platform (Claude, Gemini, Cursor) can retrieve and apply consistent styling.

<!-- AGI-INTEGRATION-END -->
