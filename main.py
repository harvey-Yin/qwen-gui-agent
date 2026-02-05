"""
GUI-Agent Main Entry Point
Launches the Streamlit application.
"""
import subprocess
import sys
from pathlib import Path


def main():
    """Launch the Streamlit app."""
    app_path = Path(__file__).parent / "ui" / "streamlit_app.py"
    
    print("🤖 Starting GUI-Agent...")
    print(f"   App path: {app_path}")
    print("   Press Ctrl+C to stop\n")
    
    # Run Streamlit
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        str(app_path),
        "--server.port", "8501",
        "--server.headless", "false"
    ])


if __name__ == "__main__":
    main()
