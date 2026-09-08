# CampusAuthenticator

An automated, event-driven Windows background application that handles FortiGate captive portal authentication for the NIT Calicut (NITC) campus Wi-Fi network.

Instead of continuously polling the network, CampusAuthenticator listens for native Windows WMI network events. When it detects a connection to the configured campus Wi-Fi, it automatically authenticates when necessary and maintains the FortiGate authentication session using the required keepalive mechanism.

CampusAuthenticator also persists the FortiGate session information locally, allowing it to attempt to recover an existing authentication session after the application is restarted or the system reconnects to the network.

## Features

* **Event-Driven**: Uses WMI to detect Wi-Fi connections and disconnections without an infinite polling loop.

* **Automatic Authentication**: Detects the NITC captive portal and submits the configured credentials automatically.

* **Session Persistence & Recovery**: Persists the FortiGate keepalive URL locally and attempts to recover the existing authentication session when the application restarts or reconnects.

* **Background Keepalive**: Automatically sends the firewall's keepalive request to maintain the authentication session.

* **Sleep & Hibernate Resilient**: Detects changes to the authentication state after waking from Sleep/Hibernate and attempts session recovery or re-authentication when necessary.

* **Configurable**: Wi-Fi SSID, portal IP, portal port, and credentials are loaded from environment variables.

* **Secure Credentials**: Credentials are stored in a local `.env` file rather than being hardcoded in the source code.

* **Desktop Notifications**: Displays Windows notifications for important authentication and logout events.

* **Daily Log Rotation**: Creates a separate log file for each day.

* **Automatic Log Cleanup**: Logs older than three days are automatically deleted.

* **Zero-Friction**: Can run silently in the background through Windows Task Scheduler.

---

## Project Structure

```text
CampusAuthenticator/
│
├── main.py
├── notifications.py
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
│   └── session.py
│
└── logs/
    └── authenticator-YYYY-MM-DD.log
```

The following files are generated or contain sensitive information and should not be committed to the repository:

```text
.env
storage/session.json
logs/
```

---

## Setup Instructions

### 1. Requirements

* **Windows**
* **Python 3.12+**
* An active NITC campus Wi-Fi connection

Install the required Python packages:

```cmd
pip install pywin32 wmi requests beautifulsoup4 python-dotenv windows-toasts
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

Replace the placeholder values with the appropriate campus network details and your credentials.

The `.env` file contains sensitive information and **must not be committed to Git**.

The repository's `.gitignore` excludes `.env` files from version control.

---

### 3. Clone the Repository

Clone the repository to a permanent location on your system.

A permanent location is recommended because Windows Task Scheduler will launch the application from the project directory.

---

## Testing Manually

Before configuring Task Scheduler, test the application manually.

Open a Command Prompt in the project directory:

```cmd
cd CampusAuthenticator
```

Then run:

```cmd
python main.py
```

CampusAuthenticator will:

1. Check the current Wi-Fi connection.
2. Verify whether the connected SSID matches `HOSTEL_SSID`.
3. Check whether a previously persisted FortiGate session exists.
4. Attempt to recover the previous session when possible.
5. Detect the captive portal if authentication is required.
6. Submit the configured credentials.
7. Persist the new keepalive URL after successful authentication.
8. Start the keepalive mechanism.
9. Listen for Windows network events.
10. Stop the keepalive when the Wi-Fi connection is lost.
11. Attempt to log out of the FortiGate session when possible.
12. Re-authenticate when necessary.

You can test the event-driven behavior by disconnecting and reconnecting to the configured Wi-Fi network.

---

## Session Persistence

CampusAuthenticator persists the FortiGate keepalive URL in:

```text
storage/session.json
```

The session lifecycle is:

```text
Successful Login
       │
       ▼
FortiGate returns keepalive URL
       │
       ▼
Save keepalive URL
       │
       ▼
storage/session.json
       │
       ▼
Start Keepalive
```

When the application starts again:

```text
Application Start
       │
       ▼
Load session.json
       │
       ▼
Previous session available?
       │
   ┌───┴────┐
   │        │
  Yes       No
   │        │
   ▼        ▼
Attempt     Check Internet
Recovery
   │
 ┌─┴──────┐
 │        │
Valid    Invalid
 │        │
 ▼        ▼
Start    Clear old
Keepalive session
 │        │
 └───┬────┘
     ▼
Check Internet / Authenticate if necessary
```

The persisted keepalive URL represents a specific FortiGate authentication session.

If the session is still active, CampusAuthenticator can resume using that session without performing a new login.

If the session has expired or been invalidated, the stored session information is cleared and the application falls back to the normal authentication flow when required.

Session persistence does **not** store the campus username or password. Credentials remain in `.env`.

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

Enter the absolute path to the directory where you cloned the repository.

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
      ├── Not target Wi-Fi ──────────► Wait for network event
      │
      └── Target Wi-Fi
              │
              ▼
       Check persisted session
              │
        ┌─────┴─────┐
        │           │
   Session found   No session
        │           │
        ▼           ▼
  Try recovery   Check Internet
        │           │
     ┌──┴───┐    ┌──┴──────┐
     │      │    │         │
   Valid  Invalid Yes       No
     │      │    │         │
     ▼      ▼    ▼         ▼
 Keepalive Clear  CONNECTED Fresh Login
     │     session    │
     │      │         │
     └──────┴─────────┘
              │
              ▼
       Listen for WMI Events
              │
       ┌──────┴──────┐
       ▼             ▼
   Connected     Disconnected
       │             │
       ▼             ▼
 Verify/Recover   Stop Keepalive
       │             │
       │             ▼
       │          Attempt Logout
       │             │
       └─────────────┴──────► Wait for reconnect
```

The application does not continuously poll the network. Network state changes are detected through Windows WMI events.

---

## Stopping the Service

If you want to manually stop CampusAuthenticator, use:

```text
stop.bat
```

The normal shutdown process stops the keepalive mechanism and attempts to log out of the campus captive portal before terminating the application.

When logout succeeds, the persisted session information is removed.

If the application is stopped through Task Scheduler, terminated forcefully, or otherwise unable to perform its normal shutdown sequence, the clean logout sequence may not run.

In such cases, the persisted session information may remain so that the application can attempt session recovery the next time it starts.

---

## Security

The following information should **never be committed to the repository**:

* Campus username
* Campus password
* FortiGate session tokens
* Other private configuration values

Credentials are stored locally in:

```text
.env
```

The current FortiGate session information is stored locally in:

```text
storage/session.json
```

Both files should remain local to your machine.

If sharing the project publicly, make sure both are excluded by `.gitignore`.

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

### The application finds a previous session but cannot recover it

Check the latest log file in:

```text
logs/
```

You may see:

```text
Previous session found — attempting session recovery...
Attempting to recover previous FortiGate session...
Previous session could not be recovered
```

If the persisted session has expired, the application will clear the stale session information and fall back to checking Internet connectivity or performing a fresh authentication when required.

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
