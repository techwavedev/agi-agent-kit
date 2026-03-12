---
name: wordpress-woocommerce-development
description: "WooCommerce store development workflow covering store setup, payment integration, shipping configuration, and customization."
category: granular-workflow-bundle
risk: safe
source: personal
date_added: "2026-02-27"
---

# WordPress WooCommerce Development Workflow

## Overview

Specialized workflow for building WooCommerce stores including setup, payment gateway integration, shipping configuration, custom product types, and store optimization.

## When to Use This Workflow

Use this workflow when:
- Setting up WooCommerce stores
- Integrating payment gateways
- Configuring shipping methods
- Creating custom product types
- Building subscription products

## Workflow Phases

### Phase 1: Store Setup

#### Skills to Invoke
- `app-builder` - Project scaffolding
- `wordpress-penetration-testing` - WordPress patterns

#### Actions
1. Install WooCommerce
2. Run setup wizard
3. Configure store settings
4. Set up tax rules
5. Configure currency

#### Copy-Paste Prompts
```
Use @app-builder to set up WooCommerce store
```

### Phase 2: Product Configuration

#### Skills to Invoke
- `wordpress-penetration-testing` - WooCommerce patterns

#### Actions
1. Create product categories
2. Add product attributes
3. Configure product types
4. Set up variable products
5. Add product images

#### Copy-Paste Prompts
```
Use @wordpress-penetration-testing to configure WooCommerce products
```

### Phase 3: Payment Integration

#### Skills to Invoke
- `payment-integration` - Payment processing
- `stripe-integration` - Stripe
- `paypal-integration` - PayPal

#### Actions
1. Choose payment gateways
2. Configure Stripe
3. Set up PayPal
4. Add offline payments
5. Test payment flows

#### Copy-Paste Prompts
```
Use @stripe-integration to integrate Stripe payments
```

```
Use @paypal-integration to integrate PayPal
```

### Phase 4: Shipping Configuration

#### Skills to Invoke
- `wordpress-penetration-testing` - WooCommerce shipping

#### Actions
1. Set up shipping zones
2. Configure shipping methods
3. Add flat rate shipping
4. Set up free shipping
5. Integrate carriers

#### Copy-Paste Prompts
```
Use @wordpress-penetration-testing to configure shipping
```

### Phase 5: Store Customization

#### Skills to Invoke
- `frontend-developer` - Store customization
- `frontend-design` - Store design

#### Actions
1. Customize product pages
2. Modify cart page
3. Style checkout flow
4. Create custom templates
5. Add custom fields

#### Copy-Paste Prompts
```
Use @frontend-developer to customize WooCommerce templates
```

### Phase 6: Extensions

#### Skills to Invoke
- `wordpress-penetration-testing` - WooCommerce extensions

#### Actions
1. Install required extensions
2. Configure subscriptions
3. Set up bookings
4. Add memberships
5. Integrate marketplace

#### Copy-Paste Prompts
```
Use @wordpress-penetration-testing to configure WooCommerce extensions
```

### Phase 7: Optimization

#### Skills to Invoke
- `web-performance-optimization` - Performance
- `database-optimizer` - Database optimization

#### Actions
1. Optimize product images
2. Enable caching
3. Optimize database
4. Configure CDN
5. Set up lazy loading

#### Copy-Paste Prompts
```
Use @web-performance-optimization to optimize WooCommerce store
```

### Phase 8: Testing

#### Skills to Invoke
- `playwright-skill` - E2E testing
- `test-automator` - Test automation

#### Actions
1. Test checkout flow
2. Verify payment processing
3. Test email notifications
4. Check mobile experience
5. Performance testing

#### Copy-Paste Prompts
```
Use @playwright-skill to test WooCommerce checkout flow
```

## Quality Gates

- [ ] Products displaying correctly
- [ ] Checkout flow working
- [ ] Payments processing
- [ ] Shipping calculating
- [ ] Emails sending
- [ ] Mobile responsive

## Related Workflow Bundles

- `wordpress` - WordPress development
- `wordpress-theme-development` - Theme development
- `wordpress-plugin-development` - Plugin development
- `payment-integration` - Payment processing

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
  --tags wordpress-woocommerce-development <relevant-tags>
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
