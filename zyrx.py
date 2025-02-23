import tkinter as tk
from tkinter import ttk, messagebox
import threading
import requests
import time
import statistics
from datetime import datetime
import json
import csv
import urllib3
import numpy as np
from collections import deque
from datetime import timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import queue
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)  # Disable SSL warnings

class LoadTester:
    def __init__(self, root):
        self.root = root
        self.root.title("Spiuwirkid - ZYRX v2.0")
        self.root.geometry("800x600")
        
        # Create main scrollable canvas
        self.main_canvas = tk.Canvas(self.root)
        self.scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.main_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.main_canvas)
        
        # Configure scrolling
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        )
        
        self.main_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.main_canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack scrollbar components
        self.main_canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Add mousewheel scrolling
        self.main_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # Test Configuration
        self.is_testing = False
        self.threads = []
        self.response_times = []
        self.success_count = 0
        self.error_count = 0
        self.start_time = None
        
        # Tambahkan metrics baru
        self.total_bytes = 0
        self.start_memory = 0
        self.request_rates = []
        self.session = requests.Session()  # Gunakan session untuk koneksi yang lebih efisien
        
        # Add SSL verification option
        self.verify_ssl = tk.BooleanVar(value=False)
        
        # Tambahan metrics untuk analisis server
        self.response_codes = {}  # Track HTTP response codes
        self.response_history = deque(maxlen=1000)  # Track response times history
        self.error_types = {}  # Track jenis error
        self.server_headers = {}  # Track server information
        self.bandwidth_history = deque(maxlen=1000)  # Track bandwidth usage
        
        # Add queue for logging and stats
        self.log_queue = queue.Queue()
        self.stats_queue = queue.Queue()
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # GUI Components
        self.create_widgets()
        
        self.active_threads = 0  # Add counter for active threads
        
        # Start background tasks
        self.start_background_tasks()
        
    def _on_mousewheel(self, event):
        self.main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def create_widgets(self):
        # Create main frame
        main_frame = ttk.Frame(self.scrollable_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Target Configuration
        target_frame = ttk.LabelFrame(main_frame, text="Target Configuration")
        target_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(target_frame, text="Target URL:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.target_entry = ttk.Entry(target_frame, width=50)
        self.target_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Test Configuration
        test_frame = ttk.LabelFrame(main_frame, text="Test Configuration")
        test_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(test_frame, text="Method:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.method_type = ttk.Combobox(test_frame, values=["GET", "POST", "PUT", "DELETE"])
        self.method_type.grid(row=0, column=1, padx=5, pady=5)
        self.method_type.current(0)
        
        ttk.Label(test_frame, text="Headers (JSON):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.headers_entry = ttk.Entry(test_frame, width=50)
        self.headers_entry.grid(row=1, column=1, padx=5, pady=5)
        self.headers_entry.insert(0, '{"Content-Type": "application/json"}')
        
        ttk.Label(test_frame, text="Body (JSON):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.body_entry = ttk.Entry(test_frame, width=50)
        self.body_entry.grid(row=2, column=1, padx=5, pady=5)
        
        # Load Configuration
        load_frame = ttk.LabelFrame(main_frame, text="Load Configuration")
        load_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(load_frame, text="Concurrent Users:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.threads_spin = ttk.Spinbox(load_frame, from_=1, to=1000)
        self.threads_spin.grid(row=0, column=1, padx=5, pady=5)
        self.threads_spin.set(10)
        
        ttk.Label(load_frame, text="Requests per User:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.requests_spin = ttk.Spinbox(load_frame, from_=1, to=10000)
        self.requests_spin.grid(row=1, column=1, padx=5, pady=5)
        self.requests_spin.set(100)
        
        ttk.Label(load_frame, text="Delay between requests (ms):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.delay_spin = ttk.Spinbox(load_frame, from_=0, to=5000)
        self.delay_spin.grid(row=2, column=1, padx=5, pady=5)
        self.delay_spin.set(100)
        
        # Control Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.start_btn = ttk.Button(button_frame, text="Start Test", command=self.start_test)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(button_frame, text="Stop Test", command=self.stop_test, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.export_btn = ttk.Button(button_frame, text="Export Results", command=self.export_results)
        self.export_btn.pack(side=tk.LEFT, padx=5)
        
        # Statistics Frame
        stats_frame = ttk.LabelFrame(main_frame, text="Real-time Statistics")
        stats_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.stats_text = tk.Text(stats_frame, height=3, width=70)
        self.stats_text.pack(padx=5, pady=5)
        
        # Log Area
        log_frame = ttk.LabelFrame(main_frame, text="Test Log")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_text = tk.Text(log_frame, height=10, width=70)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add scrollbar to log
        scrollbar = ttk.Scrollbar(self.log_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.log_text.yview)
        
        # Tambahkan konfigurasi advanced
        advanced_frame = ttk.LabelFrame(main_frame, text="Advanced Configuration")
        advanced_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(advanced_frame, text="Keep-Alive:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.keepalive_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(advanced_frame, variable=self.keepalive_var).grid(row=0, column=1)
        
        ttk.Label(advanced_frame, text="Connection Timeout (s):").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.timeout_spin = ttk.Spinbox(advanced_frame, from_=1, to=60)
        self.timeout_spin.grid(row=1, column=1)
        self.timeout_spin.set(10)
        
        ttk.Label(advanced_frame, text="Ramp-up Period (s):").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.rampup_spin = ttk.Spinbox(advanced_frame, from_=0, to=300)
        self.rampup_spin.grid(row=2, column=1)
        self.rampup_spin.set(0)
        
        # Add SSL verification checkbox to advanced frame
        ttk.Label(advanced_frame, text="Verify SSL:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        ttk.Checkbutton(advanced_frame, variable=self.verify_ssl).grid(row=3, column=1)

        # Adjust frame packing to work better with scrolling
        for frame in [target_frame, test_frame, load_frame, button_frame, 
                     stats_frame, log_frame, advanced_frame]:
            frame.pack(fill=tk.X, padx=5, pady=5, anchor="n")

    def start_background_tasks(self):
        """Start background tasks for UI updates"""
        self.root.after(100, self.process_log_queue)
        self.root.after(500, self.process_stats_queue)
        
    def process_log_queue(self):
        """Process logs in background"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
                self.log_text.see(tk.END)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_log_queue)
            
    def process_stats_queue(self):
        """Process stats updates in background"""
        try:
            while True:
                stats = self.stats_queue.get_nowait()
                self.stats_text.delete(1.0, tk.END)
                self.stats_text.insert(tk.END, stats)
        except queue.Empty:
            pass
        finally:
            self.root.after(500, self.process_stats_queue)

    async def async_request(self, session, method, url, headers, data, timeout):
        """Async request handler"""
        try:
            async with session.request(
                method=method, 
                url=url, 
                headers=headers,
                json=data,
                timeout=timeout,
                ssl=self.verify_ssl.get()
            ) as response:
                content = await response.read()
                return response, content
        except Exception as e:
            return None, str(e)

    async def async_load_test(self, total_requests):
        """Async load test implementation"""
        try:
            async with aiohttp.ClientSession() as session:
                batch_size = min(100, total_requests)
                delay = float(self.delay_spin.get()) / 1000
                rampup = float(self.rampup_spin.get())
                
                if rampup > 0:
                    delay_increment = rampup / (total_requests / batch_size)
                
                for i in range(0, total_requests, batch_size):
                    if not self.is_testing:
                        break
                    
                    # Create batch of requests
                    batch = []
                    current_batch_size = min(batch_size, total_requests - i)
                    
                    for _ in range(current_batch_size):
                        batch.append(self.async_request(
                            session=session,
                            method=self.method_type.get(),
                            url=self.target_entry.get(),
                            headers=self.headers,
                            data=self.body,
                            timeout=float(self.timeout_spin.get())
                        ))
                    
                    # Execute batch
                    responses = await asyncio.gather(*batch, return_exceptions=True)
                    self.process_responses(responses)
                    
                    # Calculate dynamic delay for ramp-up
                    if rampup > 0:
                        current_delay = delay - (i * delay_increment / total_requests)
                        await asyncio.sleep(max(0, current_delay))
                    elif delay > 0:
                        await asyncio.sleep(delay)
                
                # Wait for remaining requests to complete
                await asyncio.sleep(1)
                
                # Test completed
                if self.is_testing:
                    self.root.after(100, self.auto_stop)
                
        except Exception as e:
            self.log_queue.put(f"Load test error: {str(e)}")
            self.root.after(100, self.auto_stop)

    def process_responses(self, responses):
        """Process batch responses"""
        for response, content in responses:
            try:
                start_time = time.time()
                
                if isinstance(content, str):  # Error occurred
                    self.error_count += 1
                    error_type = content.split(':')[0]
                    self.error_types[error_type] = self.error_types.get(error_type, 0) + 1
                    self.log_queue.put(f"Error: {content}")
                    elapsed = time.time() - start_time
                    self.response_times.append(elapsed)
                else:
                    self.success_count += 1
                    self.total_bytes += len(content)
                    status = response.status
                    self.response_codes[status] = self.response_codes.get(status, 0) + 1
                    
                    elapsed = time.time() - start_time
                    self.response_times.append(elapsed)
                    self.bandwidth_history.append(len(content) / elapsed)
                    
                    # Analyze server response
                    server_info, _ = self.analyze_server_response(response)
                    self.log_queue.put(
                        f"Success: {status} - {len(content)} bytes - "
                        f"Response: {elapsed:.3f}s - Server: {server_info.get('Server', 'Unknown')}"
                    )
                    
            except Exception as e:
                self.error_count += 1
                self.log_queue.put(f"Processing error: {str(e)}")
                
        if self.response_times:
            self.update_stats_async()

    def update_stats_async(self):
        """Update stats without blocking UI"""
        stats = self.calculate_server_metrics()
        self.stats_queue.put(self.format_stats(stats))

    def log(self, message):
        """Add message to log queue"""
        self.log_queue.put(message)

    def start_test(self):
        if not self.validate_input():
            return
            
        self.is_testing = True
        self.start_time = time.time()
        self.reset_counters()
        
        # Parse headers and body
        try:
            self.headers = json.loads(self.headers_entry.get()) if self.headers_entry.get() else {}
            self.body = json.loads(self.body_entry.get()) if self.body_entry.get() else None
        except:
            self.headers = {}
            self.body = None
        
        # Update button states
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        
        thread_count = int(self.threads_spin.get())
        requests_per_thread = int(self.requests_spin.get())
        
        # Start the test in a separate thread
        test_thread = threading.Thread(
            target=self._run_async_test,
            args=(thread_count * requests_per_thread,)
        )
        test_thread.daemon = True
        test_thread.start()
        
        self.log(f"Started load test with {thread_count} concurrent users")

    def _run_async_test(self, total_requests):
        """Run async test in a separate thread"""
        try:
            asyncio.run(self.async_load_test(total_requests))
        except Exception as e:
            self.log_queue.put(f"Test error: {str(e)}")
            self.auto_stop()

    def stop_test(self):
        self.is_testing = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.log("Test stopped")

    def export_results(self):
        if not self.response_times:
            messagebox.showwarning("Warning", "No test results to export")
            return
            
        try:
            # Calculate metrics for report
            metrics = self.calculate_server_metrics()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Spiuwirkid_ZYRX_report_{timestamp}.html"
            
            # Create separate figures for each visualization
            # 1. Response Time Distribution
            fig_resp_time = go.Figure(data=[
                go.Histogram(x=list(self.response_times), name="Response Times")
            ])
            fig_resp_time.update_layout(
                title="Response Time Distribution",
                xaxis_title="Time (seconds)",
                yaxis_title="Count"
            )

            # 2. RPS over time
            fig_rps = go.Figure(data=[
                go.Scatter(y=list(self.bandwidth_history), name="Requests/Second")
            ])
            fig_rps.update_layout(
                title="Requests per Second Over Time",
                xaxis_title="Request Number",
                yaxis_title="RPS"
            )

            # 3. Error Distribution
            error_data = []
            if self.error_types:
                error_data = [go.Pie(
                    labels=list(self.error_types.keys()),
                    values=list(self.error_types.values()),
                    name="Errors"
                )]
            else:
                error_data = [go.Pie(
                    labels=['No Errors'],
                    values=[1],
                    name="Errors"
                )]
            fig_errors = go.Figure(data=error_data)
            fig_errors.update_layout(title="Error Distribution")

            # 4. Response Codes
            response_data = []
            if self.response_codes:
                response_data = [go.Bar(
                    x=[str(code) for code in self.response_codes.keys()],
                    y=list(self.response_codes.values()),
                    name="Response Codes"
                )]
            else:
                response_data = [go.Bar(
                    x=['No Data'],
                    y=[0],
                    name="Response Codes"
                )]
            fig_resp_codes = go.Figure(data=response_data)
            fig_resp_codes.update_layout(
                title="Response Code Distribution",
                xaxis_title="Response Code",
                yaxis_title="Count"
            )

            # Generate HTML report
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Spiuwirkid - ZYRX Performance Report - {timestamp}</title>
                <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap" rel="stylesheet">
                <style>
                    body {{
                        font-family: 'Roboto', sans-serif;
                        margin: 0;
                        padding: 0;
                        background-color: #f0f2f5;
                        color: #333;
                    }}
                    .container {{
                        max-width: 1200px;
                        margin: 40px auto;
                        background-color: white;
                        padding: 30px;
                        border-radius: 15px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }}
                    .header {{
                        background: linear-gradient(135deg, #2196F3, #1976D2);
                        color: white;
                        padding: 30px;
                        border-radius: 12px;
                        margin-bottom: 30px;
                        text-align: center;
                    }}
                    .header h1 {{
                        margin: 0;
                        font-size: 2.5em;
                        font-weight: 500;
                    }}
                    .metric-box {{
                        border: 1px solid #e0e0e0;
                        padding: 25px;
                        margin: 20px 0;
                        border-radius: 12px;
                        background-color: #fff;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                    }}
                    .chart-container {{
                        display: grid;
                        grid-template-columns: 1fr 1fr;
                        gap: 25px;
                        margin: 30px 0;
                    }}
                    .chart {{
                        border: 1px solid #e0e0e0;
                        padding: 20px;
                        border-radius: 12px;
                        background-color: white;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                    }}
                    .status-indicator {{
                        display: inline-block;
                        padding: 8px 15px;
                        border-radius: 20px;
                        font-weight: 500;
                        margin: 10px 0;
                    }}
                    .status-good {{ background-color: #4CAF50; color: white; }}
                    .status-warning {{ background-color: #FFC107; color: black; }}
                    .status-critical {{ background-color: #F44336; color: white; }}
                    .metric-grid {{
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                        gap: 20px;
                        margin: 20px 0;
                    }}
                    .metric-item {{
                        background: #f8f9fa;
                        padding: 15px;
                        border-radius: 8px;
                        text-align: center;
                    }}
                    .metric-value {{
                        font-size: 24px;
                        font-weight: 500;
                        color: #2196F3;
                    }}
                    .metric-label {{
                        font-size: 14px;
                        color: #666;
                        margin-top: 5px;
                    }}
                    .security-grid {{
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                        gap: 15px;
                    }}
                    .security-item {{
                        background: #fff;
                        padding: 15px;
                        border-radius: 8px;
                        border: 1px solid #e0e0e0;
                    }}
                    .recommendation-box {{
                        background: #e3f2fd;
                        padding: 20px;
                        border-radius: 8px;
                        margin: 20px 0;
                    }}
                    .performance-summary {{
                        background: #f5f5f5;
                        padding: 20px;
                        border-radius: 8px;
                        margin: 20px 0;
                    }}
                    .navbar {{
                        background: linear-gradient(135deg, #1a237e, #0d47a1);  /* ZYRX brand colors */
                        padding: 10px 20px;
                        color: white;
                        text-align: center;
                    }}
                    .navbar-title {{
                        font-size: 1.4em;
                        font-weight: 700;
                        letter-spacing: 2px;
                        content: 'Spiuwirkid - ZYRX';
                    }}
                    .footer {{
                        text-align: center;
                        padding: 20px;
                        color: #666;
                    }}
                </style>
            </head>
            <body>
                <div class="navbar">
                    <div class="navbar-title">Spiuwirkid - ZYRX Performance Report</div>
                </div>
                <div class="container">
                    <div class="header">
                        <h1>ZYRX Performance Report</h1>
                        <p>Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                    </div>

                    <div class="metric-box">
                        <h2>Server Performance Summary</h2>
                        <div class="status-indicator status-{self._get_server_health_class(metrics)}">
                            {self._get_performance_summary(metrics)}
                        </div>
                        <div class="performance-summary">
                            <h3>Key Findings:</h3>
                            {self._generate_performance_analysis(metrics)}
                        </div>
                    </div>

                    <div class="metric-box">
                        <h2>Test Configuration</h2>
                        <div class="metric-grid">
                            <div class="metric-item">
                                <div class="metric-value">{self.threads_spin.get()}</div>
                                <div class="metric-label">Concurrent Users</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-value">{self.requests_spin.get()}</div>
                                <div class="metric-label">Requests per User</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-value">{self.delay_spin.get()}ms</div>
                                <div class="metric-label">Request Delay</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-value">{self.method_type.get()}</div>
                                <div class="metric-label">HTTP Method</div>
                            </div>
                        </div>
                        <p><strong>Target URL:</strong> {self.target_entry.get()}</p>
                    </div>

                    <div class="metric-box">
                        <h2>Performance Metrics</h2>
                        <div class="metric-grid">
                            <div class="metric-item">
                                <div class="metric-value">{metrics['response_time']['avg']:.3f}s</div>
                                <div class="metric-label">Average Response Time</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-value">{metrics['throughput']['requests_per_sec']:.1f}</div>
                                <div class="metric-label">Requests/Second</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-value">{(self.success_count/(self.success_count + self.error_count))*100:.1f}%</div>
                                <div class="metric-label">Success Rate</div>
                            </div>
                            <div class="metric-item">
                                <div class="metric-value">{self.total_bytes/1024/1024:.1f} MB</div>
                                <div class="metric-label">Total Data Transferred</div>
                            </div>
                        </div>
                    </div>

                    <div class="chart-container">
                        <div class="chart">
                            {fig_resp_time.to_html(full_html=False, include_plotlyjs=False)}
                        </div>
                        <div class="chart">
                            {fig_rps.to_html(full_html=False, include_plotlyjs=False)}
                        </div>
                        <div class="chart">
                            {fig_errors.to_html(full_html=False, include_plotlyjs=False)}
                        </div>
                        <div class="chart">
                            {fig_resp_codes.to_html(full_html=False, include_plotlyjs=False)}
                        </div>
                    </div>

                    <div class="metric-box">
                        <h2>Server Analysis</h2>
                        <div class="security-grid">
                            <div class="security-item">
                                <h3>Server Information</h3>
                                <p><strong>Server Type:</strong> {metrics['server_info'].get('Server', 'Unknown')}</p>
                                <p><strong>Technology:</strong> {metrics['server_info'].get('X-Powered-By', 'Unknown')}</p>
                                <p><strong>Content Type:</strong> {metrics['server_info'].get('Content-Type', 'Unknown')}</p>
                            </div>
                            <div class="security-item">
                                <h3>Security Headers</h3>
                                {self._generate_security_analysis()}
                            </div>
                        </div>
                    </div>

                    <div class="metric-box">
                        <h2>Recommendations</h2>
                        {self._generate_recommendations(metrics)}
                    </div>
                </div>
                <div class="footer">
                    Powered by Spiuwirkid - ZYRX Performance Testing Engine
                </div>
            </body>
            </html>
            """
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            # Open report in default browser
            os.startfile(filename)
            messagebox.showinfo("Success", f"Report generated and opened: {filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate report: {str(e)}")

    def _get_server_health_class(self, metrics):
        """Determine server health status class"""
        if metrics['response_time']['avg'] < 0.5 and metrics['errors']['rate'] < 1:
            return "good"
        elif metrics['response_time']['avg'] < 2 and metrics['errors']['rate'] < 5:
            return "warning"
        else:
            return "critical"

    def _analyze_server_health(self, metrics):
        """Generate server health analysis"""
        avg_response = metrics['response_time']['avg']
        error_rate = metrics['errors']['rate']
        rps = metrics['throughput']['requests_per_sec']
        
        if avg_response < 0.5 and error_rate < 1:
            return f"""
                Server Performance: EXCELLENT
                • Fast response time ({avg_response:.3f}s)
                • Low error rate ({error_rate:.1f}%)
                • Good throughput ({rps:.1f} req/sec)
                • Server handles load efficiently
            """
        elif avg_response < 2 and error_rate < 5:
            return f"""
                Server Performance: MODERATE
                • Acceptable response time ({avg_response:.3f}s)
                • Moderate error rate ({error_rate:.1f}%)
                • Average throughput ({rps:.1f} req/sec)
                • Server might need optimization
            """
        else:
            return f"""
                Server Performance: POOR
                • Slow response time ({avg_response:.3f}s)
                • High error rate ({error_rate:.1f}%)
                • Low throughput ({rps:.1f} req/sec)
                • Server needs immediate attention
            """

    def _generate_security_analysis(self):
        """Generate security headers analysis"""
        security_status = ""
        headers = self.server_headers
        
        # Check security headers
        security_checks = {
            'X-Frame-Options': 'Protection against clickjacking',
            'X-XSS-Protection': 'Cross-site scripting protection',
            'X-Content-Type-Options': 'MIME-type sniffing protection',
            'Strict-Transport-Security': 'HTTPS enforcement'
        }
        
        for header, description in security_checks.items():
            value = headers.get(header, 'Not Set')
            status = "✅" if value != 'Not Set' else "❌"
            security_status += f"<p>{status} {header}: {value} ({description})</p>"
            
        return security_status

    def analyze_server_response(self, response):
        """Analyze server response and capabilities"""
        try:
            # Analyze server headers
            server_info = {
                'Server': response.headers.get('Server', 'Unknown'),
                'X-Powered-By': response.headers.get('X-Powered-By', 'Unknown'),
                'Content-Type': response.headers.get('Content-Type', 'Unknown'),
            }
            
            # Check for security headers
            security_headers = {
                'X-Frame-Options': response.headers.get('X-Frame-Options', 'Not Set'),
                'X-XSS-Protection': response.headers.get('X-XSS-Protection', 'Not Set'),
                'X-Content-Type-Options': response.headers.get('X-Content-Type-Options', 'Not Set'),
                'Strict-Transport-Security': response.headers.get('Strict-Transport-Security', 'Not Set'),
            }
            
            # Update server info
            self.server_headers.update(server_info)
            
            return server_info, security_headers
            
        except Exception as e:
            self.log(f"Error analyzing server: {str(e)}")
            return None, None

    def calculate_server_metrics(self):
        """Calculate detailed server performance metrics"""
        if not self.response_times:
            return {}
            
        metrics = {
            'response_time': {
                'avg': np.mean(self.response_times),
                'median': np.median(self.response_times),
                'p95': np.percentile(self.response_times, 95),
                'p99': np.percentile(self.response_times, 99),
                'std_dev': np.std(self.response_times)
            },
            'throughput': {
                'bytes_per_sec': self.total_bytes / (time.time() - self.start_time),
                'requests_per_sec': len(self.response_times) / (time.time() - self.start_time)
            },
            'errors': {
                'rate': (self.error_count / (self.success_count + self.error_count)) * 100,
                'types': self.error_types
            },
            'response_codes': self.response_codes,
            'server_info': self.server_headers
        }
        
        return metrics

    def auto_stop(self):
        """Auto stop when all threads complete"""
        self.is_testing = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.log("Test completed - all requests finished")
        
        # Show completion message
        messagebox.showinfo("Test Complete", 
            f"Load test completed\n"
            f"Total Requests: {self.success_count + self.error_count}\n"
            f"Success Rate: {(self.success_count/(self.success_count + self.error_count))*100:.1f}%")

    def validate_input(self):
        target = self.target_entry.get()
        if not target.startswith(("http://", "https://")):
            messagebox.showerror("Error", "Invalid target URL")
            return False
            
        try:
            if self.headers_entry.get():
                json.loads(self.headers_entry.get())
            if self.body_entry.get():
                json.loads(self.body_entry.get())
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Invalid JSON in headers or body")
            return False
            
        return True

    def reset_counters(self):
        self.success_count = 0
        self.error_count = 0
        self.response_times = []
        self.total_bytes = 0
        self.bandwidth_history.clear()
        self.response_codes.clear()
        self.server_headers.clear()
        self.error_types.clear()

    def format_stats(self, stats):
        """Format stats for display"""
        return (
            f"=== Load Test Statistics ===\n"
            f"Total Requests: {self.success_count + self.error_count}\n"
            f"Success Rate: {(self.success_count / (self.success_count + self.error_count)) * 100:.1f}%\n"
            f"Response Times:\n"
            f"  Average: {stats['response_time']['avg']:.3f}s\n"
            f"  Median: {stats['response_time']['median']:.3f}s\n"
            f"  95th percentile: {stats['response_time']['p95']:.3f}s\n"
            f"  99th percentile: {stats['response_time']['p99']:.3f}s\n"
            f"  Standard Deviation: {stats['response_time']['std_dev']:.3f}s\n"
            f"Performance:\n"
            f"  Throughput: {stats['throughput']['bytes_per_sec']/1024:.1f} KB/s\n"
            f"  Requests/sec: {stats['throughput']['requests_per_sec']:.1f}\n"
            f"Server Info:\n"
            f"  Type: {stats['server_info'].get('Server', 'Unknown')}\n"
            f"  Technology: {stats['server_info'].get('X-Powered-By', 'Unknown')}\n"
            f"Error Analysis:\n"
            f"  Error Rate: {stats['errors']['rate']:.1f}%\n"
            f"  Response Codes: {dict(stats['response_codes'])}\n"
        )

    def _get_performance_summary(self, metrics):
        """Generate a short performance summary"""
        avg_response = metrics['response_time']['avg']
        error_rate = metrics['errors']['rate']
        rps = metrics['throughput']['requests_per_sec']
        
        if avg_response < 0.5 and error_rate < 1:
            return "EXCELLENT - Server performs exceptionally well under load"
        elif avg_response < 2 and error_rate < 5:
            return "MODERATE - Server handles load adequately but could be optimized"
        else:
            return "POOR - Server struggles under current load"

    def _generate_performance_analysis(self, metrics):
        """Generate detailed performance analysis"""
        analysis = []
        
        # Response time analysis
        avg_response = metrics['response_time']['avg']
        if avg_response < 0.5:
            analysis.append("✅ Fast response times indicate efficient request processing")
        elif avg_response < 2:
            analysis.append("⚠️ Response times are acceptable but could be improved")
        else:
            analysis.append("❌ Slow response times suggest server optimization needed")
        
        # Throughput analysis
        rps = metrics['throughput']['requests_per_sec']
        if rps > 100:
            analysis.append("✅ High throughput indicates good server capacity")
        elif rps > 50:
            analysis.append("⚠️ Moderate throughput suggests room for improvement")
        else:
            analysis.append("❌ Low throughput indicates possible bottlenecks")
        
        # Error rate analysis
        error_rate = metrics['errors']['rate']
        if error_rate < 1:
            analysis.append("✅ Very low error rate shows stable performance")
        elif error_rate < 5:
            analysis.append("⚠️ Moderate error rate requires investigation")
        else:
            analysis.append("❌ High error rate indicates serious issues")
        
        return "<br>".join(analysis)

    def _generate_recommendations(self, metrics):
        """Generate performance recommendations"""
        recommendations = []
        avg_response = metrics['response_time']['avg']
        error_rate = metrics['errors']['rate']
        rps = metrics['throughput']['requests_per_sec']
        
        if avg_response > 1:
            recommendations.append("""
                <div class="recommendation-box">
                    <h3>Response Time Optimization</h3>
                    <ul>
                        <li>Consider implementing caching mechanisms</li>
                        <li>Optimize database queries</li>
                        <li>Enable compression for responses</li>
                        <li>Consider using a CDN for static content</li>
                    </ul>
                </div>
            """)
        
        if error_rate > 1:
            recommendations.append("""
                <div class="recommendation-box">
                    <h3>Error Rate Reduction</h3>
                    <ul>
                        <li>Implement better error handling</li>
                        <li>Add request validation</li>
                        <li>Consider rate limiting</li>
                        <li>Monitor server resources</li>
                    </ul>
                </div>
            """)
        
        if rps < 50:
            recommendations.append("""
                <div class="recommendation-box">
                    <h3>Throughput Improvement</h3>
                    <ul>
                        <li>Scale server resources</li>
                        <li>Optimize application code</li>
                        <li>Consider load balancing</li>
                        <li>Implement connection pooling</li>
                    </ul>
                </div>
            """)
        
        return "".join(recommendations) if recommendations else "<p>No specific recommendations at this time. Server is performing well!</p>"

if __name__ == "__main__":
    root = tk.Tk()
    
    # Set minimum window size
    root.minsize(800, 600)
    
    app = LoadTester(root)
    root.mainloop()