# Anki Cloud Integration Guide

This guide explains how to manage and connect to your headless Anki server running on Google Cloud Platform.

## 📍 Server Information
- **IP Address**: `34.185.196.153`
- **Region**: `europe-west3-c` (Frankfurt, Germany)
- **AnkiConnect Port**: `8765`
- **VNC Port**: `5900`

---

## 🔐 How to Connect via VNC (For Login/GUI Access)

Standard VNC connections can be flaky. The most reliable method is using an **SSH Tunnel**:

1. **Start the SSH Tunnel**:
   Open a terminal and run:
   ```bash
   gcloud compute ssh anki-server --zone=europe-west3-c -- -L 5900:localhost:5900
   ```
   *Keep this terminal window open while you are connected.*

2. **Connect with your VNC Client**:
   - **RealVNC Viewer** (Recommended): Connect to `localhost:5900`
   - **macOS Finder**: `Cmd + K` -> `vnc://localhost:5900`
   - **Password**: `lex_anki_2026`

3. **Login**:
   In the Anki window, click **Sync** and log in to your AnkiWeb account. Once logged in, you can close the VNC client and the tunnel.

---

## 🔄 How to Synchronize

Once logged in via VNC, you can trigger a sync without any GUI open:

### Method 1: CLI (Easiest)
```bash
cd cli
poetry run lex-cli sync
```

### Method 2: API Endpoint
You can call the sync endpoint from any tool:
```bash
curl -X POST http://34.185.196.153:8765/anki_sync
```

---

## 🚀 Deployment & Maintenance

### Redeploying / Changing Regions
If you need to redeploy or move to a different area:
1. Update the `ZONE` in `scripts/deploy-anki-gcloud.sh`.
2. Delete the old instance:
   ```bash
   gcloud compute instances delete anki-server --zone=<OLD_ZONE>
   ```
3. Run the script:
   ```bash
   ./scripts/deploy-anki-gcloud.sh
   ```

### Logs & Debugging
To see what Anki is doing:
```bash
gcloud compute ssh anki-server --zone=europe-west3-c --command="docker logs anki-headless"
```

## 🛠 Troubleshooting
- **Cannot connect via CLI**: Verify the `ANKI_URL` in your `.env` matches the server IP.
- **SQLite Error**: This usually means the data volume has permission issues. The current deployment uses a Docker named volume (`anki_data`) which avoids this.
- **Port 8765 Unreachable**: Ensure the "allow-anki" firewall rule is active in the GCP console.
