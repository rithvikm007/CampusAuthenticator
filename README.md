# CampusAuthenticator

An automated, event-driven Windows background service that automatically handles FortiGate captive portal authentication for the NIT Calicut (NITC) campus Wi-Fi network.

Instead of constantly polling the network, it listens for native Windows WMI network events. When it detects a connection to the configured campus Wi-Fi, it seamlessly authenticates in the background and runs the required session keepalive ping to maintain internet access. 

## Features
- **Event-Driven**: Uses WMI to instantly detect Wi-Fi connections and drops (no infinite polling loops).
- **Background Keepalive**: Automatically sends the `6400s` keepalive ping required by the firewall.
- **Sleep & Hibernate Resilient**: Automatically re-authenticates if the session expires while your laptop is asleep.
- **Zero-Friction**: Runs silently in the background with zero terminal windows once configured via Task Scheduler.

---

## Setup Instructions

### 1. Requirements
- **Windows** (uses `pywin32` and `wmi`)
- **Python 3.12+**

```cmd
pip install pywin32 wmi requests beautifulsoup4 python-dotenv
```

### 2. Configuration
1. Clone the repository to a permanent location (e.g. `D:\Personal Projects\CampusAuthenticator`).
2. Create a `.env` file in the root of the project to securely store your credentials:
   ```env
   CAMPUS_USERNAME=your_roll_number
   CAMPUS_PASSWORD=your_password
   ```
3. Open `config.py` and ensure `HOSTEL_SSID` matches the exact name of your campus Wi-Fi network.

### 3. Testing it Manually
You can test the core functionality by running it from a command prompt:
```cmd
python main.py
```
If you turn your Wi-Fi on and off, you should see the logs actively responding to network events.

---

## Automating it (Windows Task Scheduler)

The best way to use this is as an invisible background service. We've included automation scripts to make this easy.

1. Open the Windows Start Menu and search for **Task Scheduler**.
2. Click **Create Basic Task...** on the right pane.
3. **Name**: `CampusAuthenticator`
4. **Trigger**: Select **When I log on**.
5. **Action**: Select **Start a program**.
6. **Program/script**: type `wscript.exe`
7. **Add arguments**: type `run_hidden.vbs`
8. **Start in**: paste the exact path to your project folder (e.g. `D:\Personal Projects\CampusAuthenticator\`)
9. Click **Finish**.

Now, the script will silently launch every time you turn on your PC. It will write timestamped logs to the `logs/authenticator.log` file so you can check on its health anytime.

### Stopping the Service
If you ever want to forcefully log out of the campus network and terminate the background script, simply double-click the `stop.bat` file. It will cleanly signal the Python daemon to send a `/logout` request to the firewall and exit.
