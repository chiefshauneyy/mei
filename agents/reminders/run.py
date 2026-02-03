import subprocess

def get_today_reminders():
    # This script pulls reminders that are:
    # 1. Incomplete AND due before midnight tonight
    # 2. Incomplete AND have no due date at all (covers 'Today' general tasks)
    script = '''
    set midnight to (current date) + 1 * days
    set time of midnight to 0
    
    tell application "Reminders"
        set finalNames to {}
        
        -- Get reminders due specifically today
        set dueToday to (reminders whose completed is false and due date is not missing value and due date is less than midnight)
        repeat with r in dueToday
            copy name of r to end of finalNames
        end repeat
        
        -- Get reminders with NO due date (often how 'Today' tasks appear in the DB)
        set noDate to (reminders whose completed is false and due date is missing value)
        repeat with r in noDate
            copy name of r to end of finalNames
        end repeat
        
        return finalNames
    end tell
    '''
    try:
        process = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
        raw_output = process.stdout.strip()
        if not raw_output:
            return []
        
        # AppleScript returns items separated by commas and spaces
        reminders = raw_output.split(", ")
        return list(set([r.strip() for r in reminders if r])) # use set to avoid duplicates
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