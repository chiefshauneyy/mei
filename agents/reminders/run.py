import subprocess

def get_today_reminders():
    # We tell AppleScript to fetch the names from the 'Today' list
    # and we use the 'reminders' order which typically follows the app's sort.
    script = '''
    tell application "Reminders"
        set taskNames to {}
        try
            -- Directly accessing the 'Today' smart list
            set todayList to list "Today"
            
            -- Get incomplete reminders from Today list
            set activeReminders to (reminders of todayList whose completed is false)
            
            repeat with r in activeReminders
                copy name of r to end of taskNames
            end repeat
        on error
            return ""
        end try
        return taskNames
    end tell
    '''
    try:
        process = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
        raw_output = process.stdout.strip()
        
        if not raw_output:
            return []
        
        # AppleScript returns a comma-separated string: "Task 1, Task 2"
        # We split by ", " but keep all items (no sets/dicts to avoid deleting duplicates)
        tasks = [t.strip() for t in raw_output.split(", ") if t]
        return tasks
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