import subprocess
from datetime import datetime

def get_today_reminders():
    # AppleScript to pull Name and Due Date as a combined string
    script = '''
    tell application "Reminders"
        set output to ""
        -- Target the Today smart list
        try
            set todayList to list "Today"
            set remindersList to reminders of todayList
            repeat with r in remindersList
                if not completed of r then
                    set d to ""
                    if due date of r is not missing value then
                        set d to (due date of r) as string
                    end if
                    set output to output & (name of r) & "|" & d & "||"
                end if
            end repeat
        on error
            return ""
        end try
        return output
    end tell
    '''
    try:
        process = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
        raw_output = process.stdout.strip()
        if not raw_output:
            return []
        
        # Split the custom formatted string
        # Format: Name|Date||Name|Date||
        items = raw_output.split("||")
        reminders_data = []
        
        for item in items:
            if "|" in item:
                name, date_str = item.split("|")
                # Store date as object for sorting, use high date if missing
                sort_date = datetime.max
                if date_str.strip():
                    try:
                        # AppleScript dates look like "Monday, February 2, 2026 at 6:00:00 PM"
                        # We'll try to parse, but if it fails we just use it as is
                        sort_date = datetime.strptime(date_str, "%A, %B %d, %Y at %I:%M:%S %p")
                    except:
                        pass
                reminders_data.append({"name": name, "date": sort_date})

        # Sort by date
        reminders_data.sort(key=lambda x: x["date"])
        return [r["name"] for r in reminders_data]
        
    except Exception as e:
        return [f"Error: {e}"]

def main():
    tasks = get_today_reminders()
    if not tasks:
        return "### 📝 Reminders\nNo tasks found for today."
    
    formatted = "\n".join([f"* {t}" for t in tasks])
    return f"### 📝 Today's Tasks ({len(tasks)})\n{formatted}"

if __name__ == "__main__":
    print(main())