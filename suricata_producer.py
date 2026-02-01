import json
from kafka import KafkaProducer
import os
import time

KAFKA_TOPIC = "suricata-logs"
KAFKA_SERVER = "localhost:9092"
EVE_JSON_PATH = "/var/log/suricata/eve.json"

producer = KafkaProducer(
    bootstrap_servers=[KAFKA_SERVER],
    value_serializer=lambda x: json.dumps(x).encode('utf-8')
)

print("🎯 Kafka producer started. Streaming Suricata logs...")

def tail_f(filename):
    with open(filename, "r") as f:
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if not line:
                time.sleep(0.1)
                continue
            yield line

for line in tail_f(EVE_JSON_PATH):
    try:
        log = json.loads(line)
    except json.JSONDecodeError:
        continue

    producer.send(KAFKA_TOPIC, value=log)
    producer.flush()
    print(f"[LOG PRODUCED] {log.get('timestamp')} {log.get('event_type')} {log.get('src_ip','')} -> {log.get('dest_ip','')}")
