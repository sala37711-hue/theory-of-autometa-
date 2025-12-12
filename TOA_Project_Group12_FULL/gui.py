# gui.py - Separate Tkinter GUI frontend for the TOA project
# Enhanced: added Load/Save Regex, Clear Output, Export ZIP, Save Report, Zoom controls, Help
import os
import threading
import traceback
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import shutil
import time
from datetime import datetime

# Attempt to import PIL for image display; fall back to os.startfile for viewing images
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

# Import pipeline functions from your project (assumes same folder)
from regex_parser import to_postfix
from thompson_nfa import build_from_postfix, NFA
from subset_dfa import nfa_to_dfa, DFA
from minimizer import hopcroft_minimize
from visualize import draw_nfa, draw_dfa, draw_min_dfa
from table_formatter import (
    TableFormatter, create_nfa_table, create_dfa_table,
    create_minimized_dfa_table, MinimizationSteps, StringSimulation
)

DIAGRAM_DIR = 'diagrams'
os.makedirs(DIAGRAM_DIR, exist_ok=True)

# default regex from your project (Group 12)
DEFAULT_REGEX = "ggh + m(pg + gg + ggg)*m + hg"
DEFAULT_TEST = "ggh"

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TOA Project - GUI (Separate)")
        self.geometry("1200x760")
        self._img_refs = {}  # keep references to PhotoImage objects
        self._thumb_size = (420, 320)  # default thumbnail size (width, height)

        # Top frame: inputs + control buttons
        top = ttk.Frame(self)
        top.pack(side='top', fill='x', padx=8, pady=6)

        ttk.Label(top, text="Regular Expression:").grid(row=0, column=0, sticky='w')
        self.re_var = tk.StringVar(value=DEFAULT_REGEX)
        self.re_entry = ttk.Entry(top, textvariable=self.re_var, width=70)
        self.re_entry.grid(row=0, column=1, padx=6, sticky='w', columnspan=4)

        ttk.Label(top, text="Test String:").grid(row=1, column=0, sticky='w')
        self.test_var = tk.StringVar(value=DEFAULT_TEST)
        self.test_entry = ttk.Entry(top, textvariable=self.test_var, width=30)
        self.test_entry.grid(row=1, column=1, padx=6, sticky='w')

        btn_run = ttk.Button(top, text="Run Pipeline", command=self.run_pipeline_threaded)
        btn_run.grid(row=0, column=5, padx=6, rowspan=1, sticky='n')

        btn_open = ttk.Button(top, text="Open Diagrams Folder", command=self.open_diagram_folder)
        btn_open.grid(row=0, column=6, padx=6, rowspan=1, sticky='n')

        btn_load = ttk.Button(top, text="Load Regex", command=self.load_regex_from_file)
        btn_load.grid(row=1, column=5, padx=6, sticky='w')

        btn_save_re = ttk.Button(top, text="Save Regex", command=self.save_regex_to_file)
        btn_save_re.grid(row=1, column=6, padx=6, sticky='w')

        btn_clear = ttk.Button(top, text="Clear Output", command=self.clear_output)
        btn_clear.grid(row=0, column=7, padx=6, sticky='n')

        btn_save_report = ttk.Button(top, text="Save Report", command=self.save_report_to_file)
        btn_save_report.grid(row=1, column=7, padx=6, sticky='w')

        btn_export_zip = ttk.Button(top, text="Export ZIP", command=self.export_zip)
        btn_export_zip.grid(row=0, column=8, padx=6, sticky='n')

        btn_help = ttk.Button(top, text="Help", command=self.show_help)
        btn_help.grid(row=1, column=8, padx=6, sticky='w')

        # Middle frame: text output and images
        middle = ttk.Panedwindow(self, orient='horizontal')
        middle.pack(fill='both', expand=True, padx=8, pady=6)

        # Left side: textual output
        left = ttk.Frame(middle, width=620)
        middle.add(left, weight=1)

        self.text = tk.Text(left, wrap='none')
        self.text.pack(side='left', fill='both', expand=True)

        # add vertical scrollbar
        vsb = ttk.Scrollbar(left, orient='vertical', command=self.text.yview)
        vsb.pack(side='right', fill='y')
        self.text.configure(yscrollcommand=vsb.set)

        # Right side: notebook tabs for images (NFA / DFA / Minimized DFA)
        right = ttk.Frame(middle, width=520)
        middle.add(right, weight=0)

        # Notebook (tabs) to show each diagram clearly
        notebook = ttk.Notebook(right)
        notebook.pack(fill='both', expand=True, padx=6, pady=6)

        self.image_labels = {}
        for name, title in (('nfa', 'NFA'), ('dfa', 'DFA'), ('min_dfa', 'Minimized DFA')):
            tab_frame = ttk.Frame(notebook)
            notebook.add(tab_frame, text=title)

            # put the image label inside a labeled frame so each tab has a title border
            container = ttk.LabelFrame(tab_frame, text=title)
            container.pack(fill='both', expand=True, padx=6, pady=6)

            # Add a toolbar for zoom in/out per tab
            toolbar = ttk.Frame(container)
            toolbar.pack(side='top', fill='x', padx=6, pady=4)
            zoom_in = ttk.Button(toolbar, text="Zoom In", command=lambda n=name: self.zoom_image(n, 1.2))
            zoom_in.pack(side='left', padx=4)
            zoom_out = ttk.Button(toolbar, text="Zoom Out", command=lambda n=name: self.zoom_image(n, 0.8))
            zoom_out.pack(side='left', padx=4)
            save_img = ttk.Button(toolbar, text="Save Image As...", command=lambda n=name: self.save_image_as(n))
            save_img.pack(side='left', padx=4)

            lbl = ttk.Label(container, text=f"No {name}.png yet", anchor='center')
            lbl.pack(fill='both', expand=True, padx=8, pady=8)
            self.image_labels[name] = lbl

        # status bar
        self.status = ttk.Label(self, text="Ready", relief='sunken', anchor='w')
        self.status.pack(side='bottom', fill='x')

    # -------------------------
    # Utility and UI functions
    # -------------------------
    def log(self, msg):
        self.text.insert('end', msg + '\n')
        self.text.see('end')

    def clear_output(self):
        self.text.delete('1.0', 'end')
        self.set_status("Output cleared")

    def set_status(self, s):
        self.status.config(text=s)
        self.update_idletasks()

    def open_diagram_folder(self):
        path = os.path.abspath(DIAGRAM_DIR)
        try:
            if os.name == 'nt':
                os.startfile(path)
            elif os.name == 'posix':
                import subprocess
                subprocess.run(['xdg-open', path])
            else:
                messagebox.showinfo("Open folder", f"Open the folder manually: {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open folder: {e}")

    def load_regex_from_file(self):
        fn = filedialog.askopenfilename(title="Load Regular Expression", filetypes=[("Text files","*.txt"),("All files","*.*")])
        if not fn:
            return
        try:
            with open(fn, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            self.re_var.set(content)
            self.set_status(f"Loaded regex from {os.path.basename(fn)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {e}")

    def save_regex_to_file(self):
        fn = filedialog.asksaveasfilename(title="Save Regular Expression", defaultextension=".txt", filetypes=[("Text files","*.txt"),("All files","*.*")])
        if not fn:
            return
        try:
            with open(fn, 'w', encoding='utf-8') as f:
                f.write(self.re_var.get())
            self.set_status(f"Saved regex to {os.path.basename(fn)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {e}")

    def save_report_to_file(self):
        fn = filedialog.asksaveasfilename(title="Save Report", defaultextension=".txt", filetypes=[("Text files","*.txt")])
        if not fn:
            return
        try:
            content = self.text.get('1.0', 'end')
            with open(fn, 'w', encoding='utf-8') as f:
                f.write(content)
            self.set_status(f"Report saved to {os.path.basename(fn)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save report: {e}")

    def export_zip(self):
        # collect diagrams and a text report, save as zip
        fn = filedialog.asksaveasfilename(title="Export ZIP", defaultextension=".zip", filetypes=[("ZIP files","*.zip")])
        if not fn:
            return
        try:
            tmpdir = os.path.join(DIAGRAM_DIR, f"export_{int(time.time())}")
            os.makedirs(tmpdir, exist_ok=True)
            # save report.txt
            report_path = os.path.join(tmpdir, "report.txt")
            with open(report_path, 'w', encoding='utf-8') as r:
                r.write(self.text.get('1.0', 'end'))
            # copy diagrams
            for name in ('nfa','dfa','min_dfa'):
                src = os.path.join(DIAGRAM_DIR, f"{name}.png")
                if os.path.exists(src):
                    shutil.copy2(src, tmpdir)
            # create zip
            base = os.path.splitext(fn)[0]
            shutil.make_archive(base, 'zip', tmpdir)
            # remove tmpdir
            shutil.rmtree(tmpdir)
            self.set_status(f"Exported ZIP to {os.path.basename(fn)}")
            messagebox.showinfo("Exported", f"ZIP saved: {fn}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export ZIP: {e}")

    def show_help(self):
        messagebox.showinfo("Help - TOA GUI", (
            "This GUI runs the RE -> NFA -> DFA -> Minimize pipeline.\n\n"
            "Buttons:\n"
            "- Run Pipeline: execute the pipeline and display results\n"
            "- Open Diagrams Folder: open the diagrams/ folder\n"
            "- Load/Save Regex: load or save RE text files\n"
            "- Clear Output: clears the textual output area\n"
            "- Save Report: save textual output to a .txt file\n"
            "- Export ZIP: create a zip containing the diagrams and a report\n"
            "- Zoom In/Out (per tab): enlarge or shrink the displayed diagram\n"
            "\nIf PIL (Pillow) is not installed, images will be opened with your OS image viewer."
        ))

    # -------------------------
    # Pipeline orchestration
    # -------------------------
    def run_pipeline_threaded(self):
        t = threading.Thread(target=self.run_pipeline, daemon=True)
        t.start()

    def safe_call(self, fn, *a, **kw):
        try:
            return fn(*a, **kw)
        except Exception as e:
            self.log("EXCEPTION: " + repr(e))
            self.log(traceback.format_exc())
            raise

    def run_pipeline(self):
        self.set_status("Running pipeline...")
        self.text.delete('1.0', 'end')
        regex = self.re_var.get().strip()
        test = self.test_var.get().strip()

        if not regex:
            messagebox.showwarning("Input required", "Please enter a regular expression.")
            self.set_status("Idle")
            return

        # 1) postfix conversion
        try:
            postfix = to_postfix(regex)
            self.log(TableFormatter.format_pipeline_start(regex, postfix))
        except Exception as e:
            self.log(TableFormatter.format_error_message(f"Regex parsing failed: {str(e)}"))
            self.log(traceback.format_exc())
            self.set_status("Error")
            return

        # 2) build NFA
        try:
            nfa = build_from_postfix(postfix)
            self.log(TableFormatter.format_section_header("STEP 1: THOMPSON NFA CONSTRUCTION"))
            nfa_table = create_nfa_table(nfa)
            self.log(nfa_table.to_formatted_string())
            self.log(TableFormatter.format_info_message(
                f"NFA built successfully with {len(nfa_table.rows)} states"
            ))
        except Exception as e:
            self.log(TableFormatter.format_error_message(f"NFA construction failed: {str(e)}"))
            self.log(traceback.format_exc())
            self.set_status("Error")
            return

        # render NFA
        try:
            draw_nfa(nfa, filename=os.path.join(DIAGRAM_DIR, 'nfa'))
            self.log(TableFormatter.format_info_message(
                f"NFA diagram saved: {os.path.join(DIAGRAM_DIR, 'nfa.png')}"
            ))
            self.display_image_safe('nfa', os.path.join(DIAGRAM_DIR, 'nfa.png'))
        except Exception as e:
            self.log(TableFormatter.format_error_message(f"NFA diagram rendering failed: {str(e)}"))
            self.log(traceback.format_exc())

        # 3) convert to DFA
        try:
            dfa = nfa_to_dfa(nfa)
            self.log(TableFormatter.format_section_header("STEP 2: SUBSET CONSTRUCTION (DFA)"))
            dfa_table = create_dfa_table(dfa)
            self.log(dfa_table.to_formatted_string())
            self.log(TableFormatter.format_info_message(
                f"DFA constructed with {len(dfa_table.rows)} states"
            ))
        except Exception as e:
            self.log(TableFormatter.format_error_message(f"DFA construction failed: {str(e)}"))
            self.log(traceback.format_exc())
            self.set_status("Error")
            return

        # render DFA
        try:
            draw_dfa(dfa, filename=os.path.join(DIAGRAM_DIR, 'dfa'))
            self.log(TableFormatter.format_info_message(
                f"DFA diagram saved: {os.path.join(DIAGRAM_DIR, 'dfa.png')}"
            ))
            self.display_image_safe('dfa', os.path.join(DIAGRAM_DIR, 'dfa.png'))
        except Exception as e:
            self.log(TableFormatter.format_error_message(f"DFA diagram rendering failed: {str(e)}"))
            self.log(traceback.format_exc())

        # 4) minimize DFA using Hopcroft's algorithm
        try:
            min_dfa, steps = hopcroft_minimize(dfa)
            self.log(TableFormatter.format_section_header("STEP 3: DFA MINIMIZATION (HOPCROFT)"))
            
            # Format and log minimization steps
            min_steps_obj = MinimizationSteps(steps=steps)
            self.log(min_steps_obj.to_formatted_string())
            
            # Show minimized table
            min_table = create_minimized_dfa_table(min_dfa)
            self.log(min_table.to_formatted_string())
            
            self.log(TableFormatter.format_info_message(
                f"DFA minimized: {len(dfa_table.rows)} states → {len(min_table.rows)} states"
            ))
        except Exception as e:
            self.log(TableFormatter.format_error_message(f"DFA minimization failed: {str(e)}"))
            self.log(traceback.format_exc())
            self.set_status("Error")
            return

        # render minimized DFA
        try:
            draw_min_dfa(min_dfa, filename=os.path.join(DIAGRAM_DIR, 'min_dfa'))
            self.log(TableFormatter.format_info_message(
                f"Minimized DFA diagram saved: {os.path.join(DIAGRAM_DIR, 'min_dfa.png')}"
            ))
            self.display_image_safe('min_dfa', os.path.join(DIAGRAM_DIR, 'min_dfa.png'))
        except Exception as e:
            self.log(TableFormatter.format_error_message(f"Minimized DFA diagram rendering failed: {str(e)}"))
            self.log(traceback.format_exc())

        # 5) string simulation
        try:
            self.log(TableFormatter.format_section_header("STEP 4: STRING SIMULATION"))
            
            simulation = StringSimulation(input_string=test)
            current = min_dfa.start
            
            if test:
                for ch in test:
                    next_state = min_dfa.transitions.get(current, {}).get(ch)
                    next_str = next_state if next_state is not None else "REJECT"
                    simulation.trace.append((current, ch, next_str))
                    
                    if next_state is None:
                        simulation.result = "Rejected"
                        break
                    current = next_state
                
                if simulation.result == "Pending":
                    if current in min_dfa.final_states:
                        simulation.result = "Accepted"
                    else:
                        simulation.result = "Rejected"
            else:
                simulation.result = "Rejected (empty input)"
            
            self.log(simulation.to_formatted_string())
        except Exception as e:
            self.log(TableFormatter.format_error_message(f"String simulation failed: {str(e)}"))
            self.log(traceback.format_exc())

        self.log("\n" + "=" * 70)
        self.log("PIPELINE EXECUTION COMPLETED SUCCESSFULLY")
        self.log("=" * 70 + "\n")
        self.set_status("Done")

    # -------------------------
    # Image helpers
    # -------------------------
    def display_image_safe(self, key, path):
        # Display PNG in GUI if possible; otherwise open externally
        if not os.path.exists(path):
            self.log(f"Image not found: {path}")
            return
        if PIL_AVAILABLE:
            try:
                img = Image.open(path)
                img = img.convert("RGBA")
                img.thumbnail(self._thumb_size, Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.image_labels[key].config(image=photo, text='')
                # retain reference
                self._img_refs[key] = photo
            except Exception as e:
                self.log("PIL display error: " + str(e))
                try:
                    if os.name == 'nt':
                        os.startfile(path)
                    else:
                        import subprocess
                        subprocess.run(['xdg-open', path])
                except Exception:
                    pass
        else:
            # fallback: open externally
            try:
                if os.name == 'nt':
                    os.startfile(path)
                else:
                    import subprocess
                    subprocess.run(['xdg-open', path])
            except Exception as e:
                self.log("Cannot open image externally: " + str(e))

    def zoom_image(self, key, factor):
        # adjust thumbnail size and re-display the image if present
        w, h = self._thumb_size
        w = max(80, int(w * factor))
        h = max(60, int(h * factor))
        self._thumb_size = (w, h)
        path = os.path.join(DIAGRAM_DIR, f"{key}.png")
        if os.path.exists(path):
            self.display_image_safe(key, path)
            self.set_status(f"Zoom {key} to {w}x{h}")

    def save_image_as(self, key):
        src = os.path.join(DIAGRAM_DIR, f"{key}.png")
        if not os.path.exists(src):
            messagebox.showwarning("Save Image", f"No {key}.png found.")
            return
        fn = filedialog.asksaveasfilename(title=f"Save {key}.png As", defaultextension=".png", filetypes=[("PNG","*.png")])
        if not fn:
            return
        try:
            shutil.copy2(src, fn)
            self.set_status(f"Saved {os.path.basename(fn)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save image: {e}")

if __name__ == '__main__':
    app = App()
    app.mainloop()
