# CampusAuthenticator

CampusAuthenticator is a Windows desktop application that automatically authenticates a device to the NIT Calicut campus network through its FortiGate captive portal.

It runs as a system-tray application, monitors network connectivity, detects the campus captive portal, authenticates using saved credentials, and maintains the authenticated session automatically.

---

## Windows Release

A packaged Windows version of CampusAuthenticator is available through the project's GitHub Releases.

The packaged application is distributed as a self-contained Windows application and **does not require Python to be installed**.

### Installation

1. Download the latest Windows `.zip` release from GitHub Releases.
2. Extract the ZIP file to a location of your choice.
3. Open the extracted `CampusAuthenticator` folder.
4. Run:

```text
CampusAuthenticator.exe
```

5. On first launch, open **Settings** and enter your NITC campus credentials.

The application runs in the Windows system tray after startup.

### Packaged Application Structure

The packaged application uses PyInstaller's onedir format:

```text
CampusAuthenticator/
├── CampusAuthenticator.exe
└── _internal/
    ├── assets/
    └── ...
```

The `_internal` directory is required and must remain alongside `CampusAuthenticator.exe`.

Do not move or remove files from the extracted application directory.

### Runtime Data

The packaged application stores its writable runtime data separately from the application files:

```text
%LOCALAPPDATA%\CampusAuthenticator\
├── storage\
│   ├── config.json
│   └── session.json
└── logs\
    └── authenticator-YYYY-MM-DD.log
```

This allows the packaged application to keep credentials, session information, and logs without modifying the application installation directory.

---

## Features

* **Automatic campus network detection**

  * Detects the active physical network interface.
  * Supports both Wi-Fi and Ethernet connections.
  * Ignores virtual, VPN, and other non-physical network adapters.

* **Automatic captive portal authentication**

  * Detects when the campus network is behind the FortiGate captive portal.
  * Discovers the portal endpoint dynamically from the captive-portal redirect.
  * Authenticates using the credentials configured in the application.

* **Session recovery**

  * Persists the portal keepalive URL locally.
  * Attempts to recover an existing authenticated session when possible.

* **Automatic keepalive**

  * Periodically refreshes the authenticated session.
  * Keeps the campus connection alive without requiring manual interaction.

* **GUI and system tray**

  * Displays the current authentication and network state.
  * Provides login, logout, refresh, settings, and exit controls.
  * Continues running in the system tray.

* **Credential management**

  * Campus credentials can be configured through the Settings page.
  * Changing credentials while authenticated automatically handles the existing session and authenticates using the new credentials.

* **Windows notifications**

  * Authentication and connection events can be surfaced through Windows toast notifications.

* **Logging**

  * Application activity is written to dated log files.
  * Old logs are automatically cleaned up.

---

## How It Works

The application continuously monitors the system's network state and coordinates the authentication process through the following general flow:

```text
Network connection
       │
       ▼
Detect active physical interface
       │
       ▼
Check campus network connectivity
       │
       ├── Internet available
       │
       ├── No network
       │
       └── Captive portal detected
                    │
                    ▼
             Discover portal
                    │
                    ▼
             Authenticate
                    │
                    ▼
          Save session information
                    │
                    ▼
             Start keepalive
```

The application maintains four main authentication states:

```text
DISCONNECTED
CONNECTED
AUTHENTICATING
AUTHENTICATED
```

These states are exposed to the GUI and used to control the application's behavior.

---

## Network Detection

CampusAuthenticator does not require the user to configure a Wi-Fi SSID.

Instead, it determines the active physical network interface using Windows network information.

The application:

1. Examines the system's IPv4 routing table.
2. Finds the active default route.
3. Resolves the corresponding network adapter.
4. Checks whether the adapter is connected.
5. Filters out virtual, VPN, Bluetooth, and other non-physical adapters.
6. Determines whether the active connection is Wi-Fi or Ethernet.

For example:

```text
Default route
     │
     ▼
Interface index
     │
     ▼
Windows network adapter
     │
     ▼
Wi-Fi / Ethernet
```

This allows the application to work regardless of whether the computer is connected through Wi-Fi or Ethernet.

---

## Captive Portal Detection

The application does not rely on a hard-coded portal IP address or port.

When network connectivity is detected, CampusAuthenticator sends a request to a connectivity-check endpoint.

Depending on the response, the network is classified as:

```text
CAPTIVE_PORTAL
INTERNET_AVAILABLE
NO_INTERNET
```

When a captive portal is detected, the HTTP redirect is followed to obtain the actual FortiGate authentication page.

The portal URL is therefore discovered dynamically from the current network instead of being stored in configuration.

---

## Authentication

After obtaining the FortiGate authentication page, the application extracts the required login parameters from the page and submits the saved campus credentials.

The authentication flow is approximately:

```text
Connectivity check
       │
       ▼
FortiGate redirect
       │
       ▼
Retrieve login page
       │
       ▼
Parse authentication parameters
       │
       ▼
Load saved credentials
       │
       ▼
Submit login request
       │
       ▼
Receive successful redirect
       │
       ▼
Save keepalive URL
       │
       ▼
Start keepalive
```

The portal-specific HTML parsing is isolated in `portal/parser.py`, while HTTP communication and session management are handled by `portal/client.py`.

---

## Session Persistence

CampusAuthenticator stores the portal session information required for recovery in:

```text
%LOCALAPPDATA%\CampusAuthenticator\storage\session.json
```

When running from the source tree during development, this corresponds to:

```text
storage/session.json
```

When possible, the application can use the saved keepalive URL to recover an existing authenticated session rather than performing a completely new login.

The saved session is also used by the keepalive mechanism.

---

## Keepalive

After successful authentication, CampusAuthenticator periodically sends requests to the portal's keepalive endpoint.

The keepalive interval is currently:

```text
6000 seconds
```

The keepalive process runs independently so that the main application remains responsive.

The controller also handles stopping the keepalive thread when the user logs out or when the network state changes.

---

## Credential Management

Credentials are configured through the application's **Settings** page.

When using the packaged application, they are stored locally in:

```text
%LOCALAPPDATA%\CampusAuthenticator\storage\config.json
```

The configuration contains:

```json
{
    "username": "...",
    "password": "..."
}
```

The SSID is not stored as part of the application configuration.

### Changing credentials while authenticated

If the credentials are changed while the application is already authenticated, CampusAuthenticator handles the transition automatically:

```text
Save new credentials
       │
       ▼
Cancel previous credential operation
       │
       ▼
Logout existing session
       │
       ▼
Authenticate using new credentials
       │
       ▼
Start new keepalive
```

If multiple credential changes occur while an authentication attempt is in progress, older authentication operations are cancelled so that the latest saved credentials take precedence.

---

## User Interface

The application runs as a Windows system-tray application.

The main window provides information such as:

* Authentication status
* Active network interface
* Login/logout state
* Current connection state

The tray interface provides quick access to the application controls.

### Settings

The Settings page allows the user to configure:

* Campus username
* Campus password

Network interface and captive portal information are detected automatically and are not manually configured.

---

## Notifications

The application contains a small notification layer that queues application events.

On Windows, the application can display these events using Windows toast notifications.

Notifications are generated by the authentication controller and consumed by the tray application.

---

## Logging

Application activity is stored in the application's runtime `logs/` directory.

For the packaged Windows application:

```text
%LOCALAPPDATA%\CampusAuthenticator\logs\
```

Example:

```text
logs/
├── authenticator-2026-09-26.log
├── authenticator-2026-09-27.log
├── authenticator-2026-09-28.log
└── authenticator-2026-09-29.log
```

Logs are useful for diagnosing:

* Network detection
* Authentication attempts
* Captive portal detection
* Session recovery
* Logout
* Keepalive activity
* Network disconnections

Older log files are automatically removed according to the application's log-retention policy.

---

## Project Structure

```text
CampusAuthenticator/
│
├── app.py
├── notifications.py
├── README.md
├── CampusAuthenticator.spec
│
├── assets/
│   ├── icon-master.png
│   ├── icon.png
│   └── icon.ico
│
├── core/
│   ├── controller.py
│   ├── logger.py
│   ├── paths.py
│   └── __init__.py
│
├── gui/
│   ├── settings.py
│   ├── tray.py
│   ├── window.py
│   └── __init__.py
│
├── network/
│   ├── events.py
│   └── __init__.py
│
├── portal/
│   ├── client.py
│   ├── parser.py
│   └── __init__.py
│
└── storage/
    ├── config.json
    ├── config.py
    ├── session.json
    ├── session.py
    └── __init__.py
```

### Module responsibilities

| Module               | Responsibility                                                            |
| -------------------- | ------------------------------------------------------------------------- |
| `app.py`             | Application entry point and GUI/tray startup                              |
| `notifications.py`   | Notification queue and Windows toast integration                          |
| `core/controller.py` | Central authentication and network state controller                       |
| `core/logger.py`     | Application logging                                                       |
| `core/paths.py`      | Resource and runtime-data path resolution                                 |
| `gui/window.py`      | Main application window                                                   |
| `gui/settings.py`    | Credential settings interface                                             |
| `gui/tray.py`        | System-tray application and controls                                      |
| `network/events.py`  | Windows network events and active-interface detection                     |
| `portal/client.py`   | Captive portal detection, authentication, session handling, and keepalive |
| `portal/parser.py`   | Parsing of FortiGate login-page parameters                                |
| `storage/config.py`  | Local credential configuration storage                                    |
| `storage/session.py` | Local session persistence                                                 |

---

## Requirements

### Packaged Windows release

The packaged Windows release requires:

* **Windows**
* A network connection capable of reaching the NIT Calicut campus network

Python and the application's Python dependencies are already bundled into the packaged application.

### Development environment

When running CampusAuthenticator directly from source, the application currently targets:

* **Windows**
* **Python 3.12+**
* A network connection capable of reaching the NIT Calicut campus network

### Runtime Python dependencies

The source version uses:

```text
PySide6
WMI
requests
beautifulsoup4
Windows-Toasts
```

These provide:

* `PySide6` — GUI and system-tray interface
* `WMI` — Windows network adapter and routing information
* `requests` — HTTP communication with the captive portal
* `beautifulsoup4` — parsing the portal login page
* `Windows-Toasts` — Windows toast notifications

---

## Installation from Source

This section is intended for development. For normal use, download the packaged Windows release instead.

Clone or copy the project to the Windows machine.

Create and activate a Python virtual environment if desired:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

Install the required packages:

```powershell
pip install PySide6 WMI requests beautifulsoup4 Windows-Toasts
```

Then start the application:

```powershell
python app.py
```

On first launch, open **Settings** and enter the campus credentials.

---

## Building the Windows Application

The Windows release is built using PyInstaller.

The repository contains the PyInstaller build specification:

```text
CampusAuthenticator.spec
```

To create a packaged build:

```powershell
pyinstaller --noconfirm --clean CampusAuthenticator.spec
```

The resulting application is generated under:

```text
dist/
└── CampusAuthenticator/
    ├── CampusAuthenticator.exe
    └── _internal/
```

The entire `CampusAuthenticator` directory is required when distributing the packaged application.

The generated `build/` and `dist/` directories are build artifacts and are not committed to the Git repository.

---

## Running Automatically on Windows

The packaged application can be configured in **Windows Task Scheduler** to start automatically when the user logs in.

For the packaged release, the launch target is:

```text
CampusAuthenticator.exe
```

The executable should be started from the extracted application directory so that its `_internal` directory remains available.

For development, the source version can instead be launched with:

```text
python.exe app.py
```

The previous background-script launcher:

```text
run_hidden.vbs
    ↓
start.bat
    ↓
main.py
```

is no longer part of the application architecture.

---

## Manual Controls

The application provides controls for common actions such as:

### Login

Attempts to authenticate to the campus captive portal using the saved credentials.

### Logout

Terminates the current portal session and stops the keepalive process.

A manually initiated logout also temporarily prevents the automatic authentication mechanism from immediately logging back in.

### Refresh

Refreshes the application's current network/authentication state.

### Settings

Allows the saved campus username and password to be changed.

### Exit

Stops the application and closes the tray application.

---

## Troubleshooting

### Application does not authenticate

Check the application log files in:

```text
%LOCALAPPDATA%\CampusAuthenticator\logs\
```

Confirm that:

* The machine is connected to the campus network.
* The active network interface is detected.
* Credentials in Settings are correct.
* The FortiGate captive portal is reachable.

### Application shows no network connection

The application determines the active interface using the Windows routing table and network adapter information.

Check whether Windows itself has a valid network connection and a default route.

Virtual adapters, VPN interfaces, and similar adapters may intentionally be ignored.

### Credentials were changed but authentication still uses the previous credentials

Open Settings and verify that the new credentials were saved.

The application cancels older credential-change authentication attempts so that the most recently saved credentials take precedence.

### Session keeps expiring

Check the application logs for keepalive activity and confirm that the campus network remains connected.

### Login works manually but automatic login fails

Check the authentication and portal logs for the failed attempt.

The captive portal endpoint is discovered dynamically, so hard-coded portal IP or port configuration is not required.

---

## Security Notes

Campus credentials are stored locally in:

```text
%LOCALAPPDATA%\CampusAuthenticator\storage\config.json
```

The application does not use a `.env` file for credentials or portal configuration.

The persisted session information is stored separately in:

```text
%LOCALAPPDATA%\CampusAuthenticator\storage\session.json
```

These files should be treated as sensitive local application data and should not be committed to a public repository.

The packaged application does not provide additional encryption for these local files.

---

## Development Notes

CampusAuthenticator is structured around a central controller with separate modules for:

```text
GUI
 │
 ▼
Controller
 ├── Network detection
 ├── Portal client
 ├── Session storage
 └── Notifications
```

This separation keeps the GUI independent from the low-level captive-portal implementation.

The application is designed around network events rather than requiring the user to manually monitor or restart the authentication process.

---

## Current Architecture

The current version is a Windows GUI/tray application evolved from the original background-only authentication script.

The current application uses:

```text
app.py
   │
   ▼
TrayApplication
   │
   ├── MainWindow
   ├── Settings
   │
   ▼
AuthController
   │
   ├── Network detection
   ├── Captive portal detection
   ├── Authentication
   ├── Session recovery
   ├── Keepalive
   └── Notifications
```

The application also uses `core/paths.py` to distinguish between:

* bundled application resources, and
* writable runtime data such as credentials, session information, and logs.

This is the architecture documented and maintained by the current version of CampusAuthenticator.

---

## License

This project is intended for personal/educational use on the NITC campus network.

The project does not grant any additional rights to access or use the NITC network. Users are responsible for complying with applicable campus network policies and regulations.
