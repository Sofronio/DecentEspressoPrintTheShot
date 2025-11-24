# PrintTheShot

[中文文档](README_zh.md) | [English Documentation](README.md) 

A complete solution for automatically uploading DECENT espresso machine shot data to a local server and printing beautiful shot analysis charts on thermal receipt printers.

## Features

- **Automatic Upload**: Automatically uploads shot data after each espresso extraction
- **Beautiful Charts**: Generates professional pressure/flow/temperature charts
- **Thermal Printing**: Optimized for 80mm thermal receipt printers
- **Web Management**: Modern web interface for monitoring and control
- **Multilingual**: Supports both English and Chinese
- **DE1 Plugin**: Seamless integration with DECENT espresso machines

## Screenshots

### 🖥️ Server Operation
![Server Terminal](screenshots/server-terminal.jpg)
- **Server startup interface** - Displaying port, data directories, and startup status
- **Real-time logging** - Monitoring data reception and print jobs
- **Multilingual support** - Bilingual server status information
- **Active connections** - Current user sessions and system resources

### 🌐 Web Management
![Web Interface](screenshots/web-interface.jpg)
- **Dashboard overview** - Server status and statistics at a glance
- **Data visualization** - Interactive shot charts with pressure/flow/temperature curves
- **Queue management** - Real-time print queue monitoring and control
- **Language switching** - Easy toggle between English and Chinese interfaces
- **Manual controls** - Upload, print, and queue management functions

### ☕️ DE1 Integration
![DE1 Plugin](screenshots/de1-plugin.jpg)
- **Plugin configuration** - Server URL, endpoints, and upload settings
- **Manual upload** - Instant upload of last shot data
- **Status display** - Last upload results with timestamps
- **Auto-upload settings** - Minimum duration and upload preferences

### 🖨️ Printed Output
![Printed Chart](screenshots/printed-chart.jpg)
- **Professional charts** - Pressure, flow rate, and temperature curves
- **Extraction data** - Time, input/output weight, and shot duration
- **Profile information** - Coffee profile name and grinder settings
- **Thermal optimized** - Designed for 80mm receipt printers
- **Auto-cut support** - Compatible with printers having cutter function

### 🖨️ Printer in action
![Printed Chart](screenshots/printer-in-action.jpg)

## Hardware Requirements

- DECENT DE1/DE1PRO/DE1XL espresso machine
- Raspberry Pi (or any Linux server)
- 80mm thermal receipt printer (supports most CUPS-compatible printers)

## 🚀 Quick Start (Pre-built Executable)

### For Windows Users (Not tested)

1. **Download the latest release** from the [Releases page](https://github.com/yourusername/printtheshot/releases)
2. **Run the executable**: Double-click `PrintTheShot-Windows.exe`
3. **Access the web interface**: Open `http://localhost:8000` in your browser
4. **Configure your printer** through the web interface
5. **Install the DE1 plugin** from the web interface download section

### For macOS Users

1. **Download the macOS version** from the [Releases page](https://github.com/yourusername/printtheshot/releases)
2. **Run the application**: Double-click `PrintTheShot-Mac.app`
3. **Access the web interface**: Open `http://localhost:8000` in your browser
4. **Configure your printer** through the web interface
5. **Install the DE1 plugin** from the web interface download section

### For Linux Users (Not tested)

1. **Download the Linux executable** from the [Releases page](https://github.com/yourusername/printtheshot/releases)
2. **Make it executable**:
~~~
chmod +x PrintTheShot-Linux
~~~
3. **Run the server**:
~~~
./PrintTheShot-Linux
~~~
4. **Access the web interface**: Open `http://localhost:8000` in your browser

## 🔨 Building from Source

If you prefer to build from source or want to contribute:

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Build Steps

1. **Clone the repository**:
~~~
git clone https://github.com/yourusername/printtheshot.git
cd printtheshot
~~~

2. **Install build dependencies**:
~~~
pip install pyinstaller
pip install -r requirements.txt
~~~

3. **Run build script for your platform**:

   **Windows**:
~~~
build-windows.bat
~~~

   **macOS**:
~~~
./build-mac.sh
~~~

   **Linux**:
~~~
./build-linux.sh
~~~

4. **Find the executable** in the `dist/` directory

## ⚙️ Manual Installation (Advanced)

For users who prefer manual installation or are using platforms not covered by pre-built executables.

### 1. Server Setup (Raspberry Pi/Linux)

#### Prerequisites

~~~
# Update system
sudo apt update
sudo apt upgrade -y

# Install required system packages
sudo apt install -y python3 python3-pip python3-venv git cups

# For non-GUI systems, install text browser for printer configuration
sudo apt install -y lynx
~~~

#### Python Dependencies

~~~
# Create virtual environment (recommended)
python3 -m venv printtheshot-env
source printtheshot-env/bin/activate

# Install Python packages
pip install matplotlib pillow numpy flask
~~~

#### Download and Run

~~~
# Clone the repository
git clone https://github.com/yourusername/printtheshot.git
cd printtheshot

# Make server script executable
chmod +x print_the_shot_server.py

# Run server
./print_the_shot_server.py
~~~

The server will start on port 8000. Access the web interface at `http://your-pi-address:8000`

**Important**: The `plugin.tcl` file for your DE1 machine is now available in the cloned directory.

## Running as a Service

### Systemd Service (Recommended for Linux/Raspberry Pi)

1. **Create service file**:
~~~
sudo nano /etc/systemd/system/printtheshot.service
~~~

2. **Add service configuration**:
~~~
[Unit]
Description=PrintTheShot Server
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/PrintTheShot
ExecStart=/home/pi/PrintTheShot/print_the_shot_server.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
~~~

3. **Enable and start service**:
~~~
sudo systemctl daemon-reload
sudo systemctl enable printtheshot.service
sudo systemctl start printtheshot.service
~~~

4. **Check service status**:
~~~
sudo systemctl status printtheshot.service
~~~

### Managing the Service

**Start service**:
~~~
sudo systemctl start printtheshot.service
~~~

**Stop service**:
~~~
sudo systemctl stop printtheshot.service
~~~

**Restart service**:
~~~
sudo systemctl restart printtheshot.service
~~~

**View logs**:
~~~
sudo journalctl -u printtheshot.service -f
~~~

**Disable auto-start**:
~~~
sudo systemctl disable printtheshot.service
~~~

**Remove service completely**:
~~~
sudo systemctl stop printtheshot.service
sudo systemctl disable printtheshot.service
sudo rm /etc/systemd/system/printtheshot.service
sudo systemctl daemon-reload
~~~

### Manual Background Process

**Start in background**:
~~~
nohup python3 print_the_shot_server.py > server.log 2>&1 &
~~~

**Stop background process**:
~~~
pkill -f print_the_shot_server.py
~~~

### 2. Printer Configuration

#### GUI Method (Recommended for Desktop Systems)

1. Open CUPS web interface: `http://localhost:631`
2. Add your thermal printer
3. Set paper size to "Custom 80x180mm"

#### Command Line Method (For Headless Systems)

```bash
# Install CUPS text tools
sudo apt install -y cups-client

# List available printers
lpstat -p -d

# If no printers found, use lynx to configure via text browser
sudo lynx http://localhost:631
```

#### Common Thermal Printer Models

- **STAR TSP143IIU**: `driverless ipp://printer-ip`
- **Epson TM-T20II**: `sudo apt install printer-driver-escpr`
- **Zjiang ZJ-58**: Use generic POS printer driver

### 3. DE1 Plugin Installation

1. **Download the plugin**: Click "Download DE1 Plugin" from the server web interface
2. **Create plugin directory** on your DE1 tablet SD card:
   ```bash
   /de1plus/plugins/print_the_shot/
   ```
3. **Copy the plugin file**: Place `plugin.tcl` in the directory above
4. **Restart DE1App**: The plugin will auto-load

### 4. Plugin Configuration

1. Open DE1App and go to Settings → Plugins
2. Find "Print The Shot" and tap to configure
3. Set your server address:
   - **Server URL**: `your-pi-address:8000` (e.g., `192.168.1.100:8000`)
   - **Server Endpoint**: `upload`
   - **Use HTTP**: Enabled (unless using HTTPS)
4. Configure auto-upload settings as desired

## Usage

### Automatic Operation
1. Pull a shot on your DE1 machine
2. Data automatically uploads to your server
3. Chart is automatically generated and printed

### Manual Operation
1. Use "Manual Upload Last Shot" in plugin settings
2. Or use the web interface to upload JSON files manually

### Web Interface
Access `http://your-server:8000` to:
- View recent shots and charts
- Manually trigger prints
- Clear print queue
- Monitor server status
- Switch between English/Chinese

## Troubleshooting

### Common Issues

**"Upload failed" in DE1 plugin**
- Check server URL and network connectivity
- Verify server is running: `ps aux | grep print_the_shot`
- Check firewall: `sudo ufw allow 8000`

**Printer not working**
- Test printer: `echo "Test" | lp`
- Check CUPS status: `systemctl status cups`
- Verify paper size settings

**No charts generated**
- Check Python dependencies: `pip list | grep -E "matplotlib|pillow|numpy"`
- Verify write permissions in data directories

**Plugin not appearing in DE1**
- Verify file location: `/de1plus/plugins/print_the_shot/plugin.tcl`
- Check file permissions
- Restart DE1App completely

### Logs and Debugging

**Server logs**: View in terminal where server is running
**DE1 plugin logs**: Check DE1App plugin console
**Print queue**: `lpstat -o`
**CUPS logs**: `sudo tail -f /var/log/cups/error_log`

## File Structure

```
print_the_shot_server.py     # Main server script
plugin/plugin.tcl            # DE1 plugin file
shots_data/                  # JSON shot data storage
shots_images/                # Generated chart images
```

## Configuration

### Server Settings (Web Interface)
- **Print Enabled**: Toggle automatic printing
- **Max Users**: Concurrent connection limit
- **Language**: English/Chinese interface

### Plugin Settings (DE1 App)
- **Auto Upload**: Enable/disable automatic uploads
- **Minimum Duration**: Skip shots shorter than X seconds
- **Server Configuration**: URL and endpoint settings

## Supported Printers

- 80mm thermal receipt printers
- CUPS-compatible printers
- Common models: STAR, Epson, Zjiang, Citizen

## Contributing

Feel free to submit issues and pull requests for improvements.

## License

GNU General Public License v3.0 - see LICENSE file for details.

## Support

For issues and questions:
1. Check troubleshooting section above
2. Review server logs for error messages
3. Ensure all dependencies are properly installed

## Special Thanks

### Printing Inspiration & Support
A very special thank you to **Ray from Siphon House (Beijing)** who not only inspired this entire project but also generously lent a thermal printer to help bring it to life. Her Siphon House proudly serves as the first operational café to implement PrintTheShot in production.

### Technical Inspiration
The upload functionality and UI design of the **Visualizer plugin** for DECENT espresso machines greatly inspired the plugin features in this system. Their elegant approach to data handling and user interface design provided valuable reference for developing PrintTheShot's DE1 integration.
