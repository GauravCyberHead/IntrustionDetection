from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from kafka import KafkaConsumer
from pymongo import MongoClient
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import threading

app = FastAPI()

# === CORS setup ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to ["http://localhost:3001"] if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === MongoDB setup ===
MONGO_URI = "mongodb+srv://myadmin1:pass123@netguard.arzof6b.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client["SuricataLogsDB"]
collection = db["alerts"]

# === Track active WebSocket clients ===
clients = set()
main_event_loop = None  # stores FastAPI's main event loop


# === WebSocket endpoint ===
@app.websocket("/ws/alerts")
async def alerts_websocket(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    print(f"🔌 Client connected ({len(clients)} total)")

    try:
        while True:
            await asyncio.sleep(1)  # keep connection alive
    except WebSocketDisconnect:
        clients.remove(websocket)
        print(f"❌ Client disconnected ({len(clients)} left)")


# === Broadcast function (async) ===
async def broadcast_alert(alert_data: dict):
    """Send a JSON alert to all connected clients safely."""
    disconnected_clients = []
    for ws in clients:
        try:
            await ws.send_json(alert_data)
        except Exception as e:
            print(f"⚠️ Failed to send alert to a client: {e}")
            disconnected_clients.append(ws)

    for ws in disconnected_clients:
        clients.remove(ws)


# === Kafka listener thread ===
def kafka_listener(loop):
    """Kafka consumer runs in a background thread."""
    consumer = KafkaConsumer(
        "suricata-logs",
        bootstrap_servers=["localhost:9092"],
        auto_offset_reset="latest",
        enable_auto_commit=True,
        group_id="alert-consumer-group",
        value_deserializer=lambda x: json.loads(x.decode("utf-8")),
    )

    print("✅ Kafka consumer started. Waiting for Suricata alerts...")

    for message in consumer:
        log = message.value
        if log.get("event_type") == "alert":
            alert = log.get("alert", {})
            alert_data = {
                "timestamp": log.get("timestamp", ""),
                "src_ip": log.get("src_ip", ""),
                "dest_ip": log.get("dest_ip", ""),
                "proto": log.get("proto", ""),
                "signature": alert.get("signature", "Unknown Alert"),
            }

            print(f"[ALERT] {alert_data}")

            # Insert into MongoDB safely (avoid mutation with ObjectId)
            try:
                collection.insert_one(alert_data.copy())
            except Exception as e:
                print(f"⚠️ Mongo insert failed: {e}")

            # 🔥 Run async broadcast on FastAPI's event loop
            try:
                asyncio.run_coroutine_threadsafe(
                    broadcast_alert(alert_data), loop
                )
            except Exception as e:
                print(f"⚠️ Failed to schedule broadcast: {e}")


# === Startup hook ===
@app.on_event("startup")
async def start_background_tasks():
    """Start Kafka consumer in a background thread when FastAPI starts."""
    global main_event_loop
    main_event_loop = asyncio.get_running_loop()
    thread = threading.Thread(target=kafka_listener, args=(main_event_loop,), daemon=True)
    thread.start()
    print("🚀 Background Kafka listener started")
