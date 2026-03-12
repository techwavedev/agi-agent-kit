---
name: makepad-basics
description: |
  CRITICAL: Use for Makepad getting started and app structure. Triggers on:
  makepad, makepad getting started, makepad tutorial, live_design!, app_main!,
  makepad project setup, makepad hello world, "how to create makepad app",
  makepad 入门, 创建 makepad 应用, makepad 教程, makepad 项目结构
---

# Makepad Basics Skill

> **Version:** makepad-widgets (dev branch) | **Last Updated:** 2026-01-19
>
> Check for updates: https://crates.io/crates/makepad-widgets

You are an expert at the Rust `makepad-widgets` crate. Help users by:
- **Writing code**: Generate Rust code following the patterns below
- **Answering questions**: Explain concepts, troubleshoot issues, reference documentation

## Documentation

Refer to the local files for detailed documentation:
- `./references/app-structure.md` - Complete app boilerplate and structure
- `./references/event-handling.md` - Event handling patterns

## IMPORTANT: Documentation Completeness Check

**Before answering questions, Claude MUST:**

1. Read the relevant reference file(s) listed above
2. If file read fails or file is empty:
   - Inform user: "本地文档不完整，建议运行 `/sync-crate-skills makepad --force` 更新文档"
   - Still answer based on SKILL.md patterns + built-in knowledge
3. If reference file exists, incorporate its content into the answer

## Key Patterns

### 1. Basic App Structure

```rust
use makepad_widgets::*;

live_design! {
    use link::theme::*;
    use link::shaders::*;
    use link::widgets::*;

    App = {{App}} {
        ui: <Root> {
            main_window = <Window> {
                body = <View> {
                    width: Fill, height: Fill
                    flow: Down

                    <Label> { text: "Hello Makepad!" }
                }
            }
        }
    }
}

app_main!(App);

#[derive(Live, LiveHook)]
pub struct App {
    #[live] ui: WidgetRef,
}

impl LiveRegister for App {
    fn live_register(cx: &mut Cx) {
        crate::makepad_widgets::live_design(cx);
    }
}

impl AppMain for App {
    fn handle_event(&mut self, cx: &mut Cx, event: &Event) {
        self.ui.handle_event(cx, event, &mut Scope::empty());
    }
}
```

### 2. Cargo.toml Setup

```toml
[package]
name = "my_app"
version = "0.1.0"
edition = "2024"

[dependencies]
makepad-widgets = { git = "https://github.com/makepad/makepad", branch = "dev" }
```

### 3. Handling Button Clicks

```rust
impl AppMain for App {
    fn handle_event(&mut self, cx: &mut Cx, event: &Event) {
        let actions = self.ui.handle_event(cx, event, &mut Scope::empty());

        if self.ui.button(id!(my_button)).clicked(&actions) {
            log!("Button clicked!");
        }
    }
}
```

### 4. Accessing and Modifying Widgets

```rust
// Get widget references
let label = self.ui.label(id!(my_label));
label.set_text("Updated text");

let input = self.ui.text_input(id!(my_input));
let text = input.text();
```

## API Reference Table

| Macro/Type | Description | Example |
|------------|-------------|---------|
| `live_design!` | Defines UI in DSL | `live_design! { App = {{App}} { ... } }` |
| `app_main!` | Entry point macro | `app_main!(App);` |
| `#[derive(Live)]` | Derive live data | `#[derive(Live, LiveHook)]` |
| `WidgetRef` | Reference to UI tree | `#[live] ui: WidgetRef` |
| `Cx` | Context for rendering | `fn handle_event(&mut self, cx: &mut Cx, ...)` |
| `id!()` | Widget ID macro | `self.ui.button(id!(my_button))` |

## Platform Setup

| Platform | Requirements |
|----------|--------------|
| macOS | Works out of the box |
| Windows | Works out of the box |
| Linux | `apt-get install clang libaudio-dev libpulse-dev libx11-dev libxcursor-dev` |
| Web | `cargo install wasm-pack` |

## When Writing Code

1. Always include required imports: `use makepad_widgets::*;`
2. Use `live_design!` macro for all UI definitions
3. Implement `LiveRegister` and `AppMain` traits
4. Use `id!()` macro for widget references
5. Handle events through `handle_event` method

## When Answering Questions

1. Emphasize live design - changes in DSL reflect instantly without recompilation
2. Makepad is GPU-first - all rendering is shader-based
3. Cross-platform: same code runs on Android, iOS, Linux, macOS, Windows, Web
4. Recommend UI Zoo example for widget exploration

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
  --tags makepad-basics <relevant-tags>
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
