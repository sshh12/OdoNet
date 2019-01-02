# OdoNet

A framework for a network of advanced monitoring devices.

## What

[Odo](https://en.wikipedia.org/wiki/Odo_(Star_Trek))[Net](https://en.wikipedia.org/wiki/Computer_network) is a way to manage, alert, and record IOT devices with a focus on intelligent Raspberry Pi based security cameras.

##### Network Features
* Ability to route devices through each other (as a sort of WiFi mesh) to significantly increase range
* Network Backups: if a devices goes down, the devices routed to it can connect to backup networks
* A device completely separated from the network will preserve important data locally until the connection is restored.

##### Camera Features
* Object Recognition (by MobileNetSSD)
* Motion detection (automatic and custom thresholds)
* Corrupt image filtering (prevents motion false positives on bad cameras)
* Supports Raspberry Pi cameras, USB cameras, Laptop webcams, FTP-supporting cameras (like broken Insteon cameras...), and more

##### Management Features
* Easy to use dashboard for configuring, controlling, and viewing devices
* View events (like motion detected) as well as where they are occurring overtime and their priority

#### Screenshots

![dashboard](https://user-images.githubusercontent.com/6625384/50607063-f1228c80-0e95-11e9-9b46-97053c982587.png)

![events page](https://user-images.githubusercontent.com/6625384/50606987-a86ad380-0e95-11e9-8ac9-d2403cca8860.png)

## How

OdoNet is structured like a [tree](https://en.wikipedia.org/wiki/Tree_(data_structure)) with 2 parts:
* A Root where all the data comes to and where the devices are controlled from
	* The root should run from a dedicated server/computer
* A (device) Node which connects to a parent node (often the Root) and can have other nodes connected to it (via its own WiFi access point)
	* This can run on a laptop, Raspberry Pi, etc...

#### Traditional Setup
OdoNet can be configured like a normal WiFi security camera system where all the devices are connected to the same WiFi network and transfer data directly to the Root computer

![Traditional Setup](https://user-images.githubusercontent.com/6625384/50605843-938c4100-0e91-11e9-8d15-26e366de204c.png)

#### Extended Setup
...or it can be configured to chain devices off of each other so that only a few devices are connected to the main network. This allows for extended range and lessened network congestion at the expense of some latency.

![Extended Setup](https://user-images.githubusercontent.com/6625384/50606334-5fb21b00-0e93-11e9-960f-b4ce03388c28.png)

## Getting Started

1. Create a Root:
[Root Setup Guide](https://github.com/sshh12/OdoNet/blob/master/.docs/SETUP_ROOT.md)

2. Create Nodes:
[Raspberry Pi Setup Guide](https://github.com/sshh12/OdoNet/blob/master/.docs/SETUP_PI_NODE.md) or
[PC as Node Setup Guide](https://github.com/sshh12/OdoNet/blob/master/.docs/SETUP_PC_NODE.md)

3. Add devices: [Camera Setup](https://github.com/sshh12/OdoNet/blob/master/.docs/CAMERAS.md)

## Help
Fill free to [create an issue](https://github.com/sshh12/OdoNet/issues).
