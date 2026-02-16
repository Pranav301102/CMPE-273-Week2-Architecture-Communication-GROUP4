# Part B: Async RabbitMQ – Testing Guide

How to test the async RabbitMQ flow and cover all Part B use cases.

---

## Prerequisites

From the repo root:

```bash
cd cmpe273-comm-models-lab/async-rabbitmq
docker compose up --build -d
docker compose ps   # all services running
```

---

## Use Cases and How to Test

### 1. Happy path (end-to-end order flow)

**What:** Order accepted → OrderPlaced → reserve → InventoryReserved → notification sent.

**How to test:**

```bash
curl -X POST http://localhost:8001/order \
  -H "Content-Type: application/json" \
  -d '{"order_id":"happy-1","item_id":"widget","qty":1,"user_id":"u1"}'
```

**Expect:** HTTP 202 and `{"status":"accepted","order_id":"happy-1"}`.

**Verify:**

- **InventoryService:** one log line like `Processed order_id=happy-1 -> reserved`
- **NotificationService:** one log line like `Send confirmation for order_id=happy-1 user_id=u1`
- **RabbitMQ UI** (http://localhost:15672): queue `order_placed` drains; no buildup

---

### 2. Backlog and recovery

**What:** While InventoryService is down, orders still get accepted and messages pile up in `order_placed`; when InventoryService comes back, the backlog is drained.

**How to test:**

1. Terminal 1 – start the script (posts for 90s):
   ```bash
   docker compose run --rm tests python run_backlog_recovery.py
   ```
2. After ~10 lines of output, Terminal 2 – stop inventory for 60s:
   ```bash
   docker compose stop inventory_service
   ```
3. Let the script keep running (~60s). Orders keep getting 202; backlog grows in `order_placed`.
4. Terminal 2 – start inventory again:
   ```bash
   docker compose start inventory_service
   ```
5. Terminal 2 – watch inventory drain the backlog:
   ```bash
   docker compose logs -f inventory_service
   ```

**Expect:** After restart, InventoryService logs show many `Processed order_id=...` lines until the queue is empty. In RabbitMQ UI, `order_placed` message count goes to 0.

**Optional:** Before restart, open RabbitMQ UI and note `order_placed` message count; after drain, confirm it's 0.

---

### 3. Idempotency (no double reserve)

**What:** Same OrderPlaced delivered twice → reserve happens once, second time is skipped.

**How to test:**

```bash
docker compose run --rm tests python run_idempotency_check.py
docker compose logs inventory_service
```

**Expect in logs:**

- One line: `Processed order_id=idempotency-test-order-1 -> reserved` (or `-> failed` if FAIL_MODE is set).
- One line: `Idempotent skip for order_id=idempotency-test-order-1`.

So: two deliveries, one reserve.

---

### 4. DLQ / poison message

**What:** Malformed message is nack'd and moved to DLQ (or published to DLQ by the consumer).

**How to test:**

```bash
docker compose run --rm tests python run_dlq_demo.py
```

**Expect:**

- InventoryService log: `Poison message (invalid JSON): ...`
- RabbitMQ UI → Queues → `order_placed_dlq`: **1 message** (body something like `not valid json {`)

**Optional CLI check:**

```bash
docker compose exec rabbitmq rabbitmqctl list_queues name messages
```

`order_placed_dlq` should show 1 message.

---

### 5. Inventory failure (InventoryFailed, no notification)

**What:** Reserve "fails" → InventoryFailed is published; NotificationService only consumes InventoryReserved, so no confirmation is sent.

**How to test:**

1. Set failure mode and restart inventory:
   - In `docker-compose.yml`, under `inventory_service` environment, set: `FAIL_MODE=always`
   ```bash
   docker compose up -d inventory_service
   ```
2. Place an order:
   ```bash
   curl -X POST http://localhost:8001/order \
     -H "Content-Type: application/json" \
     -d '{"order_id":"fail-1","item_id":"x","qty":1,"user_id":"u1"}'
   ```

**Expect:**

- OrderService: 202 (order accepted and OrderPlaced published).
- InventoryService: `Processed order_id=fail-1 -> failed`.
- NotificationService: **no** "Send confirmation for order_id=fail-1" (it only reacts to `inventory.reserved`).

---

## Suggested order for a full run

| Order | Use case              | Command / steps |
|-------|------------------------|-----------------|
| 1     | Happy path            | `curl` POST /order once, check inventory + notification logs |
| 2     | Idempotency           | `docker compose run --rm tests python run_idempotency_check.py` then `docker compose logs inventory_service` |
| 3     | DLQ                   | `docker compose run --rm tests python run_dlq_demo.py` then check `order_placed_dlq` in UI |
| 4     | Backlog & recovery    | Run `run_backlog_recovery.py`, stop inventory 60s, start again, watch logs |
| 5     | Inventory failure     | Set `FAIL_MODE=always`, restart inventory, POST one order, confirm no notification log |

---

## Checklist for "all use cases covered"

- [ ] **Happy path:** 202 from OrderService, "reserved" in inventory logs, "Send confirmation" in notification logs.
- [ ] **Backlog/recovery:** Backlog visible in `order_placed` while inventory is stopped; after restart, backlog drains and queue goes to 0.
- [ ] **Idempotency:** Two messages, same order_id; logs show one "Processed" and one "Idempotent skip".
- [ ] **DLQ:** One poison message; `order_placed_dlq` has 1 message in RabbitMQ UI.
- [ ] **Inventory failure:** With FAIL_MODE=always, order still 202, inventory logs "failed", notification has no confirmation for that order.
