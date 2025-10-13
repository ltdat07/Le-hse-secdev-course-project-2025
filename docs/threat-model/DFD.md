flowchart LR

%% External user
U\[User]

%% Trust boundary: Edge
subgraph Edge\["Trust Boundary: Edge"]
direction TB
API\["FastAPI API"]
AUTH\["Auth (JWT)"]
end

%% Trust boundary: Core
subgraph Core\["Trust Boundary: Core"]
direction TB
DB\["(Database)"]
LOG\["(Log Sink)"]
end

%% Trust boundary: Storage
subgraph Storage\["Trust Boundary: Backups"]
direction TB
BKP\["(Backups)"]
end

%% Data flows
U -->|F1: HTTPS POST /login| API
U -->|F2: HTTPS GET/POST /notes| API
U -->|F3: HTTPS POST /import-md| API

API -->|F4: Verify credentials| AUTH
AUTH -->|F5: Query user| DB
API -->|F6: CRUD notes| DB
DB --- BKP
API -->|F7: Write logs| LOG
API -->|F8: Export .md| U
