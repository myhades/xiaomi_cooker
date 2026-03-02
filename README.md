# Xiaomi Electric Rice Cooker

Custom Home Assistant integration for Xiaomi Electric Rice Cookers.

This integration is based on the original xiaomi_cooker project by Syssi and uses python-miio by Rytilahti for device communication. It has been updated to follow current Home Assistant integration patterns, including config flow and unique IDs.


## Credits

- Original integration: [Syssi](https://github.com/syssi/xiaomi_cooker)
- Device communication library: [Rytilahti](https://github.com/rytilahti/python-miio)


## Supported devices

| Name                      | Model                  | Model no.             |
| ------------------------- | ---------------------- | --------------------- |
|                           | chunmi.cooker.normal1  | IHFB01CM              |
| Mi IH Rice Cooker         | chunmi.cooker.normal2  | IHFB01CM, 2016DP1293  |
|                           | chunmi.cooker.normal3  |                       |
|                           | chunmi.cooker.normal4  |                       |
|                           | chunmi.cooker.normal5  |                       |
| Mi Smart Pressure Cooker  | chunmi.cooker.press1   | YLIH01CM              |
|                           | chunmi.cooker.press2   |                       |

Note that `chunmi.cooker.normal1` does not have built-in cooking profiles and config entities.

## Features

* Sensors
  - mode
  - menu
  - temperature
  - remaining
  - duration
  - favorite
  - panel display auto off
  - lid open alarm
  - lid open timeout
  - status
  - rice_id (available while cooking)
  - taste (available while cooking)
  - taste_phase (available while cooking)
  - stage_name (available while cooking)
  - stage_description (available while cooking)
* Selects
  - cooking menu
* Buttons
  - start cooking
  - stop cooking


## Install

### Method 1: Through HACS

Navigate to "HACS" > "Xiaomi Electric Rice Cooker" or use the My button below.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=myhades&repository=xiaomi_cooker&category=integration)

### Method 2: Manually

Download the repo and copy the folder `/custom_components/xiaomi_miio_cooker` into your Home Assistant's `/config/custom_components` directory.


## Setup

To add the integration, navigate to "Settings"  > "Devices & services"  > "Add integration"  > "Xiaomi Electric Rice Cooker" or use the My button below. Then, follow the config flow.

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=xiaomi_miio_cooker)


## Actions

#### `xiaomi_miio_cooker.start`

Start cooking a custom profile.

| Attribute       | Optional | Description                         |
| --------------- | -------- | ----------------------------------- |
| `device_id`     |   yes    | Required if multiple cookers exist. |
| `profile`       |   no     | Temperature curve string.           |


## Feedback
You can enable debug logging in the UI (if possible) or add the following to your Home Assistant configuration:
```
logger:
  default: warning
  logs:
    custom_components.xiaomi_miio_cooker: debug
    miio: debug
```
