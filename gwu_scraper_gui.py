#!/usr/bin/env python3
"""
GWU Course Calendar Scraper - GUI Version
Provides a graphical interface for scraping GWU course schedules
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import sys
import os
from datetime import datetime

# Import the scraper components
from gwu_scraper import CourseScraper, generate_html_calendar


class ScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("GWU Course Calendar Scraper")
        self.root.geometry("700x600")
        self.root.resizable(True, True)

        # Variables
        self.is_scraping = False

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
        self.year_var = tk.StringVar()
        current_year = datetime.now().year
        years = [str(year) for year in range(current_year - 1, current_year + 3)]
        self.year_combo = ttk.Combobox(main_frame, textvariable=self.year_var,
                                       values=years, width=20, state='readonly')
        self.year_combo.set(str(current_year))
        self.year_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(0, 10))

        # Semester Selection
        ttk.Label(main_frame, text="Semester:", font=('Arial', 10)).grid(row=2, column=0, sticky=tk.W, pady=5)
        self.semester_var = tk.StringVar()
        # GWU uses: 01=Spring, 06=Summer, 08=Fall
        semesters = [
            "Spring (01)",
            "Summer (06)",
            "Fall (08)"
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

        # Progress Label
        self.progress_label = ttk.Label(main_frame, text="", font=('Arial', 10))
        self.progress_label.grid(row=7, column=0, columnspan=3, pady=(0, 10))

        # Output Text Area
        ttk.Label(main_frame, text="Output:", font=('Arial', 10, 'bold')).grid(row=8, column=0, sticky=tk.W, pady=(10, 5))

        self.output_text = scrolledtext.ScrolledText(main_frame, height=15, width=60,
                                                      wrap=tk.WORD, font=('Courier', 9))
        self.output_text.grid(row=9, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        main_frame.rowconfigure(9, weight=1)

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
        year = self.year_var.get()
        semester_code = self.get_semester_code()
        subject = self.subject_var.get().upper().strip()

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
            self.log(f"\n✓ Saved raw data to: {output_json}")

            generate_html_calendar(courses, output_html)
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

    def open_html_file(self, filename):
        """Open HTML file in default browser"""
        import webbrowser
        filepath = os.path.abspath(filename)
        webbrowser.open('file://' + filepath)


def main():
    root = tk.Tk()
    app = ScraperGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
