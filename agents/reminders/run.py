import subprocess
import json

def get_reminders():
    # AppleScript to pull incomplete reminders due today or without a date
    script = '''
    tell application "Reminders"
        set todoList to {}
        set activeReminders to (reminders whose completed is false)
        repeat with re in activeReminders
            set end of todoList to (name of re)
        end repeat
        return todoList
    end tell
    '''
    try:
        process = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
        # Convert the AppleScript list string into a clean Python list
        reminders = process.stdout.strip().split(", ")
        return [r for r in reminders if r] # Remove empties
    except Exception as e:
        return [f"Error: {e}"]

def main():
    tasks = get_reminders()
    if not tasks:
        return "### ✅ Tasks\nNo pending reminders for today! Nice."
    
    formatted = "\n".join([f"* {t}" for t in tasks])
    return f"### 📝 Reminders\n{formatted}"

if __name__ == "__main__":
    print(main())