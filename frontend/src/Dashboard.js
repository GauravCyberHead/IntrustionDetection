import React, { useEffect, useState } from "react";

export default function Dashboard() {
  const [alerts, setAlerts] = useState([]);
  const [status, setStatus] = useState("🔌 Connecting...");

  useEffect(() => {
    let socket;

    const connect = () => {
      // 👉 Use localhost (or your LAN IP if React runs on another device)
      const ws = new WebSocket("ws://localhost:8000/ws/alerts");

      ws.onopen = () => {
        console.log("✅ WebSocket connected");
        setStatus("🟢 Connected to backend");
      };

      ws.onclose = () => {
        console.warn("❌ WebSocket disconnected — retrying in 3s...");
        setStatus("🔴 Disconnected — reconnecting...");
        setTimeout(connect, 3000);
      };

      ws.onerror = (error) => {
        console.error("⚠️ WebSocket error:", error);
        setStatus("⚠️ Connection error");
      };

      ws.onmessage = (event) => {
        try {
          const alert = JSON.parse(event.data);
          console.log("📩 Received alert:", alert);

          // Only add if it has required fields
          if (alert.timestamp && alert.src_ip && alert.dest_ip && alert.signature) {
            setAlerts((prev) => [alert, ...prev].slice(0, 100));
          }
        } catch (err) {
          console.error("❌ Invalid alert format:", err);
        }
      };

      socket = ws;
    };

    connect();
    return () => socket && socket.close();
  }, []);

  return (
    <div style={{ padding: "20px", backgroundColor: "#111", color: "#fff", minHeight: "100vh" }}>
      <h2 style={{ marginBottom: "10px" }}>🚨 Suricata Network Alerts Dashboard</h2>
      <div
        style={{
          marginBottom: "15px",
          padding: "6px 12px",
          borderRadius: "8px",
          display: "inline-block",
          backgroundColor: status.includes("🟢") ? "#093" : "#933",
        }}
      >
        {status}
      </div>

      <table style={{ width: "100%", borderCollapse: "collapse", backgroundColor: "#1b1b1b" }}>
        <thead>
          <tr style={{ backgroundColor: "#333", color: "#fff" }}>
            <th style={{ padding: "8px", border: "1px solid #444" }}>Timestamp</th>
            <th style={{ padding: "8px", border: "1px solid #444" }}>Source IP</th>
            <th style={{ padding: "8px", border: "1px solid #444" }}>Destination IP</th>
            <th style={{ padding: "8px", border: "1px solid #444" }}>Protocol</th>
            <th style={{ padding: "8px", border: "1px solid #444" }}>Signature</th>
          </tr>
        </thead>
        <tbody>
          {alerts.length > 0 ? (
            alerts.map((alert, index) => (
              <tr
                key={index}
                style={{
                  backgroundColor:
                    alert.proto === "ICMP"
                      ? "#ffcccc"
                      : alert.proto === "TCP"
                      ? "#cce5ff"
                      : "#e8e8e8",
                  color: "#000",
                }}
              >
                <td style={{ border: "1px solid #444", padding: "6px" }}>
                  {new Date(alert.timestamp).toLocaleString()}
                </td>
                <td style={{ border: "1px solid #444", padding: "6px" }}>{alert.src_ip}</td>
                <td style={{ border: "1px solid #444", padding: "6px" }}>{alert.dest_ip}</td>
                <td style={{ border: "1px solid #444", padding: "6px" }}>{alert.proto}</td>
                <td style={{ border: "1px solid #444", padding: "6px" }}>{alert.signature}</td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan="5" style={{ textAlign: "center", padding: "10px", color: "#aaa" }}>
                No alerts yet
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
