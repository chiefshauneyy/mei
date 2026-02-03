import subprocess

def get_today_reminders():
    # AppleScript: Get name and time (in seconds from start of day)
    # Tasks with no time set are assigned -1 so they appear at the TOP
    script = '''
    set midnight to (current date) + 1 * days
    set time of midnight to 0
    set output to ""
    
    tell application "Reminders"
        set allR to (reminders whose completed is false)
        repeat with r in allR
            set isToday to false
            try
                -- Catch tasks due today OR overdue
                if (due date of r < midnight) then
                    set dnd to name of r
                    set rawTime to -1
                    set displayTime to ""
                    
                    if due date of r is not missing value then
                        set theDate to due date of r
                        set rawTime to time of theDate
                        -- Format a simple 12h display string
                        set hr to hours of theDate
                        set mn to minutes of theDate
                        set ampm to "AM"
                        if hr ≥ 12 then set ampm to "PM"
                        if hr > 12 then set hr to hr - 12
                        if hr = 0 then set hr to 12
                        set mnStr to mn as string
                        if (length of mnStr) < 2 then set mnStr to "0" & mnStr
                        set displayTime to " (" & hr & ":" & mnStr & " " & ampm & ")"
                    end if
                    
                    set output to output & dnd & displayTime & "|" & rawTime & ";"
                end if
            end try
        end repeat
    end tell
    return output
    '''
    try:
        process = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
        raw_output = process.stdout.strip()
        if not raw_output:
            return []
        
        # Split into individual reminder entries
        entries = [e for e in raw_output.split(";") if "|" in e]
        
        # Parse into a list of dicts for sorting
        data = []
        for e in entries:
            display_name, seconds = e.split("|")
            data.append({
                "display": display_name,
                "seconds": int(seconds)
            })
            
        # Sort by seconds (No-time tasks first, then 12:00 AM to 11:59 PM)
        data.sort(key=lambda x: x["seconds"])
        
        return [item["display"] for item in data]
    except Exception as e:
        return [f"Error parsing reminders: {e}"]

def main():
    tasks = get_today_reminders()
    if not tasks:
        return "### 📝 Reminders\nNo tasks found for today."
    
    formatted = "\n".join([f"* {t}" for t in tasks])
    return f"### 📝 Today's Tasks ({len(tasks)})\n{formatted}"

if __name__ == "__main__":
    print(main())