---
description: Semantic Versioning Rules for AGI Project
trigger: always_on 
---

# Semantic Versioning Policy

## 🌿 Patch Until Limit Protocol (Mandatory)

When determining version bumps for the `package.json` or overall project releases, agents **MUST** follow a restrictive minor-version bumping logic to prevent artificial inflation of version numbers.

### Core Rule: The .99 Threshold

Do NOT advance the MINOR version (the middle number, e.g., `1.5.x` -> `1.6.0`) simply because a new feature was added.
Instead, continue advancing the PATCH version (the third number, e.g., `1.5.8` -> `1.5.9` -> `1.5.10`) for **all** bug fixes and standard minor feature additions until the patch version reaches `99`. 

| Pre-Condition | Normal SemVer Action | **Our Required Action** |
|--------------|----------------------|-----------------------|
| Current: `1.5.9`, Bug Fix | Bump to `1.5.10` | ✅ Bump to `1.5.10` |
| Current: `1.5.10`, Feature Added | Bump to `1.6.0` | 🚫 **Stay on minor.** Bump to `1.5.11` |
| Current: `1.5.99`, Bug Fix or Feature | Bump to `1.6.0` | ✅ Bump to `1.6.0` |

**Exceptions:**
1. A legitimate breaking change (MAJOR version bump to `2.0.0`).
2. An absolute framework overhaul requiring a massive structural shift that mandates a minor bump by explicit author instruction.

**Actionable:**
Before any bump, always check the current version in `package.json`. By default, you only increment the trailing patch number `x.y.PATCH + 1` unless `PATCH` has reached `99`.
