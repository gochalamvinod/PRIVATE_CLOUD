"""
Lightweight file change watcher using standard Python library (no third-party watchdog dependency).
Monitors SERVER.txt and triggers server_html_creater.py when updated.
"""

import os
import time
import subprocess
import itertools

def monitor_file(file_to_watch, script_to_run):
    """Monitors a file for changes using standard Python library."""
    if not os.path.exists(file_to_watch):
        print(f"File {file_to_watch} does not exist. Creating it...")
        with open(file_to_watch, 'w', encoding='utf-8') as f:
            f.write("")

    last_mtime = os.path.getmtime(file_to_watch)
    spinner = itertools.cycle(['|', '/', '-', '\\'])
    print(f"Monitoring {file_to_watch} for changes...")
    try:
        while True:
            time.sleep(1)
            current_mtime = os.path.getmtime(file_to_watch)
            if current_mtime != last_mtime:
                last_mtime = current_mtime
                print(f"\nFile modified. Running {script_to_run}...")
                subprocess.run(["python", script_to_run], check=True)
            print(f"\rMonitoring file... {next(spinner)}", end='', flush=True)
    except KeyboardInterrupt:
        print("\nStopped monitoring.")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_to_watch = os.path.join(base_dir, "SERVER.txt")
    script_to_run = os.path.join(base_dir, "server_html_creater.py")
    
    monitor_file(file_to_watch, script_to_run)
