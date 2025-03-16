import os
import sys
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from threading import Thread
import logging
import traceback
from converter import CBZtoPDFConverter, batch_convert

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加文件处理程序，确保日志也写入文件
try:
    file_handler = logging.FileHandler('cbz2pdf_app.log')
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
except Exception as e:
    print(f"无法设置日志文件: {e}")

class CBZtoPDFApp:
    """
    GUI application for converting CBZ files to PDF.
    """
    
    def __init__(self, root):
        """Initialize the application."""
        self.root = root
        self.root.title("CBZ to PDF Converter")
        self.root.geometry("600x500")
        self.root.minsize(600, 500)
        
        # Set icon if available
        try:
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                application_path = sys._MEIPASS
            else:
                # Running as script
                application_path = os.path.dirname(os.path.abspath(__file__))
            
            icon_path = os.path.join(application_path, "ui", "icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except Exception as e:
            logger.warning(f"Could not set icon: {e}")
        
        # Variables
        self.input_files = []
        self.output_directory = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready")
        self.progress_var = tk.DoubleVar(value=0)
        self.is_converting = False
        
        # Create UI
        self._create_ui()
    
    def _create_ui(self):
        """Create the user interface."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="CBZ to PDF Converter", font=("Helvetica", 16, "bold"))
        title_label.pack(pady=10)
        
        # Input files frame
        input_frame = ttk.LabelFrame(main_frame, text="Input Files", padding="10")
        input_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Files listbox with scrollbar
        files_frame = ttk.Frame(input_frame)
        files_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(files_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.files_listbox = tk.Listbox(files_frame, selectmode=tk.EXTENDED, yscrollcommand=scrollbar.set)
        self.files_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=self.files_listbox.yview)
        
        # Buttons for file selection
        files_button_frame = ttk.Frame(input_frame)
        files_button_frame.pack(fill=tk.X, pady=5)
        
        add_button = ttk.Button(files_button_frame, text="Add Files", command=self._add_files)
        add_button.pack(side=tk.LEFT, padx=5)
        
        remove_button = ttk.Button(files_button_frame, text="Remove Selected", command=self._remove_selected)
        remove_button.pack(side=tk.LEFT, padx=5)
        
        clear_button = ttk.Button(files_button_frame, text="Clear All", command=self._clear_files)
        clear_button.pack(side=tk.LEFT, padx=5)
        
        # Output directory frame
        output_frame = ttk.LabelFrame(main_frame, text="Output Directory", padding="10")
        output_frame.pack(fill=tk.X, pady=5)
        
        output_entry = ttk.Entry(output_frame, textvariable=self.output_directory)
        output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        browse_button = ttk.Button(output_frame, text="Browse", command=self._browse_output)
        browse_button.pack(side=tk.RIGHT, padx=5)
        
        # Convert button
        convert_button = ttk.Button(main_frame, text="Convert", command=self._start_conversion)
        convert_button.pack(pady=10)
        
        # Progress bar
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=5)
        
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, padx=5)
        
        # Status label
        status_label = ttk.Label(main_frame, textvariable=self.status_var)
        status_label.pack(pady=5)
        
        # Version and credits
        version_label = ttk.Label(main_frame, text="v1.0.0", foreground="gray")
        version_label.pack(side=tk.RIGHT, padx=5, pady=5)
    
    def _add_files(self):
        """Add files to the list."""
        filetypes = [
            ("Comic Book Archives", "*.cbz *.cbr"),
            ("CBZ Files", "*.cbz"),
            ("CBR Files", "*.cbr"),
            ("All Files", "*.*")
        ]
        
        files = filedialog.askopenfilenames(
            title="Select CBZ/CBR Files",
            filetypes=filetypes
        )
        
        if files:
            for file in files:
                if file not in self.input_files:
                    self.input_files.append(file)
                    self.files_listbox.insert(tk.END, os.path.basename(file))
            
            self.status_var.set(f"{len(self.input_files)} files selected")
    
    def _remove_selected(self):
        """Remove selected files from the list."""
        selected_indices = self.files_listbox.curselection()
        
        if not selected_indices:
            return
        
        # Remove in reverse order to avoid index shifting
        for index in sorted(selected_indices, reverse=True):
            del self.input_files[index]
            self.files_listbox.delete(index)
        
        self.status_var.set(f"{len(self.input_files)} files selected")
    
    def _clear_files(self):
        """Clear all files from the list."""
        self.input_files = []
        self.files_listbox.delete(0, tk.END)
        self.status_var.set("Ready")
    
    def _browse_output(self):
        """Browse for output directory."""
        directory = filedialog.askdirectory(title="Select Output Directory")
        
        if directory:
            self.output_directory.set(directory)
    
    def _start_conversion(self):
        """Start the conversion process."""
        if not self.input_files:
            messagebox.showwarning("No Files", "Please select at least one file to convert.")
            return
        
        if self.is_converting:
            messagebox.showwarning("In Progress", "Conversion is already in progress.")
            return
        
        # Get output directory
        output_dir = self.output_directory.get()
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
                logger.info(f"创建输出目录: {output_dir}")
            except Exception as e:
                logger.error(f"无法创建输出目录: {e}")
                messagebox.showerror("Error", f"Could not create output directory: {e}")
                return
        
        # Start conversion in a separate thread
        self.is_converting = True
        logger.info(f"开始转换 {len(self.input_files)} 个文件")
        self.progress_var.set(0)
        conversion_thread = Thread(target=self._run_conversion, args=(output_dir,))
        conversion_thread.daemon = True
        conversion_thread.start()
    
    def _run_conversion(self, output_dir):
        """Run the conversion process in a separate thread."""
        try:
            total_files = len(self.input_files)
            successful = 0
            failed = 0
            
            logger.info(f"开始批量转换，共 {total_files} 个文件")
            
            for i, input_file in enumerate(self.input_files):
                # Update status
                file_name = os.path.basename(input_file)
                status_msg = f"Converting {file_name} ({i+1}/{total_files})"
                logger.info(status_msg)
                self.status_var.set(status_msg)
                
                # Convert file
                try:
                    converter = CBZtoPDFConverter()
                    
                    if output_dir:
                        output_file = os.path.join(output_dir, os.path.splitext(file_name)[0] + '.pdf')
                    else:
                        output_file = os.path.splitext(input_file)[0] + '.pdf'
                    
                    logger.info(f"转换文件: {input_file} -> {output_file}")
                    success = converter.convert(input_file, output_file)
                    
                    if success:
                        logger.info(f"文件 {file_name} 转换成功")
                        successful += 1
                    else:
                        logger.error(f"文件 {file_name} 转换失败")
                        failed += 1
                except Exception as e:
                    logger.error(f"处理文件 {file_name} 时出错: {e}")
                    logger.error(traceback.format_exc())
                    failed += 1
                
                # Update progress
                progress = ((i + 1) / total_files) * 100
                self.progress_var.set(progress)
            
            # Show completion message
            completion_msg = f"Converted {successful} of {total_files} files successfully."
            if failed > 0:
                completion_msg += f" {failed} files failed."
            
            logger.info(f"转换完成: {successful} 成功, {failed} 失败")
            self.root.after(0, lambda: messagebox.showinfo("Conversion Complete", completion_msg))
            self.status_var.set(f"Completed: {successful}/{total_files} successful")
        
        except Exception as e:
            error_msg = f"An error occurred during conversion: {e}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
            self.status_var.set("Error occurred")
        
        finally:
            self.is_converting = False
            logger.info("转换线程结束")

def main():
    """Main entry point for the application."""
    try:
        logger.info("启动应用程序")
        root = tk.Tk()
        app = CBZtoPDFApp(root)
        root.mainloop()
        logger.info("应用程序关闭")
    except Exception as e:
        logger.critical(f"应用程序崩溃: {e}")
        logger.critical(traceback.format_exc())
        messagebox.showerror("Critical Error", f"Application crashed: {e}\nSee log file for details.")

if __name__ == "__main__":
    main() 