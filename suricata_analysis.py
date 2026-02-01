from kafka import KafkaConsumer
from pymongo import MongoClient
import json

# Kafka & Mongo Config
KAFKA_TOPIC = "suricata-logs"
KAFKA_SERVER = "localhost:9092"
MONGO_URI = "mongodb+srv://myadmin1:pass123@netguard.arzof6b.mongodb.net/?retryWrites=true&w=majority"

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client["SuricataLogsDB"]
collection = db["alerts"]

consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=[KAFKA_SERVER],
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='log-consumer-group',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

print("🎯 Kafka consumer started. Listening for Suricata logs...")

for message in consumer:
    log = message.value
    event_type = log.get("event_type")

    if event_type == "alert":
        alert = log.get("alert", {})
        timestamp = log.get("timestamp", "")
        src_ip = log.get("src_ip", "")
        dest_ip = log.get("dest_ip", "")
        proto = log.get("proto", "")
        signature = alert.get("signature", "Unknown Alert")

        print(f"[ALERT] {timestamp} {src_ip} -> {dest_ip} [{proto}] {signature}")

        # Save alert to MongoDB
        collection.insert_one({
            "timestamp": timestamp,
            "src_ip": src_ip,
            "dest_ip": dest_ip,
            "proto": proto,
            "signature": signature
        })

    else:
        print(f"[LOG] {log.get('timestamp')} {event_type} {log.get('src_ip','')} -> {log.get('dest_ip','')}")
