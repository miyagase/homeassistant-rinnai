# Rinnai Gas Dryer — Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![GitHub release](https://img.shields.io/github/release/miyagase/homeassistant-rinnai.svg)](https://github.com/miyagase/homeassistant-rinnai/releases)

Home Assistant integration for the **Rinnai 乾太くん (Kantakun)** gas clothes dryer.

> 日本語のドキュメントは [README_ja.md](README_ja.md) をご覧ください。

## Features

- Real-time monitoring (60-second polling)
- Drying course and remaining time
- Automatic token refresh (no manual renewal required)

## Entities

| Entity | Type | Description |
|---|---|---|
| `binary_sensor.kantakun_running` | Binary Sensor | Whether the dryer is running |
| `sensor.kantakun_status` | Sensor | Status (stopped / running / standby / error) |
| `sensor.kantakun_course` | Sensor | Drying course |
| `sensor.kantakun_time_remaining` | Sensor | Remaining time (minutes) |

## Requirements

- Home Assistant 2023.1.0 or later
- Rinnai Kantakun gas dryer with cloud connectivity
- Local network access to the device

## Installation

### HACS (Recommended)

1. Open HACS → Integrations → ⋮ → Custom repositories
2. Add `https://github.com/miyagase/homeassistant-rinnai` (category: Integration)
3. Install **Rinnai 乾太くん**
4. Restart Home Assistant

### Manual

Copy `custom_components/rinnai/` into your HA `custom_components/` directory and restart.

## Setup

Settings → Devices & Services → Add Integration → search for **Rinnai**

### Pairing steps

1. Press **L3 → OK** on the dryer.
2. Press **Submit** in the HA setup dialog.
3. When the dryer display shows "Press OK", press **OK** on the dryer.

Setup completes automatically. No smartphone app or packet capture required.

## Token Management

- Access token validity: ~24 hours
- This integration automatically refreshes the token up to 2 hours before expiry.
- If the refresh token expires, re-run the setup flow.

## Compatibility

Developed and tested with the Rinnai 乾太くん (Japan). May work with Rinnai gas dryers in other regions if they share the same cloud API.
