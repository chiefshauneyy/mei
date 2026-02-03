import subprocess

def get_today_reminders():
    # We use a custom delimiter (;) to avoid issues with commas in task names
    script = '''
    set midnight to (current date) + 1 * days
    set time of midnight to 0
    set todayTasks to ""
    
    tell application "Reminders"
        -- Get all incomplete reminders
        set allR to (reminders whose completed is false)
        repeat with r in allR
            set isToday to false
            try
                -- Check if it's due today or overdue
                if (due date of r < midnight) then set isToday to true
            end try
            
            if isToday then
                set todayTasks to todayTasks & (name of r) & ";"
            end if
        end repeat
    end tell
    return todayTasks
    '''
    try:
        process = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
        raw_output = process.stdout.strip()
        
        if not raw_output:
            return []
        
        # Split by our custom semicolon and clean up
        tasks = [t.strip() for t in raw_output.split(";") if t.strip()]
        return tasks
    except Exception as e:
        return [f"Error: {e}"]

def main():
    tasks = get_today_reminders()
    if not tasks:
        return "### 📝 Reminders\nNo tasks found due for today."
    
    # Simple list (keeping duplicates)
    formatted = "\n".join([f"* {t}" for t in tasks])
    return f"### 📝 Today's Tasks ({len(tasks)})\n{formatted}"

if __name__ == "__main__":
    print(main())