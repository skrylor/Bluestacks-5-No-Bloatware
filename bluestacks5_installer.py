import os
import sys
import subprocess
import shutil
from pathlib import Path
import ctypes
import time
import signal

# Automated Package Installation
required_packages = ['requests', 'colorama', 'tqdm', 'InquirerPy']

import importlib

def install_package(package):
    """Installs the specified Python package using pip."""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install package {package}. Error: {e}")
        sys.exit(1)

for package in required_packages:
    try:
        importlib.import_module(package)
    except ImportError:
        print(f"Installing missing package: {package}")
        install_package(package)

import requests
from tqdm import tqdm
from colorama import init, Fore, Style
from InquirerPy import inquirer

# Initialize colorama
init(autoreset=True)

def clear_screen():
    """Clears the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    """Prints the stylish banner."""
    banner = f"""
{Fore.CYAN}==============================================
          ██████╗ ██╗      █████╗ ████████╗███████╗
          ██╔══██╗██║     ██╔══██╗╚══██╔══╝██╔════╝
          ██████╔╝██║     ███████║   ██║   █████╗  
          ██╔══██╗██║     ██╔══██║   ██║   ██╔══╝  
          ██████╔╝███████╗██║  ██║   ██║   ███████╗
          ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝   ╚══════╝
=============================================={Style.RESET_ALL}
    """
    print(banner)

def print_info(message):
    """Prints an informational message."""
    print(f"{Fore.GREEN}[INFO]{Style.RESET_ALL} {message}")

def print_warning(message):
    """Prints a warning message."""
    print(f"{Fore.YELLOW}[WARNING]{Style.RESET_ALL} {message}")

def print_error(message):
    """Prints an error message."""
    print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} {message}")

def download_file(url, dest, description="Downloading"):
    """Downloads a file from a URL with a progress bar."""
    try:
        print_info(f"{description}: {url}")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        total_size = int(response.headers.get('content-length', 0))
        with open(dest, 'wb') as file, tqdm(
            desc=description,
            total=total_size,
            unit='iB',
            unit_scale=True,
            unit_divisor=1024,
            bar_format='{l_bar}{bar} | {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]'
        ) as bar:
            for data in response.iter_content(chunk_size=1024):
                if data:
                    size = file.write(data)
                    bar.update(size)
        print_info(f"Downloaded: {dest}")
        return True
    except Exception as e:
        print_error(f"Failed to download {url}. Error: {e}")
        return False

def run_subprocess(command, shell=True):
    """Runs a subprocess command and returns True if successful, else False."""
    try:
        subprocess.run(command, shell=shell, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {command}")
        print_error(str(e))
        return False
    except Exception as e:
        print_error(f"An unexpected error occurred while running command: {command}")
        print_error(str(e))
        return False

def is_admin():
    """Checks if the script is running with administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Restarts the script with administrator privileges."""
    try:
        script = sys.argv[0]
        params = ' '.join([f'"{arg}"' for arg in sys.argv[1:]])
        if os.name == 'nt':
            # On Windows, use ShellExecuteW to run as admin in a new window
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{script}" {params}', None, 1)
        else:
            # For Unix-like systems
            subprocess.call(['sudo', sys.executable, script] + sys.argv[1:])
        # Attempt to close the old terminal
        try:
            os.kill(os.getppid(), signal.SIGTERM)
        except:
            pass
        sys.exit(0)
    except Exception as e:
        print_error(f"Failed to elevate privileges: {e}")
        sys.exit(1)

def check_hyperv():
    """Checks if Hyper-V is enabled on the system."""
    try:
        cmd = "systeminfo"
        output = subprocess.check_output(cmd, shell=True, universal_newlines=True)
        if "Hyper-V Requirements" in output:
            if "A hypervisor has been detected. Features required for Hyper-V will not be displayed." in output:
                # Hypervisor is running
                return True
        return False
    except Exception as e:
        print_error(f"Failed to check Hyper-V status. Error: {e}")
        return False

def disable_hyperv():
    """Disables Hyper-V and related features. Returns True if successful, else False."""
    try:
        print_info("Disabling Hyper-V and related features...")
        # List of features to disable
        features_to_disable = [
            "Microsoft-Hyper-V-All",
            "VirtualMachinePlatform",
            "Containers"  # Include only if you want to disable Containers
        ]
        
        for feature in features_to_disable:
            # Check if the feature exists and is enabled
            check_cmd = f'dism.exe /Online /Get-Feature /FeatureName:{feature}'
            result = subprocess.run(check_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if "State : Enabled" in result.stdout:
                print_info(f"Disabling feature: {feature}")
                disable_cmd = f'dism.exe /Online /Disable-Feature /FeatureName:{feature} /NoRestart'
                success = run_subprocess(disable_cmd)
                if not success:
                    print_error(f"Failed to disable feature: {feature}")
                    return False
            else:
                print_info(f"Feature '{feature}' is not enabled or does not exist. Skipping.")
        
        # Update boot configuration to prevent hypervisor from launching
        print_info("Updating boot configuration to prevent hypervisor from launching...")
        boot_cmd = "bcdedit /set hypervisorlaunchtype off"
        success = run_subprocess(boot_cmd)
        if not success:
            print_error("Failed to update boot configuration.")
            return False
        
        print_info("All specified Hyper-V related features have been disabled successfully.")
        return True
    except Exception as e:
        print_error(f"Failed to disable Hyper-V. Error: {e}")
        return False

def install_bluestacks(stats):
    """Handles the installation of BlueStacks."""
    clear_screen()
    print_banner()

    username = os.environ.get('USERNAME') or os.environ.get('USER')
    if not username:
        print_error("Could not retrieve the USERNAME environment variable.")
        sys.exit(1)

    current_dir = Path.cwd()
    downloads_dir = current_dir / "Downloads"
    installer_path = downloads_dir / "Bluestacks5Installer.exe"
    uninstaller_path = downloads_dir / "bsuninstaller.exe"

    # Create Downloads directory if it doesn't exist
    if not downloads_dir.exists():
        downloads_dir.mkdir(parents=True, exist_ok=True)
        print_info(f"Created Downloads directory: {downloads_dir}")
        stats['downloads_dir_created'] = True
    else:
        print_info(f"Using Downloads directory: {downloads_dir}")
        stats['downloads_dir_created'] = False

    # Change to Downloads directory
    os.chdir(downloads_dir)

    # URLs to download
    downloads = [
        {
            "url": "https://cdn3.bluestacks.com/downloads/windows/nxt/5.2.100.1047/6fd7ce7bdea5724b7561a06bc604ffbd/x64/BlueStacksFullInstaller_5.2.100.1047_amd64_native.exe",
            "dest": installer_path,
            "description": "Downloading BlueStacks Installer"
        },
        {
            "url": "https://cdn3.bluestacks.com/bluestacks-cleaner/v1.07/BstCleaner_native.exe",
            "dest": uninstaller_path,
            "description": "Downloading BlueStacks Cleaner"
        }
    ]

    # Download BlueStacks Installer and Cleaner
    for item in downloads:
        if not item["dest"].exists():
            success = download_file(item["url"], item["dest"], item["description"])
            if success:
                stats['files_downloaded'].append(str(item["dest"]))
            else:
                stats['files_failed'].append({
                    "url": item["url"],
                    "dest": str(item["dest"]),
                    "error": "Download failed"
                })
        else:
            print_info(f"Already exists: {item['dest']}")
            stats['files_already_exist'].append(str(item["dest"]))

    # Run BlueStacks Installer with specific options
    print_info("Installing BlueStacks...")
    installer_command = f'"{installer_path}" --defaultImageName Pie64 --imageToLaunch Pie64'
    success = run_subprocess(installer_command)
    if success:
        stats['bluestacks_installed'] = True
    else:
        stats['bluestacks_installed'] = False
        print_error("BlueStacks installation failed.")
        # Proceed based on your preference; here, we'll stop installation
        display_summary("Installation", stats)
        input("Press Enter to exit...")
        sys.exit(1)

    # Delete Promotions directory
    promotions_path = Path("C:/ProgramData/BlueStacks_nxt/Engine/Pie64/Promotions")
    if promotions_path.exists():
        try:
            shutil.rmtree(promotions_path)
            print_info("Deleted Promotions directory.")
            stats['promotions_deleted'] = True
        except Exception as e:
            print_error(f"Failed to delete Promotions directory. Error: {e}")
            stats['promotions_deleted'] = False
    else:
        print_warning("Promotions directory does not exist.")
        stats['promotions_deleted'] = False

    # Set permissions to deny write access
    try:
        icacls_command = f'icacls "{promotions_path}" /deny {username}:(W)'
        success = run_subprocess(icacls_command)
        if success:
            print_info("Set permissions to deny write access on Promotions directory.")
            stats['permissions_set'] = True
        else:
            print_error("Failed to set permissions on Promotions directory.")
            stats['permissions_set'] = False
    except Exception as e:
        print_error(f"Failed to set permissions. Error: {e}")
        stats['permissions_set'] = False

    # Move the uninstaller to BlueStacks installation directory
    dest_uninstaller = Path("C:/Program Files/BlueStacks_nxt") / "bsuninstaller.exe"
    try:
        if dest_uninstaller.exists():
            shutil.rmtree(dest_uninstaller.parent, ignore_errors=True)
        shutil.move(str(uninstaller_path), dest_uninstaller)
        print_info(f"Moved bsuninstaller.exe to {dest_uninstaller}")
        stats['uninstaller_moved'] = True
    except Exception as e:
        print_error(f"Failed to move bsuninstaller.exe. Error: {e}")
        stats['uninstaller_moved'] = False

    # Display Installation Summary
    display_summary("Installation", stats)

    input("Press Enter to exit...")

def uninstall_bluestacks(stats):
    """Handles the uninstallation of BlueStacks."""
    clear_screen()
    print_banner()

    uninstaller_path = Path("C:/Program Files/BlueStacks_nxt/bsuninstaller.exe")

    if not uninstaller_path.exists():
        print_error(f"Uninstaller not found at {uninstaller_path}. BlueStacks may not be installed.")
        stats['uninstaller_found'] = False
        display_summary("Uninstallation", stats)
        input("Press Enter to exit...")
        sys.exit(1)

    print_info("Starting BlueStacks uninstallation...")
    try:
        success = run_subprocess([str(uninstaller_path)])
        if success:
            print_info("BlueStacks has been uninstalled successfully.")
            stats['bluestacks_uninstalled'] = True
        else:
            print_error("BlueStacks uninstallation failed.")
            stats['bluestacks_uninstalled'] = False
    except Exception as e:
        print_error(f"Uninstallation failed. Error: {e}")
        stats['bluestacks_uninstalled'] = False

    # Display Uninstallation Summary
    display_summary("Uninstallation", stats)

    input("Press Enter to exit...")

def display_summary(action, stats):
    """Displays a summary of the actions performed."""
    clear_screen()
    print_banner()
    print_info(f"{action} Summary:")
    print("=" * 50)
    if action == "Installation":
        print(f"{Fore.GREEN}Downloads Directory Created:{Style.RESET_ALL} {'Yes' if stats.get('downloads_dir_created') else 'No'}")
        print(f"{Fore.GREEN}Files Downloaded:{Style.RESET_ALL}")
        for file in stats.get('files_downloaded', []):
            print(f"  - {file}")
        print(f"{Fore.GREEN}Files Already Exist:{Style.RESET_ALL}")
        for file in stats.get('files_already_exist', []):
            print(f"  - {file}")
        if stats.get('files_failed'):
            print(f"{Fore.RED}Files Failed to Download:{Style.RESET_ALL}")
            for fail in stats.get('files_failed', []):
                print(f"  - URL: {fail['url']}")
                print(f"    Destination: {fail['dest']}")
                print(f"    Error: {fail['error']}")
        print(f"{Fore.GREEN}BlueStacks Installed:{Style.RESET_ALL} {'Yes' if stats.get('bluestacks_installed') else 'No'}")
        print(f"{Fore.GREEN}Promotions Directory Deleted:{Style.RESET_ALL} {'Yes' if stats.get('promotions_deleted') else 'No'}")
        print(f"{Fore.GREEN}Permissions Set:{Style.RESET_ALL} {'Yes' if stats.get('permissions_set') else 'No'}")
        print(f"{Fore.GREEN}Uninstaller Moved:{Style.RESET_ALL} {'Yes' if stats.get('uninstaller_moved') else 'No'}")
    elif action == "Uninstallation":
        print(f"{Fore.GREEN}BlueStacks Uninstalled:{Style.RESET_ALL} {'Yes' if stats.get('bluestacks_uninstalled') else 'No'}")
        print(f"{Fore.GREEN}Uninstaller Found:{Style.RESET_ALL} {'Yes' if stats.get('uninstaller_found') else 'No'}")
    print("=" * 50)

def main_menu():
    """Displays the main menu and handles user selection."""
    while True:
        clear_screen()
        print_banner()
        try:
            choice = inquirer.select(
                message="Please select an option:",
                choices=[
                    "Install BlueStacks 5",
                    "Uninstall BlueStacks 5",
                    "Exit"
                ],
                default="Install BlueStacks 5"
            ).execute()
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            sys.exit(0)

        if choice == "Install BlueStacks 5":
            # Check Hyper-V
            hyperv_enabled = check_hyperv()
            if hyperv_enabled:
                print_warning("Hyper-V is currently enabled on your system.")
                proceed = inquirer.confirm(
                    message="Disabling Hyper-V is required to install this version of BlueStacks.\nDo you want to disable Hyper-V now?",
                    default=True
                ).execute()
                if proceed:
                    success = disable_hyperv()
                    if success:
                        # Prompt to restart now or later
                        restart = inquirer.select(
                            message="Do you want to restart your computer now to apply the changes?",
                            choices=["Yes", "No"],
                            default="Yes"
                        ).execute()
                        if restart == "Yes":
                            print_info("Restarting the computer...")
                            os.system("shutdown /r /t 0")
                            sys.exit(0)
                        else:
                            print_warning("Please restart your computer manually for changes to take effect.")
                            print_warning("Installation will be paused until the system is restarted.")
                            input("Press Enter to return to the main menu...")
                            continue  # Return to main menu
                    else:
                        print_error("Failed to disable Hyper-V. Installation cannot proceed.")
                        print_warning("Please ensure you run the script with administrative privileges.")
                        input("Press Enter to return to the main menu...")
                        continue  # Return to main menu
                else:
                    print_warning("Installation canceled because Hyper-V needs to be disabled.")
                    input("Press Enter to return to the main menu...")
                    continue  # Return to main menu
            else:
                # Proceed with installation
                stats = {
                    'downloads_dir_created': False,
                    'files_downloaded': [],
                    'files_already_exist': [],
                    'files_failed': [],
                    'bluestacks_installed': False,
                    'promotions_deleted': False,
                    'permissions_set': False,
                    'uninstaller_moved': False
                }
                install_bluestacks(stats)
        elif choice == "Uninstall BlueStacks 5":
            if not is_admin():
                proceed = inquirer.confirm(
                    message="It's recommended to run this script as an administrator for proper uninstallation.\nDo you want to restart the script with administrative privileges?",
                    default=True
                ).execute()
                if proceed:
                    run_as_admin()
                else:
                    print_warning("Proceeding without administrative privileges may cause uninstallation issues.")
                    input("Press Enter to return to the main menu...")
                    continue  # Return to main menu
            else:
                stats = {
                    'bluestacks_uninstalled': False,
                    'uninstaller_found': True
                }
                uninstall_bluestacks(stats)
        elif choice == "Exit":
            print_info("Exiting the installer. Goodbye!")
            sys.exit(0)
        else:
            print_warning("Invalid choice. Please select a valid option.")
            time.sleep(2)

if __name__ == "__main__":
    if not is_admin():
        print_warning("Administrator privileges are required for installation.")
        proceed = inquirer.confirm(
            message="Do you want to restart the script with administrative privileges?",
            default=True
        ).execute()
        if proceed:
            run_as_admin()
        else:
            print_warning("Proceeding without administrative privileges will cause installation to fail.")
            input("Press Enter to exit...")
            sys.exit(1)
    else:
        main_menu()
