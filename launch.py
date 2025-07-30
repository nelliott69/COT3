#!/usr/bin/env python3

"""
COT Positions Analyzer - One-Click Launcher
Installs dependencies and runs the app in one command
"""

import subprocess
import sys
import os

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python {sys.version.split()[0]} detected")

def check_and_install_packages():
    """Check if packages are installed, install if missing"""
    print("Checking dependencies...")
    
    packages_to_check = [
        ("streamlit", "streamlit>=1.47.1"),
        ("pandas", "pandas>=2.3.1"), 
        ("plotly", "plotly>=6.2.0"),
        ("requests", "requests>=2.32.4"),
        ("numpy", "numpy>=2.3.2"),
        ("cot_reports", "cot-reports>=0.1.3")
    ]
    
    missing_packages = []
    
    for import_name, pip_name in packages_to_check:
        try:
            __import__(import_name)
            print(f"  ✅ {import_name}")
        except ImportError:
            print(f"  ❌ {import_name} missing")
            missing_packages.append(pip_name)
    
    if missing_packages:
        print(f"\nInstalling missing packages: {', '.join(missing_packages)}")
        for package in missing_packages:
            try:
                print(f"Installing {package}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", package], 
                                    stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
                print(f"  ✅ {package} installed")
            except subprocess.CalledProcessError:
                print(f"  ❌ Failed to install {package}")
                print(f"\nPlease install manually: pip install {package}")
                return False
        
        # Re-test imports after installation
        print("\nVerifying installations...")
        for import_name, _ in packages_to_check:
            try:
                __import__(import_name)
                print(f"  ✅ {import_name} verified")
            except ImportError:
                print(f"  ❌ {import_name} still not working")
                return False
    
    print("✅ All dependencies ready!")
    return True

def run_app():
    """Launch the Streamlit app"""
    if not os.path.exists("app.py"):
        print("❌ Error: app.py not found in current directory")
        return False
    
    print("\n🚀 Launching COT Positions Analyzer...")
    print("📊 The app will open in your browser at http://localhost:8501")
    print("🛑 Press Ctrl+C to stop the application\n")
    
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
    except KeyboardInterrupt:
        print("\n👋 COT Analyzer stopped")
    except Exception as e:
        print(f"❌ Error running app: {e}")
        return False
    
    return True

def main():
    """Main launcher function"""
    print("COT Positions Analyzer - One-Click Launcher")
    print("=" * 45)
    
    # Check Python version
    check_python_version()
    
    # Check and install dependencies
    if not check_and_install_packages():
        print("\n❌ Setup failed. Please check error messages above.")
        sys.exit(1)
    
    # Run the app
    run_app()

if __name__ == "__main__":
    main()