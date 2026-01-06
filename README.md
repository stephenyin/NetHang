<div align="center">
  <img src="https://raw.githubusercontent.com/stephenyin/NetHang/e5f090958d180be880aaa0a6f1af644392fe1cf9/assets/logo-dark.png" alt="NetHang Logo" width="240"/>

  <h3>Network Quality Simulation Tool</h3>

  ![Tests](https://github.com/stephenyin/NetHang/actions/workflows/tests.yml/badge.svg)
</div>

---

## 📖 Overview

NetHang is a web-based tool designed to simulate network quality, focusing on the diversity of last-mile network conditions. For modern internet applications and services with high real-time requirements, NetHang offers a stable, reentrant, customizable, and easily extensible network quality simulation system, helping to achieve low-latency and high-quality internet services.

### 🎥 Video Tutorial

<div align="center">
  <a href="https://www.youtube.com/watch?v=Mi3pPmpDwTg">
    <img src="https://img.youtube.com/vi/Mi3pPmpDwTg/maxresdefault.jpg" alt="A Great Way to do the Weak Network Test - NetHang" width="1080"/>
  </a>
  <p><strong><a href="https://www.youtube.com/watch?v=Mi3pPmpDwTg">📺 Watch: A Great Way to do the Weak Network Test - NetHang</a></strong></p>
</div>

---

## 🎯 What Makes NetHang Different?

Unlike traditional network impairment tools that target backbone network quality between servers and switches, NetHang is optimized for:

- **Simulating network quality from user equipment (UE) to servers**, typically traversing:
  - UE ↔ LAN (Wi-Fi or Wired) ↔ Routers ↔ ISP edge nodes ↔ APP servers
  - UE ↔ Cellular ↔ ISP edge nodes ↔ APP servers
  - UE ↔ Air interface ↔ Satellite ↔ APP servers

<div align="center">
  <img src="https://raw.githubusercontent.com/stephenyin/NetHang/2cbd1de5542e3487636128daccb566f1ddbda729/assets/nh-10.gif" alt="Add Path" width="1080"/>
</div>

- **The current network model** is built and simplified based on existing network quality data modeling, while also supporting users to easily customize the network models they need for testing in YAML format. The following image shows the StarLink network simulation (Queuing changes every 20s - 30s caused by Satellite handover):

<div align="center">
  <img src="https://raw.githubusercontent.com/stephenyin/NetHang/c6bca493d8c2fc6600b025ece99c0106e8f9e1a7/assets/model-starlink.gif" alt="StarLink Simulation" width="1080"/>
</div>

- **NetHang clearly displays** the differences in data traffic before and after simulation, as well as the state of the simulation conditions.

<div align="center">
  <img src="https://raw.githubusercontent.com/stephenyin/NetHang/c57c352eed71b9e7f93f47850792b3bde67c782a/assets/nh-00.gif" alt="Manipulate Charts" width="1080"/>
</div>

---

## ✨ Features

### Traffic Control & Shaping

- ✅ Configurable traffic rules and models
- ✅ Traffic rate limiting and shaping
- ✅ Throttle queue depth control

<div align="center">
  <img src="https://raw.githubusercontent.com/stephenyin/NetHang/c6bca493d8c2fc6600b025ece99c0106e8f9e1a7/assets/throttle-settings-0.png" alt="Throttle Settings" width="480"/>
</div>

### Latency & Jitter Simulation

- ✅ Network latency and latency variation (Jitter) simulation
- ✅ Jitter simulation with and without reordering allowed

<div align="center">
  <img src="https://raw.githubusercontent.com/stephenyin/NetHang/c6bca493d8c2fc6600b025ece99c0106e8f9e1a7/assets/latency-settings-0.png" alt="Latency Settings" width="480"/>
  <img src="https://raw.githubusercontent.com/stephenyin/NetHang/c6bca493d8c2fc6600b025ece99c0106e8f9e1a7/assets/latency-settings-1.png" alt="Latency Settings" width="480"/>
</div>

### Packet Loss Simulation

- ✅ Packet loss with random and burst support

<div align="center">
  <img src="https://raw.githubusercontent.com/stephenyin/NetHang/c6bca493d8c2fc6600b025ece99c0106e8f9e1a7/assets/loss-settings-0.png" alt="Loss Settings" width="480"/>
</div>

### Real-time Monitoring

- ✅ Support for both uplink and downlink traffic control
- ✅ Real-time traffic statistics display

---

## 📋 Requirements

- Python **3.8** or higher
- Linux system with `tc` and `iptables` support
- Root privileges for traffic control operations

---

## 🚀 Installation

### From PyPI (Recommended)

You can install NetHang from PyPI using the following command:

```bash
pip install nethang
```

### From Source (For Developers)

You can also install NetHang from source by cloning the repository and running the following command:

```bash
git clone https://github.com/stephenyin/NetHang.git
cd NetHang
pip install .
```

---

## 📄 License

**MIT License**

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

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

Please make sure to update tests as appropriate and adhere to the existing coding style.

---

## 👥 Authors

NetHang Contributors

---

## 🙏 Acknowledgments

- Thanks to all contributors who have helped with the project
- Inspired by various network traffic control tools and utilities

---

<div align="center">
  <p>Made with ❤️ by the NetHang community</p>
</div>
