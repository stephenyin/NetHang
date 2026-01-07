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
- Ubuntu 22.04 LTS (or similar Linux distribution)
- At least **TWO** network interface cards (NICs)

---

## ⚙️ System Configuration

Before installing NetHang, you need to configure your Linux system as a software router. Follow the steps below to set up the required dependencies and network settings.

### 📦 Dependencies and Permissions

Install the required packages:

```bash
sudo apt update
sudo apt install iproute2 iptables libcap2-bin
```

Check command paths:

```bash
which tc
which iptables
```

They are typically located in `/sbin/tc` and `/sbin/iptables` (or `/usr/sbin/tc` and `/usr/sbin/iptables`).

Grant the `CAP_NET_ADMIN` capability, which is required for `tc` and `iptables`:

```bash
sudo setcap cap_net_admin+ep /usr/sbin/tc
sudo setcap cap_net_admin+ep /usr/sbin/xtables-nft-multi
```

Verify the permissions:

```bash
iptables -L
tc qdisc add dev lo root netem delay 1ms
tc qdisc del dev lo root
```

If the output is without errors, the permissions are set correctly. If not, you may need to reboot the machine.

### 🔄 Enabling IP Forwarding

**Step 1: Check Current IP Forwarding Status**

Before proceeding, check whether IP forwarding is currently enabled on your Ubuntu machine:

```bash
cat /proc/sys/net/ipv4/ip_forward
```

If the output is `0`, IP forwarding is disabled. If it's `1`, it's already enabled.

**Step 2: Enable IP Forwarding**

To enable IP forwarding temporarily (valid until the next reboot), run:

```bash
sudo sysctl -w net.ipv4.ip_forward=1
```

To make the change permanent, edit the `/etc/sysctl.conf` file and uncomment or add the line:

```bash
net.ipv4.ip_forward=1
```

Then, apply the changes:

```bash
sudo sysctl -p /etc/sysctl.conf
```

### 🌐 Configuring Network Interfaces

**Step 1: List Network Interfaces**

Identify your network interfaces using the `ip` command:

```bash
ip addr
```

You should see a list of interfaces like `eth0`, `eth1`, etc.

**Step 2: Configure Network Interfaces**

Edit the network configuration files for your interfaces. For example, to configure `eth0` and `eth1`, edit `/etc/network/interfaces`:

```bash
sudo vi /etc/network/interfaces
```

Here's a sample configuration for `eth0` and `eth1`:

```bash
# eth0 - Internet-facing interface
auto eth0
iface eth0 inet dhcp

# eth1 - Internal LAN interface
auto eth1
iface eth1 inet static
    address 192.168.1.1
    netmask 255.255.255.0
```

**Step 3: Apply Network Configuration Changes**

Apply the changes to network interfaces:

```bash
sudo systemctl restart networking
```

### 🔀 Configuring NAT (Network Address Translation)

To enable NAT for outbound traffic from your LAN, use `iptables`:

```bash
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
```

Make the change permanent by installing `iptables-persistent`:

```bash
sudo apt update
sudo apt install iptables-persistent
```

Follow the prompts to save the current rules.

### 📡 Setting Up DHCP Server (Optional)

This step is optional. If you want to use DHCP to assign IP addresses to devices on the LAN, you can configure the DHCP server.

**Step 1: Install DHCP Server**

If you want your Ubuntu router to assign IP addresses to devices on the LAN, install the DHCP server software:

```bash
sudo apt update
sudo apt install isc-dhcp-server
```

**Step 2: Configure DHCP Server**

Edit the DHCP server configuration file:

```bash
sudo vi /etc/dhcp/dhcpd.conf
```

Here's a sample configuration:

```bash
subnet 192.168.1.0 netmask 255.255.255.0 {
  range 192.168.1.10 192.168.1.50;
  option routers 192.168.1.1;
  option domain-name-servers 8.8.8.8, 8.8.4.4;
}
```

**Step 3: Start DHCP Server**

Start the DHCP server:

```bash
sudo systemctl start isc-dhcp-server
```

**Step 4: Enable DHCP Server at Boot**

To ensure the DHCP server starts at boot:

```bash
sudo systemctl enable isc-dhcp-server
```

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
