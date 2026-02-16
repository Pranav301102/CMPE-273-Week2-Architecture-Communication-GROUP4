"""
Shared event payload field names for OrderPlaced and inventory events.
Services can use these as reference; each service still defines its own payload dict.
"""

# OrderPlaced (order_events, order.placed)
ORDER_PLACED_FIELDS = ("order_id", "item_id", "qty", "user_id")

# InventoryReserved / InventoryFailed (inventory_events)
INVENTORY_EVENT_FIELDS = ("order_id", "status", "user_id")
