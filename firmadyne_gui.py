import os
import sys
import subprocess
import pexpect
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from pathlib import Path
import threading
import queue

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
except ImportError:
    messagebox.showerror("Error", "Please install tkinterdnd2: pip install tkinterdnd2")
    sys.exit(1)

class FirmadyneGUI:
    def _init_(self, root):
        self.root = root
        self.root.title("Firmadyne Firmware Analyzer")
        self.root.geometry("600x400")
       
        self.firmadyne_path = os.path.dirname(os.path.abspath(_file_))
        self.output_dir = os.path.join(self.firmadyne_path, "images")
        self.sudo_password = None
        self.db_password = None
        self.analysis_window = None
        self.emulation_process = None
        self.terminal_text = None

        self.command_history = []
        self.history_position = 0
        self.current_input = ""
        self.stop_thread = False
        self.output_queue = queue.Queue()
       
        self._create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._check_firmadyne_structure()

    def _check_firmadyne_structure(self):
        """Verify required directories exist"""
        required = ["sources/extractor", "scripts", "images"]
        missing = [d for d in required if not os.path.exists(os.path.join(self.firmadyne_path, d))]
        if missing:
            messagebox.showerror("Error", f"Missing directories:\n{', '.join(missing)}")
            self.root.destroy()
            sys.exit(1)

    def _stop_emulation(self):
        if self.emulation_process and self.emulation_process.poll() is None:
            try:
                self.emulation_process.terminate()
                self.emulation_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.emulation_process.kill()
            finally:
                try:
                    self.emulation_process.stdin.close()
                except:
                    pass
                self.emulation_process = None

        if hasattr(self, 'terminal_text') and self.terminal_text:
            self.terminal_text.insert(tk.END, "\n[Emulation stopped]\n")
            self.terminal_text.see(tk.END)

    def _on_close(self):
        # Try to gracefully shut down the shell process
        if hasattr(self, 'shell_process') and self.shell_process:
            try:
                self.shell_process.terminate()
                self.shell_process.wait(timeout=2)
            except Exception:
                self.shell_process.kill()
        
        self.root.destroy()

    def _on_enter_terminal(self, event):
        if not hasattr(self, 'emulator_text') or not self.emulator_text:
            return
            
        command = self.emulator_text.get("insert linestart", "insert lineend").strip()
        if command:
            try:
                if self.emulation_process and self.emulation_process.stdin:
                    self.emulation_process.stdin.write(command + '\n')
                    self.emulation_process.stdin.flush()

                if hasattr(self, 'terminal_text') and self.terminal_text:
                    self.terminal_text.insert(tk.END, command + '\n')
                    self.terminal_text.see(tk.END)
            except Exception as e:
                if hasattr(self, 'terminal_text') and self.terminal_text:
                    self.terminal_text.insert(tk.END, f"\n[Error]: {e}\n")
                    self.terminal_text.see(tk.END)

        return "break"

    def _create_widgets(self):
        """Setup GUI components"""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
       
        # Drag and drop area
        self.drop_label = tk.Label(main_frame,
                                 text="Drag Firmware Here\n(or click to browse)",
                                 relief=tk.RAISED,
                                 padx=20, pady=20,
                                 background="lightgray")
        self.drop_label.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        self.drop_label.drop_target_register(DND_FILES)
        self.drop_label.dnd_bind('<<Drop>>', self._on_drop)
        self.drop_label.bind("<Button-1>", self._browse_file)
       
        # Options
        options_frame = ttk.Frame(main_frame)
        options_frame.pack(fill=tk.X, pady=(0, 10))
       
        ttk.Label(options_frame, text="Brand:").pack(side=tk.LEFT, padx=(0, 5))
        self.brand_var = tk.StringVar(value="Netgear")
        ttk.Entry(options_frame, textvariable=self.brand_var, width=20).pack(side=tk.LEFT)
       
        ttk.Label(options_frame, text="SQL Host:").pack(side=tk.LEFT, padx=(10, 5))
        self.sql_host_var = tk.StringVar(value="127.0.0.1")
        ttk.Entry(options_frame, textvariable=self.sql_host_var, width=15).pack(side=tk.LEFT)
       
        # Analyze button
        self.analyze_button = ttk.Button(
            main_frame,
            text="Analyze Firmware",
            command=self._analyze_firmware,
            state=tk.DISABLED
        )
        self.analyze_button.pack(pady=(0, 10))
       
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN).pack(fill=tk.X, side=tk.BOTTOM)
       
        self.firmware_path = None

    def _create_analysis_window(self):
        """Create the analysis results window with tabs"""
        if self.analysis_window and self.analysis_window.winfo_exists():
            self.analysis_window.lift()
            return
            
        self.analysis_window = tk.Toplevel(self.root)
        self.analysis_window.title("Analysis Results")
        self.analysis_window.geometry("1000x700")
        self.analysis_window.protocol("WM_DELETE_WINDOW", self._on_analysis_window_close)

        # Main paned window
        main_paned = ttk.PanedWindow(self.analysis_window, orient=tk.VERTICAL)
        main_paned.pack(fill=tk.BOTH, expand=True)

        # Notebook for tabs
        notebook_frame = ttk.Frame(main_paned)
        main_paned.add(notebook_frame, weight=3)

        self.notebook = ttk.Notebook(notebook_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Create tabs
        self.emulation_tab = ttk.Frame(self.notebook)
        self.snmp_tab = ttk.Frame(self.notebook)
        self.web_tab = ttk.Frame(self.notebook)
        self.nmap_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.emulation_tab, text="Emulation")
        self.notebook.add(self.snmp_tab, text="SNMP")
        self.notebook.add(self.web_tab, text="Web Access")
        self.notebook.add(self.nmap_tab, text="NMAP")

        # Create output widgets for each tab
        self.emulation_output = self._create_output_widget(self.emulation_tab)
        self.snmp_output = self._create_output_widget(self.snmp_tab)
        self.web_output = self._create_output_widget(self.web_tab)
        self.nmap_output = self._create_output_widget(self.nmap_tab)

        # Terminal frame
        terminal_frame = ttk.Frame(main_paned)
        main_paned.add(terminal_frame, weight=1)

        # Start bash subprocess
        self.proc = subprocess.Popen(
            ["/bin/bash"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        self.output_queue = queue.Queue()
        self.stop_thread = False

        # Start reading bash output in a separate thread
        self.read_thread = threading.Thread(target=self._read_output, daemon=True)
        self.read_thread.start()

        # Schedule periodic output checks in GUI
        self._check_output()

        # Terminal text widget with initial content
        self.terminal_text = tk.Text(
            terminal_frame,
            wrap=tk.WORD,
            bg='black',
            fg='white',
            insertbackground='white',
            font=('Consolas', 10)
        )
        terminal_scroll = ttk.Scrollbar(terminal_frame, command=self.terminal_text.yview)
        self.terminal_text.config(yscrollcommand=terminal_scroll.set)

        # Add initial terminal content
        self.terminal_text.insert(tk.END, "")  # or insert a welcome message
        self.terminal_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        terminal_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Terminal control buttons
        term_button_frame = ttk.Frame(terminal_frame)
        term_button_frame.pack(fill=tk.X, padx=10, pady=5)

        stop_button = ttk.Button(
            term_button_frame,
            text="Stop Emulation",
            command=self._stop_emulation
        )
        stop_button.pack(side=tk.LEFT, padx=5)

        clear_button = ttk.Button(
            term_button_frame,
            text="Clear Terminal",
            command=lambda: self.terminal_text.delete(1.0, tk.END)
        )
        clear_button.pack(side=tk.LEFT, padx=5)

        # Terminal input with command prompt
        input_frame = ttk.Frame(term_button_frame)
        input_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        ttk.Label(input_frame, text="firmadync>", foreground="green").pack(side=tk.LEFT)
        
        self.terminal_input = ttk.Entry(input_frame)
        self.terminal_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.terminal_input.bind("<Return>", self._send_terminal_input)
    
    def _read_output(self):
        for line in self.proc.stdout:
            if self.stop_thread:
                break
            self.output_queue.put(line)
    
    def _check_output(self):
        try:
            while True:
                line = self.output_queue.get_nowait()
                if hasattr(self, 'terminal_text') and self.terminal_text:
                    self.terminal_text.insert(tk.END, line)
                    self.terminal_text.see(tk.END)
        except queue.Empty:
            pass
        if hasattr(self, 'terminal_text') and self.terminal_text:
            self.terminal_text.after(100, self._check_output)

    def _create_output_widget(self, parent):
        """Helper to create output widgets for tabs"""
        frame = tk.Frame(parent)
        scroll = tk.Scrollbar(frame)
        text = tk.Text(frame, wrap=tk.WORD, yscrollcommand=scroll.set)
        scroll.config(command=text.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        frame.pack(fill=tk.BOTH, expand=True)
        return text

    def _send_terminal_input(self, event=None):
        """Handle terminal input"""
        if not hasattr(self, 'terminal_input') or not self.terminal_input:
            return
            
        user_input = self.terminal_input.get()
        if not user_input:
            return
            
        # Add the prompt and command to the terminal output
        if hasattr(self, 'terminal_text') and self.terminal_text:
            self.terminal_text.insert(tk.END, f"firmadync> {user_input}\n")
            
            if user_input.lower() == 'exit':
                self._stop_emulation()
            elif user_input.lower() == 'clear':
                self.terminal_text.delete(1.0, tk.END)
            elif hasattr(self, 'emulation_process') and self.emulation_process and self.emulation_process.poll() is None:
                try:
                    if self.emulation_process.stdin:
                        self.emulation_process.stdin.write(user_input + "\n")
                        self.emulation_process.stdin.flush()
                except Exception as e:
                    self.terminal_text.insert(tk.END, f"[Error]: {e}\n")
            
            self.terminal_input.delete(0, tk.END)
            self.terminal_text.see(tk.END)

    def _on_analysis_window_close(self):
        """Handle analysis window close"""
        if messagebox.askokcancel("Quit", "Stop emulation and close this window?"):
            self._stop_emulation()
            if self.analysis_window and self.analysis_window.winfo_exists():
                self.analysis_window.destroy()
            self.analysis_window = None

    def _browse_file(self, event=None):
        """Handle file browsing"""
        if file_path := filedialog.askopenfilename(title="Select Firmware", filetypes=[("ZIP files", "*.zip")]):
            self._process_file(file_path)
   
    def _on_drop(self, event):
        """Handle file drop"""
        if file_path := event.data.strip('{}'):
            self._process_file(file_path)
   
    def _process_file(self, file_path):
        """Validate and set selected file"""
        if not file_path.lower().endswith('.zip'):
            messagebox.showerror("Error", "Please select a ZIP file")
            return
        if not os.path.exists(file_path):
            messagebox.showerror("Error", "File does not exist")
            return
       
        self.firmware_path = file_path
        self.drop_label.config(text=f"Selected:\n{os.path.basename(file_path)}", background="lightgreen")
        self.analyze_button.config(state=tk.NORMAL)
   
    def _get_newest_image(self):
        """Find most recently created image file"""
        images = list(Path(self.output_dir).glob("*.tar.gz"))
        return max(images, key=os.path.getmtime) if images else None
   
    def _get_image_number(self, image_path):
        """Extract just the numeric ID from image filename"""
        return os.path.basename(image_path).split('.')[0]
   
    def _analyze_firmware(self):
        """Run full analysis workflow"""
        if not self.firmware_path:
            messagebox.showerror("Error", "No firmware selected")
            return
       
        try:
            # Get sudo password if needed
            if self.sudo_password is None:
                self.sudo_password = simpledialog.askstring(
                    "Sudo Password", "Enter sudo password:", show='*', parent=self.root
                )
                if not self.sudo_password:
                    return
           
            # Run extractor
            self.status_var.set("Extracting firmware...")
            self.root.update()
           
            extractor_path = os.path.join(self.firmadyne_path, "sources/extractor/extractor.py")
            cmd = [
                "sudo", "-S", "python3", extractor_path,
                "-b", self.brand_var.get(),
                "-sql", self.sql_host_var.get(),
                "-np", "-nk",
                self.firmware_path,
                "images"
            ]
           
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.firmadyne_path,
                text=True
            )
            stdout, stderr = process.communicate(f"{self.sudo_password}\n")
            if "sudo: a password is required" in stderr:
                messagebox.showerror("Error", "Incorrect sudo password")
                self.sudo_password = None
                return
            if process.returncode != 0:
                raise Exception(stderr)
           
            # Get the new image
            if not (image_path := self._get_newest_image()):
                raise Exception("No image file created")
           
            # Get database password if needed
            if self.db_password is None:
                self.db_password = simpledialog.askstring(
                    "Database Password", "Enter Firmadyne database password:",
                    show='*', parent=self.root
                )
                if not self.db_password:
                    return
            env = os.environ.copy()
            env["PGPASSWORD"] = self.db_password
           
            # Analyze architecture
            self.status_var.set("Getting architecture...")
            self.root.update()
           
            # Create a temporary script that includes the password
            temp_script = os.path.join(self.firmadyne_path, "temp_getarch.sh")
            with open(temp_script, "w") as f:
                f.write(f"""#!/bin/bash
export PGPASSWORD='{self.db_password}'
{os.path.join(self.firmadyne_path, 'scripts/getArch.sh')} "$@"
""")
            os.chmod(temp_script, 0o755)
           
            try:
                result = subprocess.run(
                    ["bash", temp_script, str(image_path)],
                    capture_output=True,
                    text=True,
                    cwd=self.firmadyne_path
                )
               
                if result.returncode != 0:
                    raise Exception(result.stderr)
               
                # Show results
                messagebox.showinfo(
                    "Analysis Complete",
                    f"Image: {image_path.name}\nArchitecture: {result.stdout.strip()}"
                )
                self.status_var.set("Done")
               
                # After architecture detection succeeds:
                image_name = self._get_image_number(image_path)
               
                # Load filesystem into database
                self.status_var.set("Loading filesystem into DB...")
                self.root.update()
               
                tar2db_cmd = [
                    "python3",
                    os.path.join(self.firmadyne_path, "scripts/tar2db.py"),
                    "-i", image_name,
                    "-f", str(image_path)
                ]
                tar2db_result = subprocess.run(
                    tar2db_cmd,
                    capture_output=True,
                    text=True,
                    cwd=self.firmadyne_path
                )
               
                if tar2db_result.returncode != 0:
                    if "duplicate key value violates unique constraint" in tar2db_result.stderr:
                        duplicate_info = ""
                        if "DETAIL:" in tar2db_result.stderr:
                            duplicate_info = "\n" + tar2db_result.stderr.split("DETAIL:")[1].strip()
                       
                        response = messagebox.askyesno(
                            "Duplicate Firmware Detected",
                            f"This firmware appears to already exist in the database.{duplicate_info}\n\n"
                            "Do you want to continue with disk creation and emulation using the existing database entries?",
                            parent=self.root
                        )
                       
                        if not response:
                            raise Exception("Operation cancelled by user")
                    else:
                        raise Exception(f"Failed to load filesystem to DB:\n{tar2db_result.stderr}")
               
                # Create QEMU disk image
                self.status_var.set("Creating QEMU image...")
                self.root.update()
                command = f'./scripts/makeImage.sh {image_name}'
                full_command = f'echo {self.sudo_password} | sudo -SE bash -c "{command}"'
                subprocess.run(full_command, shell=True, env=env, capture_output=True, text=True)

                # Infer network configuration
                self.status_var.set("Inferring network config...")
                self.root.update()
                command2 = f'./scripts/inferNetwork.sh {image_name}'
                full_command2 = f'echo {self.sudo_password} | sudo -SE bash -c "{command2}"'
                subprocess.run(full_command2, shell=True, env=env, capture_output=True, text=True)

                # Start emulation and analyses
                self.status_var.set("Starting emulation and analyses...")
                self.root.update()

                run_script_path = os.path.join(self.firmadyne_path, f"scratch/{image_name}/run.sh")
                if not os.path.exists(run_script_path):
                    raise Exception("Run script not found")

                # Create analysis window if it doesn't exist
                self._create_analysis_window()

                # Run analyses
                self._run_analyses(image_name, run_script_path)
               
            finally:
                if os.path.exists(temp_script):
                    os.remove(temp_script)
           
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.status_var.set("Failed")
        finally:
            self.analyze_button.config(state=tk.DISABLED)
            self.drop_label.config(
                text="Drag Firmware Here\n(or click to browse)",
                background="lightgray"
            )
            self.firmware_path = None

    def _run_analyses(self, image_name, run_script_path):
        """Run all analysis processes"""
        ip_address = "192.168.0.100"  # Make this configurable if needed
        log_file = os.path.join(self.firmadyne_path, f"scratch/{image_name}/analyses.log")

        def display_snmp_files():
            """Display contents of SNMP files in the SNMP tab"""
            if not hasattr(self, 'snmp_output') or not self.snmp_output:
                return

            snmp_files = {
                "Public": "snmp.public.txt",
                "Private": "snmp.private.txt"
            }

            for file_type, filename in snmp_files.items():
                file_path = os.path.join(self.firmadyne_path, filename)
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r') as f:
                            content = f.read()
                            self.snmp_output.insert(tk.END, f"\n=== {file_type} SNMP Results ===\n")
                            self.snmp_output.insert(tk.END, content)
                            self.snmp_output.insert(tk.END, "\n" + "="*50 + "\n")
                            self.snmp_output.see(tk.END)
                    except Exception as e:
                        if hasattr(self, 'terminal_text') and self.terminal_text:
                            self.terminal_text.insert(tk.END, f"[Error reading {filename}]: {e}\n")

        # Function to update output widgets
        def update_output(process, output_widget, process_name=""):
            if not process or not output_widget:
                return
            try:
                while True:
                    line = process.stdout.readline()
                    if not line:
                        break
                    if process_name:
                        line = f"[{process_name}] {line}"
                    output_widget.insert(tk.END, line)
                    output_widget.see(tk.END)
                    output_widget.update_idletasks()
            except Exception as e:
                if hasattr(self, 'terminal_text') and self.terminal_text:
                    self.terminal_text.insert(tk.END, f"[Error in {process_name} thread]: {e}\n")
            finally:
                try:
                    process.stdout.close()
                except:
                    pass

        # Run emulation first
        try:
            if hasattr(self, 'terminal_text') and self.terminal_text:
                self.terminal_text.insert(tk.END, "[Starting emulation...]\n")
            
            self.emulation_process = subprocess.Popen(
                [run_script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True
            )
            
            if hasattr(self, 'emulation_output') and self.emulation_output:
                threading.Thread(
                    target=update_output,
                    args=(self.emulation_process, self.emulation_output, "Emulation"),
                    daemon=True
                ).start()
            
            # Wait for emulation to stabilize
            if hasattr(self, 'terminal_text') and self.terminal_text:
                self.terminal_text.insert(tk.END, "[Waiting for emulation to stabilize...]\n")
            
            # Wait longer for emulation to fully stabilize
            time.sleep(60)  # Increased to 60 seconds
            
            # Check if emulation is still running
            if self.emulation_process.poll() is not None:
                raise Exception("Emulation process terminated unexpectedly")
            
            if hasattr(self, 'terminal_text') and self.terminal_text:
                self.terminal_text.insert(tk.END, "[Emulation stabilized, starting SNMP analysis...]\n")
            
        except Exception as e:
            if hasattr(self, 'terminal_text') and self.terminal_text:
                self.terminal_text.insert(tk.END, f"[Error starting emulation]: {e}\n")
            return

        # Run SNMP analysis after emulation is stable
        try:
            snmp_process = subprocess.Popen(
                [os.path.join(self.firmadyne_path, "analyses/snmpwalk.sh"), ip_address],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            if hasattr(self, 'snmp_output') and self.snmp_output:
                threading.Thread(
                    target=update_output,
                    args=(snmp_process, self.snmp_output, "SNMP"),
                    daemon=True
                ).start()
            
            # Wait for SNMP analysis to complete
            time.sleep(20)  # Increased to 20 seconds
            
            # Display SNMP files after analysis
            display_snmp_files()
            
        except Exception as e:
            if hasattr(self, 'terminal_text') and self.terminal_text:
                self.terminal_text.insert(tk.END, f"[Error starting SNMP analysis]: {e}\n")

        # Run web access analysis
        try:
            if hasattr(self, 'terminal_text') and self.terminal_text:
                self.terminal_text.insert(tk.END, "[Starting web access analysis...]\n")
            
            web_process = subprocess.Popen(
                ["sudo", "-S", "python3", os.path.join(self.firmadyne_path, "analyses/webAccess.py"), "1", ip_address, log_file],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            if hasattr(self, 'web_output') and self.web_output:
                threading.Thread(
                    target=update_output,
                    args=(web_process, self.web_output, "Web"),
                    daemon=True
                ).start()
            
            # Wait before starting next analysis
            time.sleep(10)
            
        except Exception as e:
            if hasattr(self, 'terminal_text') and self.terminal_text:
                self.terminal_text.insert(tk.END, f"[Error starting web analysis]: {e}\n")

        # Run NMAP scan last
        try:
            if hasattr(self, 'terminal_text') and self.terminal_text:
                self.terminal_text.insert(tk.END, "[Starting NMAP scan...]\n")
            
            nmap_process = subprocess.Popen(
                ["sudo", "nmap", "-O", "-sV", ip_address],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            if hasattr(self, 'nmap_output') and self.nmap_output:
                threading.Thread(
                    target=update_output,
                    args=(nmap_process, self.nmap_output, "NMAP"),
                    daemon=True
                ).start()
            
        except Exception as e:
            if hasattr(self, 'terminal_text') and self.terminal_text:
                self.terminal_text.insert(tk.END, f"[Error starting NMAP scan]: {e}\n")

if _name_ == "_main_":
    root = TkinterDnD.Tk()
    app = FirmadyneGUI(root)
    root.mainloop()
