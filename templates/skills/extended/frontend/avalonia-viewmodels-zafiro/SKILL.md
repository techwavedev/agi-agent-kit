---
name: avalonia-viewmodels-zafiro
description: "Optimal ViewModel and Wizard creation patterns for Avalonia using Zafiro and ReactiveUI."
risk: unknown
source: community
date_added: "2026-02-27"
---

# Avalonia ViewModels with Zafiro

This skill provides a set of best practices and patterns for creating ViewModels, Wizards, and managing navigation in Avalonia applications, leveraging the power of **ReactiveUI** and the **Zafiro** toolkit.

## Core Principles

1.  **Functional-Reactive Approach**: Use ReactiveUI (`ReactiveObject`, `WhenAnyValue`, etc.) to handle state and logic.
2.  **Enhanced Commands**: Utilize `IEnhancedCommand` for better command management, including progress reporting and name/text attributes.
3.  **Wizard Pattern**: Implement complex flows using `SlimWizard` and `WizardBuilder` for a declarative and maintainable approach.
4.  **Automatic Section Discovery**: Use the `[Section]` attribute to register and discover UI sections automatically.
5.  **Clean Composition**: map ViewModels to Views using `DataTypeViewLocator` and manage dependencies in the `CompositionRoot`.

## Guides

- [ViewModels & Commands](viewmodels.md): Creating robust ViewModels and handling commands.
- [Wizards & Flows](wizards.md): Building multi-step wizards with `SlimWizard`.
- [Navigation & Sections](navigation_sections.md): Managing navigation and section-based UIs.
- [Composition & Mapping](composition.md): Best practices for View-ViewModel wiring and DI.

## Example Reference

For real-world implementations, refer to the **Angor** project:
- `CreateProjectFlowV2.cs`: Excellent example of complex Wizard building.
- `HomeViewModel.cs`: Simple section ViewModel using functional-reactive commands.

## When to Use
This skill is applicable to execute the workflow or actions described in the overview.

---

<!-- AGI-INTEGRATION-START -->

## AGI Framework Integration

> **Adapted for [@techwavedev/agi-agent-kit](https://www.npmjs.com/package/@techwavedev/agi-agent-kit)**
> Original source: [antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills)

### Memory-First Protocol

Retrieve prior design decisions (color palettes, typography, spacing scales) to maintain visual consistency across sessions. Cache generated design tokens.

```bash
# Check for prior frontend/design context before starting
python3 execution/memory_manager.py auto --query "design system decisions and component patterns for Avalonia Viewmodels Zafiro"
```

### Storing Results

After completing work, store frontend/design decisions for future sessions:

```bash
python3 execution/memory_manager.py store \
  --content "Design system: adopted 8px grid, Inter font family, HSL color tokens with dark mode support" \
  --type decision --project <project> \
  --tags avalonia-viewmodels-zafiro frontend
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
