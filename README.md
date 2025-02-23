# Spiuwirkid - ZYRX
Next-Generation Performance Testing Engine

![ZYRX Logo](assets/zyrx_logo.png)

Spiuwirkid's ZYRX is a cutting-edge load testing tool engineered for modern web applications and APIs. With advanced analytics and real-time monitoring, ZYRX delivers precise performance insights under any load scenario.

## About Spiuwirkid - ZYRX

Created by Spiuwirkid, ZYRX represents the future of performance testing, combining power with precision. Built for modern web applications and APIs, ZYRX provides comprehensive insights into your system's performance under various load conditions.

Key Differentiators:
- Advanced Real-time Analytics
- Comprehensive Performance Metrics
- Intelligent Server Analysis
- Modern and Intuitive Interface
- Detailed HTML Reports

## Quick Start

```bash
python zyrx.py
```

## Features

- **Multiple HTTP Methods Support**
  - GET, POST, PUT, DELETE
  - Custom headers and body configuration
  - JSON payload support

- **Flexible Load Configuration**
  - Concurrent users (1-1000)
  - Requests per user (1-10000)
  - Configurable delay between requests
  - Ramp-up period support

- **Advanced Options**
  - Keep-alive connections
  - Configurable timeout
  - SSL verification toggle
  - Custom headers support

- **Real-time Monitoring**
  - Success/Error rate
  - Response times (avg/min/max)
  - Requests per second
  - Throughput monitoring
  - Total data transferred

- **Data Export**
  - HTML export support
  - Detailed test results
  - Timestamp-based file naming

## Requirements

- Python 3.x
- Required packages:
  ```bash
  pip install requests
  ```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/load-testing-tool.git
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python ddos.py
   ```

## Usage Guide

### Basic Configuration

1. **Target Setup**
   - Enter the target URL (must start with http:// or https://)
   - Select HTTP method (GET, POST, PUT, DELETE)
   - Configure headers and body if needed

2. **Load Parameters**
   - Set number of concurrent users
   - Define requests per user
   - Adjust delay between requests
   - Configure ramp-up period if needed

3. **Running Tests**
   - Click "Start Test" to begin
   - Monitor real-time statistics
   - Use "Stop Test" to end the test
   - Export results as needed

### Advanced Configuration

1. **Headers Configuration**
   ```json
   {
     "Content-Type": "application/json",
     "Authorization": "Bearer your-token"
   }
   ```

2. **Body Configuration (for POST/PUT)**
   ```json
   {
     "key": "value",
     "data": "test"
   }
   ```

3. **Performance Options**
   - Enable/disable keep-alive
   - Adjust connection timeout
   - Configure ramp-up period

## Test Scenarios

### Light Load Test
- Concurrent Users: 10
- Requests per User: 100
- Delay: 100ms
- Ramp-up: 10s

### Heavy Load Test
- Concurrent Users: 100
- Requests per User: 1000
- Delay: 10ms
- Ramp-up: 30s

### Stress Test
- Concurrent Users: 500
- Requests per User: 5000
- Delay: 0ms
- Ramp-up: 60s

## Metrics Explained

- **Success Rate**: Percentage of successful requests
- **Response Time**: Time taken for request completion
- **Throughput**: Data transfer rate in KB/s
- **RPS**: Requests per second
- **Total Data**: Total amount of data transferred

## Best Practices

1. **Start Small**
   - Begin with small user counts
   - Gradually increase load
   - Monitor system resources

2. **Use Ramp-up**
   - Prevents sudden server overload
   - More realistic user simulation
   - Better for sustained testing

3. **Monitor Errors**
   - Watch error rates
   - Check response times
   - Monitor throughput

## Export Format

The CSV export includes:
- Total Requests
- Success Count
- Error Count
- Average Response Time
- Minimum Response Time
- Maximum Response Time

## Legal Notice

This tool is for legitimate load testing purposes only. Ensure you have permission to perform load testing on the target system. Unauthorized testing may be illegal.

## Contributing

Contributions are welcome! Please feel free to submit pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Author

[Your Name]

## Acknowledgments

- Thanks to all contributors
- Inspired by professional load testing tools
- Built for educational purposes

## SSL Configuration

The tool provides SSL verification options:

- **Verify SSL**: Enable for production sites with valid SSL certificates
- **Disable SSL Verification**: Use for testing internal/development environments

Note: Disabling SSL verification is not recommended for production environments.
