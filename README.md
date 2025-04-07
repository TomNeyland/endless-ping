# Endless Ping - Network Monitoring Tool

A cross-platform, Python-based network monitoring application for visualizing network latency, packet loss, and route information.

![Network Monitor Screenshot](https://via.placeholder.com/800x600?text=Network+Monitor+Screenshot)

## Features

- **Real-time Network Monitoring**: Continuously monitor network performance to any target
- **Traceroute Visualization**: Display the complete path to destination with hop-by-hop analysis
- **Multi-platform Support**: Works on Windows, macOS, and Linux
- **Rich Data Display**: View latency, packet loss, jitter, and other metrics in real-time
- **Time Series Analysis**: Track performance over time with customizable intervals
- **Session Management**: Save and load monitoring sessions for later analysis
- **Data Export**: Export monitoring data to CSV and JSON formats
- **Customizable Monitoring**: Adjust monitoring intervals from 1 to 10 seconds

## Requirements

- Python 3.11 or newer
- PyQt6
- PyQtGraph
- NumPy
- QDarkStyle (optional, for dark theme)
- Root/Administrator privileges (for ICMP ping functionality on Unix systems)

## Installation

### Using Poetry (recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/endless-ping.git
cd endless-ping

# Install dependencies with Poetry
poetry install

# Run the application
poetry run python src/main.py
```

### Using pip

```bash
# Clone the repository
git clone https://github.com/yourusername/endless-ping.git
cd endless-ping

# Install dependencies
pip install pyqt6 pyqtgraph numpy qdarkstyle

# Run the application
python src/main.py
```

## Usage

1. Enter a hostname or IP address in the target field
2. Select your desired monitoring interval
3. Click "Start" to begin monitoring
4. The application will:
   - Perform an initial traceroute to discover the network path
   - Begin continuous ping monitoring of each hop
   - Display results in both table and graph formats
5. Use the "Pause" button to temporarily halt monitoring
6. Use the "Save" button to save the current session

## UI Components

- **Control Panel**: Input field for target, monitoring interval selection, and control buttons
- **Hop Data Grid**: Tabular display of network statistics for each hop
- **Latency Bar Graph**: Horizontal bar graph showing current latency by hop
- **Time Series Graph**: Line graph showing latency trends over time for all hops

## Technical Details

The application consists of several modules:

- **Core**: Network monitoring logic, statistics calculation, and session management
- **UI**: PyQt6-based user interface components
- **Utils**: Low-level networking utilities (ping, traceroute, DNS lookup)

The network monitoring works by:
1. Performing an initial traceroute to discover the path to the target
2. Sending ICMP ping packets to each hop in the path
3. Collecting and analyzing response data
4. Updating the UI in real-time with the results

## Building from Source

The project includes GitHub Actions workflows for building standalone executables for Windows, macOS, and Linux using PyInstaller.

To build manually:

```bash
# Install PyInstaller
poetry add --group dev pyinstaller

# Build the executable
poetry run pyinstaller --name=EndlessPing --onefile --windowed src/main.py
```

## Permissions

On Unix-like systems (Linux, macOS), raw socket operations require root privileges. Run the application with sudo:

```bash
sudo poetry run python src/main.py
```

Or use capabilities to grant the Python interpreter the necessary permissions:

```bash
sudo setcap cap_net_raw=eip $(which python3)
```

## License

[MIT License](LICENSE)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
