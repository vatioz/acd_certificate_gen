"""
Launcher script for Certificate Generator
This script starts the Streamlit application.
"""
import os
import sys
import subprocess

def main():
    # Determine the path to app.py
    # When running as PyInstaller bundle, files are in _MEIPASS temp directory
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        bundle_dir = sys._MEIPASS
    else:
        # Running as normal Python script
        bundle_dir = os.path.dirname(os.path.abspath(__file__))
    
    app_path = os.path.join(bundle_dir, "app.py")
    
    # Check if app.py exists
    if not os.path.exists(app_path):
        print("Error: app.py not found!")
        print(f"Looking in: {bundle_dir}")
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Launch Streamlit
    print("Starting Certificate Generator...")
    print("The app will open in your browser shortly.")
    print("To stop the app, close this window or press Ctrl+C")
    print("-" * 50)
    
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", app_path,
            "--server.headless", "true"
        ])
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error starting application: {e}")
        input("Press Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()
