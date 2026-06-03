#!/usr/bin/env python3
"""
GWU Course Calendar Scraper - GUI Version
Provides a graphical interface for scraping GWU course schedules
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import json
import threading
import sys
import os
from datetime import datetime

# Import the scraper components
from gwu_scraper import CourseScraper, generate_html_calendar
import registrar_io


class ScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GWU Course Calendar Scraper")
        self.root.geometry("700x600")
        self.root.resizable(True, True)

        # Variables
        self.is_scraping = False
        self.courses = None  # most recently scraped or imported courses

        # Create UI
        self.create_widgets()

    def create_widgets(self):
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights for resizing
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Title
        title_label = ttk.Label(main_frame, text="🎓 GWU Course Calendar Scraper",
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # Year Selection
        ttk.Label(main_frame, text="Year:", font=('Arial', 10)).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.year_var = tk.StringVar(value="2026")
        self.year_entry = ttk.Entry(main_frame, textvariable=self.year_var, width=20)
        self.year_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(0, 10))

        # Year hint
        year_hint = ttk.Label(main_frame, text="(4-digit year, e.g., 2026)",
                             font=('Arial', 8), foreground='gray')
        year_hint.grid(row=1, column=2, sticky=tk.W, padx=(5, 0))

        # Semester Selection
        ttk.Label(main_frame, text="Semester:", font=('Arial', 10)).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.semester_var = tk.StringVar()
        # GWU uses: 01=Spring, 02=Summer, 03=Fall
        semesters = [
            "Spring (01)",
            "Summer (02)",
            "Fall (03)"
        ]
        self.semester_combo = ttk.Combobox(main_frame, textvariable=self.semester_var,
                                           values=semesters, width=20, state='readonly')
        self.semester_combo.set("Spring (01)")
        self.semester_combo.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(0, 10))

        # Subject Code Entry
        ttk.Label(main_frame, text="Subject Code:", font=('Arial', 10)).grid(row=3, column=0, sticky=tk.W, pady=5)
        self.subject_var = tk.StringVar(value="GEOG")
        self.subject_entry = ttk.Entry(main_frame, textvariable=self.subject_var, width=20)
        self.subject_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5, padx=(0, 10))

        # Subject code hint
        hint_label = ttk.Label(main_frame, text="(e.g., GEOG, CSCI, MATH, PSYC)",
                              font=('Arial', 8), foreground='gray')
        hint_label.grid(row=4, column=1, sticky=tk.W, pady=(0, 10))

        # Output filename
        ttk.Label(main_frame, text="Output File:", font=('Arial', 10)).grid(row=5, column=0, sticky=tk.W, pady=5)
        self.output_var = tk.StringVar(value="gwu_course_calendar.html")
        self.output_entry = ttk.Entry(main_frame, textvariable=self.output_var, width=20)
        self.output_entry.grid(row=5, column=1, sticky=(tk.W, tk.E), pady=5, padx=(0, 10))

        # Button Frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=3, pady=20)

        # Scrape Button
        self.scrape_button = ttk.Button(button_frame, text="Scrape Courses",
                                        command=self.start_scraping)
        self.scrape_button.grid(row=0, column=0, padx=5)

        # Cancel Button
        self.cancel_button = ttk.Button(button_frame, text="Cancel",
                                        command=self.cancel_scraping, state='disabled')
        self.cancel_button.grid(row=0, column=1, padx=5)

        # Report Issue Button
        self.report_button = ttk.Button(button_frame, text="Report Issue",
                                        command=self.open_github_issues)
        self.report_button.grid(row=0, column=2, padx=5)

        # Registrar .xlsx Import/Export row
        registrar_frame = ttk.LabelFrame(main_frame, text="Registrar Spreadsheet (.xlsx)",
                                         padding="8")
        registrar_frame.grid(row=7, column=0, columnspan=3, pady=(0, 10),
                             sticky=(tk.W, tk.E))

        self.import_button = ttk.Button(registrar_frame, text="📥 Import .xlsx → Calendar",
                                        command=self.import_xlsx)
        self.import_button.grid(row=0, column=0, padx=5)

        self.export_button = ttk.Button(registrar_frame, text="📤 Export Calendar → .xlsx",
                                        command=self.export_xlsx)
        self.export_button.grid(row=0, column=1, padx=5)

        registrar_hint = ttk.Label(registrar_frame,
                                   text="Read/write the GWU registrar's schedule format",
                                   font=('Arial', 8), foreground='gray')
        registrar_hint.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(4, 0))

        # Progress Label
        self.progress_label = ttk.Label(main_frame, text="", font=('Arial', 10))
        self.progress_label.grid(row=8, column=0, columnspan=3, pady=(0, 10))

        # Output Text Area
        ttk.Label(main_frame, text="Output:", font=('Arial', 10, 'bold')).grid(row=9, column=0, sticky=tk.W, pady=(10, 5))

        self.output_text = scrolledtext.ScrolledText(main_frame, height=15, width=60,
                                                      wrap=tk.WORD, font=('Courier', 9))
        self.output_text.grid(row=10, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        main_frame.rowconfigure(10, weight=1)

        # Status Bar
        self.status_bar = ttk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))

    def log(self, message):
        """Add message to output text area"""
        self.output_text.insert(tk.END, message + "\n")
        self.output_text.see(tk.END)
        self.root.update_idletasks()

    def update_status(self, message):
        """Update status bar"""
        self.status_bar.config(text=message)

    def get_semester_code(self):
        """Extract semester code from dropdown selection"""
        semester_text = self.semester_var.get()
        # Extract code from "Spring (01)" format
        code = semester_text.split("(")[1].split(")")[0]
        return code

    def build_url(self):
        """Build the GWU course URL from user inputs"""
        year = self.year_var.get().strip()
        semester_code = self.get_semester_code()
        subject = self.subject_var.get().upper().strip()

        # Validate year
        if not year:
            raise ValueError("Year is required")
        if not year.isdigit() or len(year) != 4:
            raise ValueError("Year must be a 4-digit number (e.g., 2026)")

        year_int = int(year)
        if year_int < 2000 or year_int > 2099:
            raise ValueError("Year must be between 2000 and 2099")

        if not subject:
            raise ValueError("Subject code is required")

        term_id = f"{year}{semester_code}"
        url = f"https://my.gwu.edu/mod/pws/courses.cfm?campId=1&termId={term_id}&subjId={subject}"
        return url

    def start_scraping(self):
        """Start the scraping process in a background thread"""
        if self.is_scraping:
            return

        # Validate inputs
        try:
            url = self.build_url()
        except ValueError as e:
            messagebox.showerror("Input Error", str(e))
            return

        # Clear output
        self.output_text.delete(1.0, tk.END)

        # Update UI
        self.is_scraping = True
        self.scrape_button.config(state='disabled')
        self.cancel_button.config(state='normal')
        self.update_status("Scraping in progress...")
        self.progress_label.config(text="Starting scraper...")

        # Start scraping in background thread
        thread = threading.Thread(target=self.scrape, args=(url,), daemon=True)
        thread.start()

    def cancel_scraping(self):
        """Cancel the scraping process"""
        self.is_scraping = False
        self.log("\n⚠️  Scraping cancelled by user")
        self.update_status("Cancelled")
        self.scrape_button.config(state='normal')
        self.cancel_button.config(state='disabled')

    def scrape(self, url):
        """Perform the actual scraping"""
        try:
            self.log("="*70)
            self.log("🎓 GWU COURSE CALENDAR SCRAPER")
            self.log("="*70)
            self.log(f"\nYear: {self.year_var.get()}")
            self.log(f"Semester: {self.semester_var.get()}")
            self.log(f"Subject: {self.subject_var.get().upper()}")
            self.log(f"\nURL: {url}\n")

            # Create scraper
            scraper = CourseScraper(url=url)

            self.log("Starting scrape...\n")
            self.progress_label.config(text="Fetching data from GWU...")

            # Scrape courses
            courses = scraper.scrape()

            if not self.is_scraping:
                return

            if len(courses) == 0:
                self.log("\n⚠️  WARNING: No courses found!")
                self.log("   The subject code might be invalid or no courses are offered.")
                self.update_status("No courses found")
                return

            # Generate output files
            self.progress_label.config(text="Generating calendar...")
            output_html = self.output_var.get()
            output_json = output_html.replace('.html', '.json')

            scraper.save_to_json(output_json)
            self.courses = courses  # keep for registrar export
            self.log(f"\n✓ Saved raw data to: {output_json}")

            # Get year and semester for HTML title
            year = self.year_var.get().strip()
            semester_code = self.get_semester_code()
            generate_html_calendar(courses, output_html, year=year, semester=semester_code)
            self.log(f"✓ Calendar saved to: {output_html}")

            # Success
            self.log("\n" + "="*70)
            self.log("✅ SUCCESS!")
            self.log(f"   📊 {len(courses)} courses")
            self.log(f"   📅 {output_html}")
            self.log("="*70)

            self.update_status(f"Success! {len(courses)} courses scraped")
            self.progress_label.config(text=f"✅ Completed: {len(courses)} courses found")

            # Ask if user wants to open the calendar
            result = messagebox.askyesno("Success",
                                        f"Successfully scraped {len(courses)} courses!\n\n"
                                        f"Calendar saved to: {output_html}\n\n"
                                        "Would you like to open the calendar in your browser?")
            if result:
                self.open_html_file(output_html)

        except Exception as e:
            self.log(f"\n❌ ERROR: {str(e)}")
            self.update_status("Error occurred")
            self.progress_label.config(text="❌ Error")
            messagebox.showerror("Scraping Error", f"An error occurred:\n\n{str(e)}")

        finally:
            self.is_scraping = False
            self.scrape_button.config(state='normal')
            self.cancel_button.config(state='disabled')

    def import_xlsx(self):
        """Import a registrar-format .xlsx file and build the calendar from it."""
        if self.is_scraping:
            return

        path = filedialog.askopenfilename(
            title="Select registrar schedule (.xlsx)",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")])
        if not path:
            return

        self.output_text.delete(1.0, tk.END)
        try:
            self.log("="*70)
            self.log("📥 IMPORTING REGISTRAR SPREADSHEET")
            self.log("="*70)
            self.log(f"\nFile: {path}\n")

            courses, warnings = registrar_io.read_registrar_xlsx(path, return_warnings=True)
            for w in warnings:
                self.log(f"⚠️  {w}")
            if not courses:
                self.log("⚠️  No course rows found in the file.")
                messagebox.showwarning("Import", "No course rows were found in that file.")
                return

            self.courses = courses
            timed = [c for c in courses if c.get('time')]
            tba = len(courses) - len(timed)
            self.log(f"✓ Read {len(courses)} courses "
                     f"({len(timed)} scheduled, {tba} arranged/TBA)")

            output_html = self.output_var.get()
            output_json = output_html.replace('.html', '.json')
            with open(output_json, 'w', encoding='utf-8') as f:
                json.dump(courses, f, indent=2)
            self.log(f"✓ Saved raw data to: {output_json}")

            # Only scheduled courses can be placed on the calendar grid.
            generate_html_calendar(timed, output_html)
            self.log(f"✓ Calendar saved to: {output_html}")
            if tba:
                self.log(f"\nℹ️  {tba} arranged/TBA course(s) have no meeting time and "
                         f"are not shown on the calendar grid (still kept in the data).")

            self.update_status(f"Imported {len(courses)} courses")
            self.progress_label.config(text=f"✅ Imported {len(courses)} courses")

            if messagebox.askyesno("Import complete",
                                   f"Imported {len(courses)} courses "
                                   f"({len(timed)} scheduled).\n\n"
                                   f"Calendar saved to: {output_html}\n\n"
                                   "Open the calendar in your browser?"):
                self.open_html_file(output_html)

        except ImportError as e:
            self.log(f"\n❌ {e}")
            messagebox.showerror("Missing dependency", str(e))
        except Exception as e:
            self.log(f"\n❌ ERROR: {e}")
            self.update_status("Import error")
            messagebox.showerror("Import Error", f"Could not import that file:\n\n{e}")

    def export_xlsx(self):
        """Export the current courses to a registrar-format .xlsx file."""
        courses = self.courses
        # Fall back to the JSON next to the output file if nothing is loaded.
        if not courses:
            output_json = self.output_var.get().replace('.html', '.json')
            if os.path.exists(output_json):
                try:
                    with open(output_json, encoding='utf-8') as f:
                        courses = json.load(f)
                except Exception:
                    courses = None

        if not courses:
            messagebox.showinfo(
                "Nothing to export",
                "Scrape or import some courses first, then export.")
            return

        path = filedialog.asksaveasfilename(
            title="Save registrar schedule (.xlsx)",
            defaultextension=".xlsx",
            initialfile="registrar_schedule.xlsx",
            filetypes=[("Excel files", "*.xlsx")])
        if not path:
            return

        try:
            registrar_io.write_registrar_xlsx(courses, path)
            self.log(f"\n✓ Exported {len(courses)} courses to: {path}")
            self.update_status(f"Exported {len(courses)} courses")
            messagebox.showinfo("Export complete",
                                f"Exported {len(courses)} courses to:\n\n{path}")
        except ImportError as e:
            messagebox.showerror("Missing dependency", str(e))
        except Exception as e:
            self.log(f"\n❌ ERROR: {e}")
            messagebox.showerror("Export Error", f"Could not write that file:\n\n{e}")

    def open_html_file(self, filename):
        """Open HTML file in default browser"""
        import webbrowser
        filepath = os.path.abspath(filename)
        webbrowser.open('file://' + filepath)

    def open_github_issues(self):
        """Open GitHub issues page in default browser"""
        import webbrowser
        webbrowser.open('https://github.com/mmann1123/GWU_Course_Calendar/issues')


def main():
    root = tk.Tk()
    app = ScraperGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
