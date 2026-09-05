# CampusAuthenticator

An automated, event-driven Windows background service that automatically handles FortiGate captive portal authentication for the NIT Calicut (NITC) campus Wi-Fi network.

Instead of constantly polling the network, CampusAuthenticator listens for native Windows WMI network events. When it detects a connection to the configured campus Wi-Fi, it automatically authenticates in the background and runs the required session keepalive to maintain internet access.

## Features

* **Event-Driven**: Uses WMI to detect Wi-Fi connections and disconnections without an infinite polling loop.
* **Automatic Authentication**: Detects the NITC captive portal and submits the configured credentials automatically.
* **Background Keepalive**: Automatically sends the firewall's keepalive request to maintain the authentication session.
* **Sleep & Hibernate Resilient**: Detects when an existing authentication session has expired and automatically re-authenticates.
* **Configurable**: Wi-Fi SSID, portal IP, portal port, and credentials are loaded from environment variables.
* **Secure Credentials**: Credentials are stored in a local `.env` file rather than being hardcoded in the source code.
* **Daily Log Rotation**: Creates a separate log file for each day.
* **Automatic Log Cleanup**: Logs older than three days are automatically deleted.
* **Zero-Friction**: Can run silently in the background through Windows Task Scheduler.

---

## Project Structure

```text
CampusAuthenticator/
│
├── main.py
├── start.bat
├── stop.bat
├── run_hidden.vbs
├── config.py
├── .env
├── .gitignore
│
├── network/
│   ├── __init__.py
│   ├── wifi.py
│   └── events.py
│
├── portal/
│   ├── __init__.py
│   ├── client.py
│   └── parser.py
│
├── storage/
│   ├── __init__.py
│   └── credentials.py
│
└── logs/
    └── authenticator-YYYY-MM-DD.log
```

---

## Setup Instructions

### 1. Requirements

* **Windows**
* **Python 3.12+**
* An active NITC campus Wi-Fi connection

Install the required Python packages:

```cmd
pip install pywin32 wmi requests beautifulsoup4 python-dotenv
```

---

### 2. Configuration

Configuration is loaded from a `.env` file in the root directory.

Create a file named:

```text
.env
```

and add:

```env
HOSTEL_SSID=your_wifi_ssid

PORTAL_IP=192.168.116.1
PORTAL_PORT=1000

CAMPUS_USERNAME=your_roll_number
CAMPUS_PASSWORD=your_password
```

Replace the values with the appropriate campus network details and your credentials.

For example:

```env
HOSTEL_SSID=Galaxy S21 FE 5G

PORTAL_IP=192.168.116.1
PORTAL_PORT=1000

CAMPUS_USERNAME=your_roll_number
CAMPUS_PASSWORD=your_password
```

The `.env` file contains sensitive information and **must not be committed to Git**.

The repository's `.gitignore` excludes `.env` files from version control.

---

### 3. Clone the Repository

Clone the repository to a permanent location, for example:

```text
D:\Personal Projects\CampusAuthenticator\
```

It is recommended to use a permanent location because Windows Task Scheduler will launch the application from this directory.

---

## Testing Manually

Before configuring Task Scheduler, test the application manually.

Open a Command Prompt in the project directory:

```cmd
cd /d "D:\Personal Projects\CampusAuthenticator"
```

Then run:

```cmd
python main.py
```

CampusAuthenticator will:

1. Check the current Wi-Fi connection.
2. Verify whether the connected SSID matches `HOSTEL_SSID`.
3. Detect the captive portal if authentication is required.
4. Submit the configured credentials.
5. Start the keepalive mechanism after successful authentication.
6. Listen for Windows network events.
7. Stop the keepalive when the Wi-Fi connection is lost.
8. Re-authenticate when necessary.

You can test the event-driven behavior by disconnecting and reconnecting to the configured Wi-Fi network.

---

## Logging

CampusAuthenticator automatically maintains daily log files inside the `logs` directory.

For example:

```text
logs/
├── authenticator-2026-09-05.log
├── authenticator-2026-09-04.log
├── authenticator-2026-09-03.log
└── authenticator-2026-09-02.log
```

Each log entry is timestamped:

```text
[2026-09-05 22:14:31] CampusAuthenticator started

[2026-09-05 22:14:31] Checking initial network state...
[2026-09-05 22:14:31] Already connected to hostel WiFi
```

A new log file is automatically created when the date changes.

Logs older than **three days** are automatically removed, preventing the log directory from growing indefinitely while still retaining recent logs for troubleshooting.

The application handles log rotation internally, so `start.bat` does not need to redirect stdout or stderr to a log file.

---

## Automating it with Windows Task Scheduler

The recommended way to run CampusAuthenticator is as a background task that starts automatically when you log into Windows.

### 1. Open Task Scheduler

Open the Windows Start Menu and search for:

**Task Scheduler**

Click **Create Basic Task...** from the right-hand pane.

### 2. Create the Task

Use:

**Name:**

```text
CampusAuthenticator
```

**Trigger:**

```text
When I log on
```

**Action:**

```text
Start a program
```

### 3. Configure the Program

**Program/script:**

```text
wscript.exe
```

**Add arguments:**

```text
run_hidden.vbs
```

**Start in:**

Paste the exact path to your project directory, for example:

```text
D:\Personal Projects\CampusAuthenticator\
```

Then click **Finish**.

The VBS launcher allows the Python process to run without leaving a visible Command Prompt window.

---

## Background Operation

Once configured, the application runs continuously in the background.

The general lifecycle is:

```text
Windows starts
      │
      ▼
Task Scheduler
      │
      ▼
run_hidden.vbs
      │
      ▼
start.bat
      │
      ▼
main.py
      │
      ▼
Check current Wi-Fi
      │
      ├── Not target Wi-Fi ──► Wait for network event
      │
      └── Target Wi-Fi
              │
              ▼
       Captive Portal Login
              │
              ▼
       Authentication Success
              │
              ▼
       Start Keepalive
              │
              ▼
       Listen for WMI Events
              │
       ┌──────┴──────┐
       ▼             ▼
   Connected     Disconnected
       │             │
       ▼             ▼
  Verify/Auth    Stop Keepalive
                     │
                     ▼
               Wait for reconnect
```

The application does not continuously poll the network. Network state changes are detected through Windows WMI events.

---

## Stopping the Service

If you want to manually stop CampusAuthenticator, use:

```text
stop.bat
```

The shutdown process cleanly stops the keepalive mechanism and logs out of the campus captive portal before terminating the application.

If the application is stopped through Task Scheduler or another forceful mechanism, the clean logout sequence may not run.

---

## Security

The following information should **never be committed to the repository**:

* Campus username
* Campus password
* Other private configuration values

Keep them in:

```text
.env
```

The `.env` file should remain local to your machine.

If sharing the project publicly, make sure that `.env` is excluded by `.gitignore`.

---

## Troubleshooting

### Wi-Fi is connected but authentication does not start

Check that the SSID in `.env` exactly matches the Wi-Fi network name:

```env
HOSTEL_SSID=your_wifi_ssid
```

You can manually verify the detected Wi-Fi information using:

```cmd
python -m network.wifi
```

---

### Authentication is failing

Check the latest log file in:

```text
logs/
```

The application logs authentication attempts and network events with timestamps.

Also verify:

```env
PORTAL_IP=your_captive_portal_ip
PORTAL_PORT=your_captive_portal_port
CAMPUS_USERNAME=your_roll_number
CAMPUS_PASSWORD=your_password
```

---

### The application does not start after Windows login

Check the Task Scheduler configuration:

* Task is enabled.
* Trigger is **When I log on**.
* Program is `wscript.exe`.
* Arguments are `run_hidden.vbs`.
* **Start in** points to the project directory.
* Python is available to the account running the task.

You can also run:

```cmd
start.bat
```

manually to verify that the application itself starts correctly.

---

## License

This project is intended for personal/educational use on the NITC campus network.