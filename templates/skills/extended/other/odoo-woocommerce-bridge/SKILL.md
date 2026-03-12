---
name: odoo-woocommerce-bridge
description: "Sync Odoo with WooCommerce: products, inventory, orders, and customers via WooCommerce REST API and Odoo external API."
---

# Odoo ↔ WooCommerce Bridge

## Overview

This skill guides you through building a reliable sync bridge between Odoo (the back-office ERP) and WooCommerce (the WordPress online store). It covers product catalog sync, real-time inventory updates, order import, and customer record management.

## When to Use This Skill

- Running a WooCommerce store with Odoo for inventory and fulfillment.
- Automatically pulling WooCommerce orders into Odoo as sale orders.
- Keeping WooCommerce product stock in sync with Odoo's warehouse.
- Mapping WooCommerce order statuses to Odoo delivery states.

## How It Works

1. **Activate**: Mention `@odoo-woocommerce-bridge` and describe your sync requirements.
2. **Design**: Get the field mapping table between WooCommerce and Odoo objects.
3. **Build**: Receive Python integration scripts using the WooCommerce REST API.

## Field Mapping: WooCommerce → Odoo

| WooCommerce | Odoo |
|---|---|
| `products` | `product.template` + `product.product` |
| `orders` | `sale.order` + `sale.order.line` |
| `customers` | `res.partner` |
| `stock_quantity` | `stock.quant` |
| `sku` | `product.product.default_code` |
| `order status: processing` | Sale Order: `sale` (confirmed) |
| `order status: completed` | Delivery: `done` |

## Examples

### Example 1: Pull WooCommerce Orders into Odoo (Python)

```python
from woocommerce import API
import xmlrpc.client

# WooCommerce client
wcapi = API(
    url="https://mystore.com",
    consumer_key="ck_xxxxxxxxxxxxx",
    consumer_secret="cs_xxxxxxxxxxxxx",
    version="wc/v3"
)

# Odoo client
odoo_url = "https://myodoo.example.com"
db, uid, pwd = "my_db", 2, "api_key"
models = xmlrpc.client.ServerProxy(f"{odoo_url}/xmlrpc/2/object")

def sync_orders():
    # Get unprocessed WooCommerce orders
    orders = wcapi.get("orders", params={"status": "processing", "per_page": 50}).json()

    for wc_order in orders:
        # Find or create Odoo partner
        email = wc_order['billing']['email']
        partner = models.execute_kw(db, uid, pwd, 'res.partner', 'search',
            [[['email', '=', email]]])
        if not partner:
            partner_id = models.execute_kw(db, uid, pwd, 'res.partner', 'create', [{
                'name': f"{wc_order['billing']['first_name']} {wc_order['billing']['last_name']}",
                'email': email,
                'phone': wc_order['billing']['phone'],
                'street': wc_order['billing']['address_1'],
                'city': wc_order['billing']['city'],
            }])
        else:
            partner_id = partner[0]

        # Create Sale Order in Odoo
        order_lines = []
        for item in wc_order['line_items']:
            product = models.execute_kw(db, uid, pwd, 'product.product', 'search',
                [[['default_code', '=', item['sku']]]])
            if product:
                order_lines.append((0, 0, {
                    'product_id': product[0],
                    'product_uom_qty': item['quantity'],
                    'price_unit': float(item['price']),
                }))

        models.execute_kw(db, uid, pwd, 'sale.order', 'create', [{
            'partner_id': partner_id,
            'client_order_ref': f"WC-{wc_order['number']}",
            'order_line': order_lines,
        }])

        # Mark WooCommerce order as on-hold (processed by Odoo)
        wcapi.put(f"orders/{wc_order['id']}", {"status": "on-hold"})
```

### Example 2: Push Odoo Stock to WooCommerce

```python
def sync_inventory_to_woocommerce():
    # Get all products with a SKU from Odoo
    products = models.execute_kw(db, uid, pwd, 'product.product', 'search_read',
        [[['default_code', '!=', False], ['type', '=', 'product']]],
        {'fields': ['default_code', 'qty_available']}
    )

    for product in products:
        sku = product['default_code']
        qty = int(product['qty_available'])

        # Update WooCommerce by SKU
        wc_products = wcapi.get("products", params={"sku": sku}).json()
        if wc_products:
            wcapi.put(f"products/{wc_products[0]['id']}", {
                "stock_quantity": qty,
                "manage_stock": True,
            })
```

## Best Practices

- ✅ **Do:** Use **SKU** as the unique identifier linking WooCommerce products to Odoo products.
- ✅ **Do:** Run inventory sync on a **schedule** (every 15-30 min) rather than real-time to avoid rate limits.
- ✅ **Do:** Log all API calls and errors to a database table for debugging.
- ❌ **Don't:** Process the same WooCommerce order twice — flag it as processed immediately after import.
- ❌ **Don't:** Sync draft or cancelled WooCommerce orders to Odoo — filter by `status = processing` or `completed`.

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
  --tags odoo-woocommerce-bridge <relevant-tags>
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
