#!/usr/bin/env python
"""
Build script for creating an executable from the Python application.
"""

import os
import sys
import subprocess
import shutil
import platform

def main():
    """Main build function."""
    print("Building CBZ to PDF Converter executable...")
    
    # Ensure we're in the project root directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    
    # Create the icon if it doesn't exist
    icon_path = os.path.join(project_root, "python_app", "ui", "icon.ico")
    if not os.path.exists(icon_path):
        try:
            print("Generating icon...")
            sys.path.append(os.path.join(project_root, "python_app", "ui"))
            from icon import generate_icon
            icon_path = generate_icon()
            print(f"Icon generated at: {icon_path}")
        except Exception as e:
            print(f"Warning: Could not generate icon: {e}")
            icon_path = None
    
    # Build the executable
    try:
        print("Building executable with PyInstaller...")
        
        # 确保必要的依赖项
        hidden_imports = [
            "PyPDF2",
            "PIL",
            "PIL._tkinter_finder",
            "PIL._imagingtk",
            "rarfile",
            "tqdm",
            "tkinter",
            "tkinter.filedialog",
            "tkinter.ttk",
            "tkinter.messagebox"
        ]
        
        hidden_imports_str = ",".join(hidden_imports)
        
        # Determine the appropriate command based on the platform
        if platform.system() == "Windows":
            cmd = [
                "pyinstaller",
                "--onefile",
                "--windowed",
                "--name", "CBZtoPDFConverter",
                "--add-data", f"{os.path.join('python_app', 'ui', 'icon.ico')};ui",
                "--hidden-import", hidden_imports_str,
                "--collect-all", "PyPDF2",
                "--collect-all", "PIL",
                "--collect-all", "rarfile",
                "--icon", icon_path if icon_path else "",
                "--log-level", "DEBUG",
                os.path.join("python_app", "main.py")
            ]
        else:  # macOS or Linux
            cmd = [
                "pyinstaller",
                "--onefile",
                "--windowed",
                "--name", "CBZtoPDFConverter",
                "--add-data", f"{os.path.join('python_app', 'ui', 'icon.ico')}:ui",
                "--hidden-import", hidden_imports_str,
                "--collect-all", "PyPDF2",
                "--collect-all", "PIL",
                "--collect-all", "rarfile",
                "--icon", icon_path if icon_path else "",
                "--log-level", "DEBUG",
                os.path.join("python_app", "main.py")
            ]
        
        # Remove empty icon parameter if no icon
        if not icon_path:
            cmd.remove("--icon")
            cmd.remove("")
        
        # 创建spec文件
        print("Creating spec file...")
        spec_cmd = [
            "pyi-makespec",
            "--onefile",
            "--windowed",
            "--name", "CBZtoPDFConverter",
            "--hidden-import", hidden_imports_str,
            "--collect-all", "PyPDF2",
            "--collect-all", "PIL",
            "--collect-all", "rarfile",
            os.path.join("python_app", "main.py")
        ]
        
        subprocess.run(spec_cmd, check=True)
        
        # 修改spec文件以添加更多配置
        spec_file = "CBZtoPDFConverter.spec"
        with open(spec_file, 'r') as f:
            spec_content = f.read()
        
        # 添加datas配置
        spec_content = spec_content.replace(
            "datas=[]",
            "datas=[('" + os.path.join('python_app', 'ui', 'icon.ico').replace('\\', '\\\\') + "', 'ui')]"
        )
        
        with open(spec_file, 'w') as f:
            f.write(spec_content)
        
        print("Building from spec file...")
        build_cmd = ["pyinstaller", "--clean", spec_file]
        subprocess.run(build_cmd, check=True)
        
        print("Executable built successfully!")
        print(f"You can find it in the 'dist' directory: {os.path.join(project_root, 'dist')}")
        
    except subprocess.CalledProcessError as e:
        print(f"Error building executable: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 