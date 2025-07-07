#!/usr/bin/env python3
"""
Development server for Site Safety Monitor
This replaces docker-compose for local development in WebContainer
"""

import os
import sys
import subprocess
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver

class DevServer:
    def __init__(self):
        self.processes = []
    
    def start_static_server(self, port=8000, directory="examples/streaming_web/frontend/public"):
        """Start a static file server for frontend assets"""
        if os.path.exists(directory):
            os.chdir(directory)
            handler = SimpleHTTPRequestHandler
            with socketserver.TCPServer(("", port), handler) as httpd:
                print(f"Static server running at http://localhost:{port}")
                print(f"Serving files from: {directory}")
                httpd.serve_forever()
        else:
            print(f"Directory {directory} not found")
    
    def start_python_app(self, app_path, port=8001):
        """Start a Python application"""
        if os.path.exists(app_path):
            try:
                # Change to the app directory
                app_dir = os.path.dirname(app_path)
                if app_dir:
                    os.chdir(app_dir)
                
                # Start the Python app
                cmd = [sys.executable, os.path.basename(app_path)]
                process = subprocess.Popen(cmd, env={**os.environ, 'PORT': str(port)})
                self.processes.append(process)
                print(f"Python app started: {app_path} on port {port}")
                return process
            except Exception as e:
                print(f"Error starting {app_path}: {e}")
        else:
            print(f"App file {app_path} not found")
        return None
    
    def stop_all(self):
        """Stop all running processes"""
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()
        self.processes.clear()

def main():
    print("🚀 Starting Site Safety Monitor Development Environment")
    print("=" * 60)
    
    dev_server = DevServer()
    
    try:
        # Check if we're in the project root
        if not os.path.exists("main.py"):
            print("❌ Please run this from the project root directory")
            return
        
        print("📋 Available services:")
        print("1. Main application (main.py)")
        print("2. YOLO Server API (examples/YOLO_server_api/backend/app.py)")
        print("3. Streaming Web Backend (examples/streaming_web/backend/app.py)")
        print("4. Static file server for frontend")
        print()
        
        # Start main application
        print("🔧 Starting main application...")
        main_process = dev_server.start_python_app("main.py", 8001)
        
        # Start static file server in a separate thread
        print("🌐 Starting static file server...")
        static_thread = threading.Thread(
            target=dev_server.start_static_server,
            args=(8000, "examples/streaming_web/frontend/public"),
            daemon=True
        )
        static_thread.start()
        
        print()
        print("✅ Development environment is running!")
        print("📍 Access points:")
        print("   - Static files: http://localhost:8000")
        print("   - Main app: http://localhost:8001")
        print()
        print("Press Ctrl+C to stop all services")
        
        # Keep the main thread alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Shutting down development environment...")
        dev_server.stop_all()
        print("✅ All services stopped")

if __name__ == "__main__":
    main()