import subprocess
from datetime import datetime

def get_today_reminders():
    # This script pulls name and time, separated by a pipe (|)
    script = '''
    set midnight to (current date) + 1 * days
    set time of midnight to 0
    set output to ""
    
    tell application "Reminders"
        set allR to (reminders whose completed is false)
        repeat with r in allR
            set isToday to false
            try
                if (due date of r < midnight) then
                    set dnd to name of r
                    set dt to ""
                    if due date of r is not missing value then
                        -- Get time in 24hr format for easy Python sorting
                        set hh to hours of (due date of r)
                        set mm to minutes of (due date of r)
                        set dt to (hh as string) & ":" & (mm as string)
                    end if
                    set output to output & dnd & "|" & dt & ";"
                end if
            end try
        end repeat
    end tell
    return output
    '''
    try:
        process = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
        raw_output = process.stdout.strip()
        if not raw_output: return []
        
        items = [t.strip() for t in raw_output.split(";") if t.strip()]
        reminders_list = []
        
        for item in items:
            name, time_str = item.split("|")
            # If no time, treat as end of day
            sort_time = time_str if time_str else "23:59"
            
            # Convert 24h to 12h for the display
            display_time = ""
            if time_str:
                h, m = map(int, time_str.split(":"))
                period = "AM" if h < 12 else "PM"
                h_12 = h if 0 < h <= 12 else abs(h - 12)
                if h == 0: h_12 = 12
                display_time = f" ({h_12}:{m:02d} {period})"
            
            reminders_list.append({
                "name": name,
                "sort_key": sort_time,
                "display": f"{name}{display_time}"
            })

        # Sort based on the 24h time string
        reminders_list.sort(key=lambda x: x["sort_key"])
        return [r["display"] for r in reminders_list]
    except Exception as e:
        return [f"Error: {e}"]

def main():
    tasks = get_today_reminders()
    if not tasks:
        return "### 📝 Reminders\nNo tasks found due for today."
    
    formatted = "\n".join([f"* {t}" for t in tasks])
    return f"### 📝 Today's Tasks ({len(tasks)})\n{formatted}"

if __name__ == "__main__":
    print(main())