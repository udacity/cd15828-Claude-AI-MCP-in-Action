# From a monolithic tool to four single-purpose tools

## The anti-pattern

A first instinct is to expose one broad tool and switch behavior on a parameter:

```python
def manage_inventory(action: str, sku: str, **kwargs) -> dict:
    if action == "check":
        ...
    elif action == "update_price":
        ...
    elif action == "return":
        ...
    elif action == "shrinkage":
        ...
```

`manage_inventory` fails as a tool interface:

- **Misrouting.** The description must cover every action at once, so it is vague. The agent
  cannot tell from the description when to use it versus a built-in, and often defaults to a
  generic tool (e.g., Grep over raw data) instead.
- **Untyped inputs.** `**kwargs` means the schema cannot express which fields each action needs;
  validation collapses into a pile of conditionals.
- **No boundaries.** A read (`check`) and an approval-gated write (`update_price`) sit behind one
  name, so the agent cannot reason about side effects or permissions per action.

## The decomposition

`manage_inventory` is split into four granular tools, each with a typed schema and an explicit
boundary clause (see `inventory_agent/contracts.py`):

| Tool | Responsibility | Side effect |
|------|----------------|-------------|
| `check_stock` | read on-hand quantity for a SKU at a warehouse | none (read-only) |
| `update_price` | change a SKU's price | write, manager-approval gated |
| `process_return` | authorize an RMA for a purchased SKU | write |
| `flag_shrinkage` | open a loss-prevention case | write |

`check_stock` and `process_return` both accept a product id, so their descriptions name each
other in the "do not use for" clause to prevent misrouting. No catch-all tool and no
`action`/`mode`/`operation` selector parameter remains — the server registers exactly these four.
