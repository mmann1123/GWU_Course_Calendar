# 📌 START HERE - GWU Course Calendar

## 🎯 Two Ways to Use This

### Option 1: Just View the Calendar (NO SETUP NEEDED) ⭐
**Perfect if you just want to see the schedule**

1. Open **gwu_course_calendar.html** in your web browser
2. That's it! The calendar is already generated and ready to use
3. Click on any course to see details

✅ **This works immediately** - no installation required!

---

### Option 2: Generate Your Own Calendars (REQUIRES SETUP)
**Perfect if you want to scrape different subjects or update schedules**

#### First Time Setup (Do This Once)

**Windows Users:**
1. Double-click **run_scraper.bat**
2. Wait for packages to install (1-2 minutes)
3. Done!

**Mac/Linux Users:**
1. Open Terminal in this folder
2. Run: `chmod +x run_scraper.sh` 
3. Run: `./run_scraper.sh`
4. Wait for packages to install (1-2 minutes)
5. Done!

**Having installation issues?** → Read **INSTALLATION.md**

#### After Setup - Generate Calendars Anytime

```bash
# Geography courses (default)
python gwu_scraper.py

# Computer Science courses
python gwu_scraper.py --url "https://my.gwu.edu/mod/pws/courses.cfm?campId=1&termId=202601&subjId=CSCI" --output cs_calendar.html

# Math courses
python gwu_scraper.py --url "https://my.gwu.edu/mod/pws/courses.cfm?campId=1&termId=202601&subjId=MATH" --output math_calendar.html
```

---

## 📁 Files You Have

### 🌟 Ready to Use (No setup needed)
- **gwu_course_calendar.html** - Pre-generated calendar, open in browser!
- **courses_data.json** - Course data in JSON format

### 🔧 Application Files (Need setup first)
- **gwu_scraper.py** - Main Python application
- **requirements.txt** - List of required packages
- **run_scraper.bat** - Windows auto-install & run
- **run_scraper.sh** - Mac/Linux auto-install & run

### 📚 Documentation
- **QUICK_START.md** - Quick guide (read this second)
- **INSTALLATION.md** - Detailed installation help
- **README.md** - Complete documentation
- **FIXED_SUMMARY.md** - Technical details

---

## ❓ Quick Answers

### "I just want to see the calendar"
→ Open **gwu_course_calendar.html** in your browser

### "I want to generate calendars for other subjects"
→ Follow Option 2 setup above, then run with different URLs

### "I'm getting 'module not found' errors"
→ You need to install packages first. See **INSTALLATION.md**

### "The calendar is empty"
→ It shouldn't be! The fixed version has 32 courses. Try refreshing your browser or re-opening the HTML file

### "How do I change the subject from Geography?"
→ Use the `--url` parameter with different `subjId` (CSCI, MATH, BADM, etc.)

### "Can I make this an .exe file?"
→ Yes! See README.md section "Creating an Executable"

---

## 🎓 What the Calendar Shows

- **32 Geography Courses** for Spring 2026
- **13 Different Instructors**
- **Time slots**: 9:00 AM - 9:00 PM
- **Days**: Monday through Friday
- **Interactive features**: Click any course for details
- **Smart overlaps**: Overlapping courses shown side-by-side

---

## 🚀 Common Subjects You Can Scrape

Just change the `subjId=` parameter:

| Subject | Code | URL Parameter |
|---------|------|---------------|
| Computer Science | CSCI | `subjId=CSCI` |
| Mathematics | MATH | `subjId=MATH` |
| Business Admin | BADM | `subjId=BADM` |
| Psychology | PSYC | `subjId=PSYC` |
| Economics | ECON | `subjId=ECON` |
| Political Science | PSC | `subjId=PSC` |
| Biology | BISC | `subjId=BISC` |
| Chemistry | CHEM | `subjId=CHEM` |
| Physics | PHYS | `subjId=PHYS` |
| English | ENGL | `subjId=ENGL` |

Full example:
```bash
python gwu_scraper.py --url "https://my.gwu.edu/mod/pws/courses.cfm?campId=1&termId=202601&subjId=CSCI" --output cs.html
```

---

## 💡 Pro Tips

1. **Start with the pre-generated calendar** - Open gwu_course_calendar.html to see what it looks like
2. **Only install if you need custom calendars** - If the Geography schedule is all you need, no setup required!
3. **Use the automated scripts** - run_scraper.bat (Windows) or run_scraper.sh (Mac/Linux) handle everything
4. **Save multiple calendars** - Generate one for each subject you're interested in
5. **Keep the JSON** - The courses_data.json file is useful for analysis

---

## 🆘 Need Help?

**Installation problems?** → **INSTALLATION.md**

**Want step-by-step usage?** → **QUICK_START.md**

**Want all the details?** → **README.md**

**Technical questions?** → **FIXED_SUMMARY.md**

---

## ✅ Quick Verification

After installation, test if everything works:

```bash
# Show help (should display usage info)
python gwu_scraper.py --help

# Generate a test calendar
python gwu_scraper.py

# You should see: gwu_course_calendar.html created
```

If you see the success message, you're all set! 🎉

---

## 🎯 TL;DR

**Just want to view the calendar?**
→ Open gwu_course_calendar.html ✅

**Want to generate custom calendars?**
→ Run run_scraper.bat (Windows) or ./run_scraper.sh (Mac/Linux) ✅

**Having issues?**
→ Read INSTALLATION.md ✅

---

**You're ready to go! Pick an option above and get started.** 🚀
