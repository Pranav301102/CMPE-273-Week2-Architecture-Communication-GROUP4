# Part B: Async (RabbitMQ)

Event-driven order flow: OrderService publishes **OrderPlaced**; InventoryService consumes, reserves (idempotent), and publishes **InventoryReserved** or **InventoryFailed**; NotificationService consumes **InventoryReserved** and sends confirmation.

## Quick start

```bash
cd async-rabbitmq
docker compose up --build -d
docker compose ps
```

- OrderService HTTP: http://localhost:8001
- RabbitMQ Management: http://localhost:15672 (guest/guest)

Place an order:

```bash
curl -X POST http://localhost:8001/order \
  -H "Content-Type: application/json" \
  -d '{"order_id":"ord-1","item_id":"widget","qty":1,"user_id":"u1"}'
```

## Event flow

- **OrderPlaced** (exchange `order_events`, routing key `order.placed`, queue `order_placed`): published by OrderService; consumed by InventoryService.
- **InventoryReserved** / **InventoryFailed** (exchange `inventory_events`, keys `inventory.reserved` / `inventory.failed`, queue `inventory_reserved`): published by InventoryService; NotificationService consumes only `inventory.reserved`.

## Idempotency strategy

**Where:** InventoryService.

**How:** Before performing a reserve, InventoryService checks whether the message’s `order_id` is already in a processed set (in-memory). If it is, the message is acknowledged and no reserve is performed (idempotent no-op). If not, the service performs the reserve, adds `order_id` to the set, then acks and publishes InventoryReserved or InventoryFailed.

Re-delivering the same OrderPlaced message (e.g. due to broker or consumer restart) therefore does not cause double reservation: the second delivery is skipped and acked.

## Part B test scenarios

### 1. Backlog and recovery

1. Start the stack: `docker compose up -d`.
2. Run the test script (posts orders every second for 90s):
   ```bash
   docker compose run --rm tests python run_backlog_recovery.py
   ```
3. After ~10 orders, stop InventoryService for  60s:
   ```bash
   docker compose stop inventory_service
   ```
4. Let the script keep posting orders (backlog builds in `order_placed`).
5. Restart InventoryService:
   ```bash
   docker compose start inventory_service
   ```
6. Watch logs to see the backlog drain:
   ```bash
   docker compose logs -f inventory_service
   ```

### 2. Idempotency

Publish the same OrderPlaced message twice; inventory should process once and skip the duplicate:

```bash
docker compose run --rm tests python run_idempotency_check.py
docker compose logs inventory_service
```

Look for one “Processed order_id=idempotency-test-order-1” and one “Idempotent skip for order_id=idempotency-test-order-1”.

### 3. Dead letter queue (DLQ) / poison message

Send a malformed message; it should be nack’d and end up in `order_placed_dlq`:

```bash
docker compose run --rm tests python run_dlq_demo.py
```

Then open RabbitMQ Management (http://localhost:15672), go to Queues, and confirm `order_placed_dlq` has one message.

## Stop

```bash
docker compose down
```
