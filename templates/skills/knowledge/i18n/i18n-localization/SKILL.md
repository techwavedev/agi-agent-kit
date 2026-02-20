---
name: i18n-localization
description: Internationalization and localization patterns. Detecting hardcoded strings, managing translations, locale files, RTL support.
allowed-tools: Read, Glob, Grep
---

# i18n & Localization

> Internationalization (i18n) and Localization (L10n) best practices.

---

## 1. Core Concepts

| Term | Meaning |
|------|---------|
| **i18n** | Internationalization - making app translatable |
| **L10n** | Localization - actual translations |
| **Locale** | Language + Region (en-US, tr-TR) |
| **RTL** | Right-to-left languages (Arabic, Hebrew) |

---

## 2. When to Use i18n

| Project Type | i18n Needed? |
|--------------|--------------|
| Public web app | ✅ Yes |
| SaaS product | ✅ Yes |
| Internal tool | ⚠️ Maybe |
| Single-region app | ⚠️ Consider future |
| Personal project | ❌ Optional |

---

## 3. Implementation Patterns

### React (react-i18next)

```tsx
import { useTranslation } from 'react-i18next';

function Welcome() {
  const { t } = useTranslation();
  return <h1>{t('welcome.title')}</h1>;
}
```

### Next.js (next-intl)

```tsx
import { useTranslations } from 'next-intl';

export default function Page() {
  const t = useTranslations('Home');
  return <h1>{t('title')}</h1>;
}
```

### Python (gettext)

```python
from gettext import gettext as _

print(_("Welcome to our app"))
```

---

## 4. File Structure

```
locales/
├── en/
│   ├── common.json
│   ├── auth.json
│   └── errors.json
├── tr/
│   ├── common.json
│   ├── auth.json
│   └── errors.json
└── ar/          # RTL
    └── ...
```

---

## 5. Best Practices

### DO ✅

- Use translation keys, not raw text
- Namespace translations by feature
- Support pluralization
- Handle date/number formats per locale
- Plan for RTL from the start
- Use ICU message format for complex strings

### DON'T ❌

- Hardcode strings in components
- Concatenate translated strings
- Assume text length (German is 30% longer)
- Forget about RTL layout
- Mix languages in same file

---

## 6. Common Issues

| Issue | Solution |
|-------|----------|
| Missing translation | Fallback to default language |
| Hardcoded strings | Use linter/checker script |
| Date format | Use Intl.DateTimeFormat |
| Number format | Use Intl.NumberFormat |
| Pluralization | Use ICU message format |

---

## 7. RTL Support

```css
/* CSS Logical Properties */
.container {
  margin-inline-start: 1rem;  /* Not margin-left */
  padding-inline-end: 1rem;   /* Not padding-right */
}

[dir="rtl"] .icon {
  transform: scaleX(-1);
}
```

---

## 8. Checklist

Before shipping:

- [ ] All user-facing strings use translation keys
- [ ] Locale files exist for all supported languages
- [ ] Date/number formatting uses Intl API
- [ ] RTL layout tested (if applicable)
- [ ] Fallback language configured
- [ ] No hardcoded strings in components

---

## Script

| Script | Purpose | Command |
|--------|---------|---------|
| `scripts/i18n_checker.py` | Detect hardcoded strings & missing translations | `python scripts/i18n_checker.py <project_path>` |

## AGI Framework Integration

### Qdrant Memory Integration

Before executing complex tasks with this skill:
```bash
python3 execution/memory_manager.py auto --query "<task summary>"
```

**Decision Tree:**
- **Cache hit?** Use cached response directly — no need to re-process.
- **Memory match?** Inject `context_chunks` into your reasoning.
- **No match?** Proceed normally, then store results:

```bash
python3 execution/memory_manager.py store \
  --content "Description of what was decided/solved" \
  --type decision \
  --tags i18n-localization <relevant-tags>
```

> **Note:** Storing automatically updates both Vector (Qdrant) and Keyword (BM25) indices.

### Agent Team Collaboration

- **Strategy**: This skill communicates via the shared memory system.
- **Orchestration**: Invoked by `orchestrator` via intelligent routing.
- **Context Sharing**: Always read previous agent outputs from memory before starting.

### Local LLM Support

When available, use local Ollama models for embedding and lightweight inference:
- Embeddings: `nomic-embed-text` via Qdrant memory system
- Lightweight analysis: Local models reduce API costs for repetitive patterns
