<div align="center">
  <img src="https://raw.githubusercontent.com/stephenyin/NetHang/e5f090958d180be880aaa0a6f1af644392fe1cf9/assets/logo-dark.png" alt="NetHang Logo" width="240"/>
</div>

![Tests](https://github.com/stephenyin/NetHang/actions/workflows/tests.yml/badge.svg)

NetHang is a web-based tool designed to simulate network quality, focusing on the diversity of last-mile network conditions. For modern internet applications and services with high real-time requirements, NetHang offers a stable, reentrant, customizable, and easily extensible network quality simulation system, helping to achieve low-latency and high-quality internet services.

<img src="https://raw.githubusercontent.com/stephenyin/NetHang/e5f090958d180be880aaa0a6f1af644392fe1cf9/assets/nh-10.gif" alt="Add Path" width="1080"/>

Unlike traditional network impairment tools that target backbone network quality between servers and switches, NetHang is optimized for:

- Simulating network quality from user equipment (UE) to servers, typically traversing:
    - UE <--> Lan (Wi-Fi or Wired) <--> Routers <--> ISP edge nodes <--> APP servers
    - UE <--> Cellular <--> ISP edge nodes <--> APP servers
    - UE <--> Air interface <--> Satellite <--> APP servers

<img src="https://raw.githubusercontent.com/stephenyin/NetHang/e5f090958d180be880aaa0a6f1af644392fe1cf9/assets/nh-01.gif" alt="Start Simulation" width="1080"/>

- The current network model is built and simplified based on existing network quality data modeling, while also supporting users to easily customize the network models they need for testing in YAML format.

- NetHang clearly displays the differences in data traffic before and after simulation, as well as the state of the simulation conditions.

<img src="https://raw.githubusercontent.com/stephenyin/NetHang/c57c352eed71b9e7f93f47850792b3bde67c782a/assets/nh-00.gif" alt="Manipulate Charts" width="1080"/>

## Features

- Traffic rate limiting and shaping
- Network latency and latency variation simulation
- Packet loss simulation
- Support for both uplink and downlink traffic control
- Configurable traffic rules and models
- Real-time traffic statistics display

## Requirements

- Python 3.8 or higher
- Linux system with `tc` and `iptables` support
- Root privileges for traffic control operations

## Installation

### From PyPI (Recommended)

You can install NetHang from PyPI using the following command:

```pip install nethang```

### From Source (For Developers)

You can also install NetHang from source by cloning the repository and running the following command:

```pip install .```

## License

MIT License

Copyright (c) 2025 NetHang Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

Please make sure to update tests as appropriate and adhere to the existing coding style.

## Authors

NetHang Contributors

## Acknowledgments

- Thanks to all contributors who have helped with the project
- Inspired by various network traffic control tools and utilities
