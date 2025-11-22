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

## Hardware Requirements

- DECENT DE1/DE1PRO/DE1XL espresso machine
- Raspberry Pi (or any Linux server)
- 80mm thermal receipt printer (supports most CUPS-compatible printers)

## Installation

### 1. Server Setup (Raspberry Pi/Linux)

#### Prerequisites

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install required system packages
sudo apt install -y python3 python3-pip python3-venv git cups

# For non-GUI systems, install text browser for printer configuration
sudo apt install -y lynx
```

#### Python Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv printtheshot-env
source printtheshot-env/bin/activate

# Install Python packages
pip install matplotlib pillow numpy
```

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
plugin.tcl                   # DE1 plugin file
shots_data/                  # JSON shot data storage
shots_images/                # Generated chart images
plugin/                      # Plugin download directory
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
