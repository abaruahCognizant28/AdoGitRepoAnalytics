#!/usr/bin/env python3
"""
Launcher script for Azure DevOps Git Repository Analytics Tool
Choose between Command Line Interface (CLI) and Web UI modes
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path


def print_banner():
    """Print application banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                     Azure DevOps Git Repository Analytics                   ║
║                                                                              ║
║  📊 Comprehensive analytics for Azure DevOps Git repositories               ║
║  🔍 Extract insights from commits, authors, branches, and pull requests     ║
║  📈 Generate detailed reports and visualizations                            ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def check_dependencies():
    """Check if required dependencies are installed"""
    missing_deps = []
    
    try:
        import streamlit
    except ImportError:
        missing_deps.append("streamlit")
    
    try:
        import plotly
    except ImportError:
        missing_deps.append("plotly")
    
    try:
        import pandas
    except ImportError:
        missing_deps.append("pandas")
    
    if missing_deps:
        print("❌ Missing required dependencies:")
        for dep in missing_deps:
            print(f"   • {dep}")
        print("\n📦 Install missing dependencies with:")
        print("   pip install -r requirements.txt")
        return False
    
    return True


def launch_cli():
    """Launch the command line interface"""
    print("🚀 Launching Command Line Interface...")
    print("   Use Ctrl+C to exit\n")
    
    try:
        # Run the CLI version
        subprocess.run([sys.executable, "run.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ CLI failed to start: {e}")
        return False
    except KeyboardInterrupt:
        print("\n👋 CLI session ended")
        return True
    
    return True


def launch_ui():
    """Launch the web UI interface"""
    print("🚀 Launching Web UI Interface...")
    print("   The application will open in your default web browser")
    print("   Use Ctrl+C to stop the server\n")
    
    ui_path = Path("ui/app.py")
    if not ui_path.exists():
        print(f"❌ UI application not found: {ui_path}")
        return False
    
    try:
        # Run Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(ui_path),
            "--server.headless", "false",
            "--server.runOnSave", "true",
            "--browser.gatherUsageStats", "false"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Web UI failed to start: {e}")
        return False
    except KeyboardInterrupt:
        print("\n👋 Web UI server stopped")
        return True
    
    return True


def launch_database_cli():
    """Launch the database CLI tool"""
    print("🚀 Launching Database CLI...")
    print("   Use 'python db_cli.py --help' for available commands\n")
    
    try:
        # Show database CLI help
        subprocess.run([sys.executable, "db_cli.py", "--help"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Database CLI failed: {e}")
        return False
    
    return True


def interactive_mode():
    """Run in interactive mode with menu"""
    while True:
        print("\n" + "="*60)
        print("          AZURE DEVOPS GIT ANALYTICS LAUNCHER")
        print("="*60)
        print("\nChoose how you want to run the application:")
        print("  1️⃣  Web UI (Recommended for beginners)")
        print("  2️⃣  Command Line Interface (Advanced users)")
        print("  3️⃣  Database CLI (Manage stored data)")
        print("  4️⃣  Configuration Check")
        print("  5️⃣  Install/Update Dependencies")
        print("  0️⃣  Exit")
        print("-" * 60)
        
        choice = input("Enter your choice (0-5): ").strip()
        
        if choice == "1":
            if check_dependencies():
                launch_ui()
            else:
                input("\nPress Enter to continue...")
        
        elif choice == "2":
            launch_cli()
        
        elif choice == "3":
            launch_database_cli()
        
        elif choice == "4":
            check_configuration()
            input("\nPress Enter to continue...")
        
        elif choice == "5":
            install_dependencies()
            input("\nPress Enter to continue...")
        
        elif choice == "0":
            print("\n👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please select 0-5.")


def check_configuration():
    """Check configuration status"""
    print("\n🔍 Checking Configuration...")
    print("-" * 40)
    
    # Check environment file
    env_file = Path(".env")
    if env_file.exists():
        print("✅ Environment file (.env) exists")
    else:
        print("❌ Environment file (.env) missing")
        print("   Create from template: cp env.template .env")
    
    # Check config file
    config_file = Path("config/repositories.yaml")
    if config_file.exists():
        print("✅ Configuration file exists")
    else:
        print("❌ Configuration file missing")
        print("   Check config/repositories.yaml")
    
    # Check output directory
    output_dir = Path("output")
    if output_dir.exists():
        print("✅ Output directory exists")
    else:
        print("⚠️  Output directory will be created automatically")
    
    # Check logs directory
    logs_dir = Path("logs")
    if logs_dir.exists():
        print("✅ Logs directory exists")
    else:
        print("⚠️  Logs directory will be created automatically")
    
    print("\n💡 Configuration Tips:")
    print("   • Set your Azure DevOps PAT in .env file")
    print("   • Configure projects and repositories in config/repositories.yaml")
    print("   • Use the Web UI for easy configuration management")


def install_dependencies():
    """Install or update dependencies"""
    print("\n📦 Installing Dependencies...")
    print("-" * 40)
    
    try:
        # Upgrade pip first
        print("Upgrading pip...")
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                      check=True, capture_output=True)
        print("✅ pip upgraded")
        
        # Install requirements
        print("Installing requirements...")
        result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                              check=True, capture_output=True, text=True)
        print("✅ Dependencies installed successfully")
        
        # Show what was installed
        if result.stdout:
            print("\nInstallation details:")
            print(result.stdout[-500:])  # Show last 500 chars
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        if e.stderr:
            print(f"Error: {e.stderr}")
    except FileNotFoundError:
        print("❌ requirements.txt not found")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Azure DevOps Git Repository Analytics Tool Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Interactive mode (default)
  %(prog)s --ui               # Launch Web UI directly
  %(prog)s --cli              # Launch CLI directly
  %(prog)s --db               # Launch Database CLI
  %(prog)s --check            # Check configuration
  %(prog)s --install          # Install dependencies
        """
    )
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--ui", action="store_true", help="Launch Web UI directly")
    group.add_argument("--cli", action="store_true", help="Launch CLI directly")
    group.add_argument("--db", action="store_true", help="Launch Database CLI")
    group.add_argument("--check", action="store_true", help="Check configuration only")
    group.add_argument("--install", action="store_true", help="Install/update dependencies")
    
    parser.add_argument("--skip-banner", action="store_true", help="Skip banner display")
    
    args = parser.parse_args()
    
    # Print banner unless skipped
    if not args.skip_banner:
        print_banner()
    
    # Handle direct launch modes
    if args.ui:
        if check_dependencies():
            return 0 if launch_ui() else 1
        else:
            return 1
    
    elif args.cli:
        return 0 if launch_cli() else 1
    
    elif args.db:
        return 0 if launch_database_cli() else 1
    
    elif args.check:
        check_configuration()
        return 0
    
    elif args.install:
        install_dependencies()
        return 0
    
    else:
        # Interactive mode
        try:
            interactive_mode()
            return 0
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            return 0
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            return 1


if __name__ == "__main__":
    sys.exit(main()) 