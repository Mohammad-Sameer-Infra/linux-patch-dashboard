# Linux Patch & Compliance Dashboard

Production-style Linux Patch Management and Infrastructure Compliance Platform.

## Overview

Linux Patch & Compliance Dashboard provides centralized visibility into Linux server patch status, compliance posture, inventory, and node lifecycle management.

The platform is designed for infrastructure engineers, system administrators, DevOps teams, and platform operations teams who need a lightweight solution for monitoring Linux patch compliance across multiple servers.

---

## Current Features

### Node Management

* Token-based node registration
* Automated SSH trust onboarding
* Unique node identification (UUID)
* Node lifecycle tracking
* Last-seen monitoring

### Inventory Management

* Managed node inventory
* Hostname tracking
* IP address tracking
* Registration timestamps
* Node state management

### Patch Visibility

* Available package updates
* Kernel update tracking
* Security update identification
* Critical package monitoring
* Detailed package views

### Telemetry Collection

* Remote system information collection
* OS version tracking
* Uptime monitoring
* Online/offline status
* Historical telemetry storage

### Platform Operations

* Bootstrap installer
* Environment readiness validation
* Runtime configuration management
* Service health verification

---

## Architecture

```text
+--------------------+
| Managed Linux Node |
+--------------------+
          |
          | Registration Token
          |
          v
+----------------------------+
| Linux Patch Dashboard      |
|                            |
| - Inventory               |
| - Registration Service    |
| - Telemetry Collector     |
| - Compliance Engine       |
+----------------------------+
          |
          | SSH
          |
          v
+----------------------------+
| Telemetry Collection       |
+----------------------------+
          |
          v
+----------------------------+
| SQLite Database            |
+----------------------------+
```

---

## Project Structure

```text
linux-patch-dashboard/

├── app/
├── config/
├── inventory/
├── registration/
├── security/
├── templates/
├── bootstrap.sh
├── collector.py
├── app.py
└── requirements.txt
```

---

## Installation

### Clone Repository

```bash
git clone <repository-url>

cd linux-patch-dashboard
```

### Bootstrap Environment

```bash
chmod +x bootstrap.sh

./bootstrap.sh
```

The bootstrap process validates:

* Python installation
* Runtime directories
* Inventory configuration
* Registration token configuration
* Dashboard settings
* Public key configuration
* Virtual environment status
* Service status

### Create Virtual Environment

```bash
python3 -m venv venv

source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Configuration

Edit:

```text
config/settings.json
```

Configure:

* Dashboard URL
* Inventory location
* Registration token storage
* SSH public key location
* Dashboard refresh interval

---

## Node Registration

Generate a registration token from the dashboard.

On the target node:

```bash
./register-node.sh
```

Provide:

* Dashboard URL
* Registration token

The node will:

1. Install dashboard SSH trust.
2. Register with the platform.
3. Appear in the managed node inventory.

---

## Roadmap

### Phase 1 – Inventory & Patch Visibility

* [x] Node inventory
* [x] Patch visibility
* [x] Telemetry collection
* [x] Registration workflow

### Phase 2 – Platform Readiness

* [x] Bootstrap validation
* [x] Runtime validation
* [x] Repository portability

### Phase 3 – Operational Excellence

* [ ] Collector health monitoring
* [ ] Approval workflow
* [ ] Node decommissioning

### Phase 4 – Security

* [ ] Authentication
* [ ] Role-based access control
* [ ] Audit logging

### Phase 5 – Enterprise Features

* [ ] Patch compliance reporting
* [ ] Maintenance windows
* [ ] Node grouping and tagging
* [ ] Notification integrations

---

## Intended Audience

* Linux System Administrators
* Infrastructure Engineers
* Platform Engineers
* DevOps Engineers
* Site Reliability Engineers (SRE)

---

## License

MIT License

