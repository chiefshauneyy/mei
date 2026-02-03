import subprocess

def get_today_reminders():
    # AppleScript to pull uncompleted reminders due before the end of today
    script = '''
    set midnight to (current date) + 1 * days
    set time of midnight to 0
    
    tell application "Reminders"
        set todoList to {}
        -- Get reminders that are incomplete AND due before tomorrow's midnight
        set todayReminders to (reminders whose completed is false and due date is not missing value and due date is less than midnight)
        
        repeat with re in todayReminders
            set end of todoList to (name of re)
        end repeat
        return todoList
    end tell
    '''
    try:
        process = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
        # Clean up the output string into a list
        raw_output = process.stdout.strip()
        if not raw_output:
            return []
        reminders = raw_output.split(", ")
        return [r for r in reminders if r]
    except Exception as e:
        return [f"Error fetching reminders: {e}"]

def main():
    tasks = get_today_reminders()
    if not tasks:
        # Returning an empty string prevents the header from showing if there's no data
        return ""
    
    formatted = "\n".join([f"* {t}" for t in tasks])
    return f"### 📝 Today's Reminders\n{formatted}"

if __name__ == "__main__":
    print(main())