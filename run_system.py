"""
Healthcare Insurance Assurance Platform - Unified System Runner
Starts both the Django REST Backend (Port 8000) and the Web Frontend (Port 3000).
"""

import subprocess
import sys
import time
import os
import webbrowser

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(root_dir, 'backend')

    print("=" * 65)
    print(" HEALTHCARE PATIENT & FUND DISTRIBUTION MANAGEMENT SYSTEM")
    print("=" * 65)
    print("[1/2] Starting Django REST Backend on http://127.0.0.1:8000 ...")
    backend_proc = subprocess.Popen(
        [sys.executable, 'manage.py', 'runserver', '127.0.0.1:8000'],
        cwd=backend_dir
    )

    print("[2/2] Starting Web Frontend Server on http://localhost:3000 ...")
    frontend_proc = subprocess.Popen(
        ['node', 'server.js'],
        cwd=root_dir
    )

    time.sleep(2)
    print("\n" + "=" * 65)
    print(" Both Backend and Frontend are running!")
    print(" - Frontend Application : http://localhost:3000/")
    print(" - Django REST API Root  : http://127.0.0.1:8000/api/")
    print(" - Django Admin Portal   : http://127.0.0.1:8000/admin/")
    print("=" * 65)
    print("Press Ctrl+C to stop both servers gracefully.\n")

    try:
        backend_proc.wait()
    except KeyboardInterrupt:
        print("\nStopping servers...")
        backend_proc.terminate()
        frontend_proc.terminate()
        print("Servers stopped.")

if __name__ == '__main__':
    main()
