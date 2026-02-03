import subprocess

def get_today_reminders():
    # This AppleScript targets the specific 'Today' smart list directly.
    script = '''
    tell application "Reminders"
        set todayTasks to {}
        -- 'Today' is a special built-in list in modern macOS
        try
            set todayList to list "Today"
            set remindersList to reminders of todayList
            repeat with r in remindersList
                if not completed of r then
                    copy name of r to end of todayTasks
                end if
            end repeat
        on error
            -- Fallback: If 'Today' as a list name fails, we get everything due today
            set midnight to (current date) + 1 * days
            set time of midnight to 0
            set allReminders to (reminders whose completed is false)
            repeat with r in allReminders
                try
                    if (due date of r < midnight) then
                        copy name of r to end of todayTasks
                    end if
                end try
            end repeat
        end try
        return todayTasks
    end tell
    '''
    try:
        process = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
        raw_output = process.stdout.strip()
        if not raw_output:
            return []
        
        # Clean and unique list
        reminders = [r.strip() for r in raw_output.split(", ") if r]
        return list(dict.fromkeys(reminders)) 
    except Exception as e:
        return [f"Error: {e}"]

def main():
    tasks = get_today_reminders()
    if not tasks:
        return "### 📝 Reminders\nNo tasks found in your Today list."
    
    formatted = "\n".join([f"* {t}" for t in tasks])
    return f"### 📝 Today's Tasks ({len(tasks)})\n{formatted}"

if __name__ == "__main__":
    print(main())