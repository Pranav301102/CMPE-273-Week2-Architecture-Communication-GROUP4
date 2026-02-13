# CMPE 273 Week2 Assignment 
### Group Member1: Ekant Kapgate, Hei Lam, Shefali Saini and Pranav Jitendra Trivedi

## Part A: Synchronous REST
### 1. Start the system
```bash
cd sync-rest
docker compose up --build -d
docker compose ps
```

### 2. Baseline test (latency table)
```bash
docker compose run --rm tests
```
### 3. Inject 2s delay into Inventory and re-test 
1. Edit sync-rest/docker-compose.yml and set:
```bash
inventory_service:
  environment:
    - DELAY_SEC=2
    - FAIL_MODE=none
  ```
2. Restart inventory (or restart everything):
```bash
docker compose up --build -d
```
3. Run latency test again:
```bash
docker compose run --rm tests
```
### 4. Inject Inventory failure and show OrderService handling (timeout + error)
#### Always fail
1. Edit sync-rest/docker-compose.yml:
```bash
inventory_service:
  environment:
    - DELAY_SEC=0
    - FAIL_MODE=always
```

2. Restart:
```bash
docker compose up --build -d
```
3. Run test:
```bash
docker compose run --rm tests
```
#### Force timeout
1. Keep OrderService timeout at 1s (already set INVENTORY_TIMEOUT_SEC=1.0)
2. Edit sync-rest/docker-compose.yml and Make inventory delay 2s:
```bash
- DELAY_SEC=2
- FAIL_MODE=none
```
3. Restart + test:
```bash
docker compose up --build -d
docker compose run --rm tests
```
### 5. View logs
```bash
docker compose logs -f order_service
# in another terminal if needed:
docker compose logs -f inventory_service
```
### 6. Stop Part A
```bash
docker compose down
```
