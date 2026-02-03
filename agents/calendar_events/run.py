import subprocess

def get_today_calendar():
    # Targets specific calendars identified by your terminal scan
    script = '''
    set midnight to (current date) + 1 * days
    set time of midnight to 0
    set output to ""
    
    tell application "Calendar"
        -- We focus only on your real data calendars
        set targetCalendars to {"Home", "Work"}
        
        repeat with calName in targetCalendars
            try
                set theCal to calendar calName
                set todayEvents to (events of theCal whose start date is less than midnight and start date is greater than or equal to (current date))
                
                repeat with e in todayEvents
                    set eventName to summary of e
                    set eventDate to start date of e
                    
                    set hr to hours of eventDate
                    set mn to minutes of eventDate
                    set ampm to "AM"
                    if hr ≥ 12 then set ampm to "PM"
                    if hr > 12 then set hr to hr - 12
                    if hr = 0 then set hr to 12
                    set mnStr to mn as string
                    if (length of mnStr) < 2 then set mnStr to "0" & mnStr
                    
                    set displayTime to hr & ":" & mnStr & " " & ampm
                    set output to output & eventName & "|" & (time of eventDate) & "|" & displayTime & ";"
                end repeat
            end try
        end repeat
    end tell
    return output
    '''
    try:
        process = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
        raw_output = process.stdout.strip()
        
        if not raw_output or raw_output == "":
            return []
        
        entries = [e for e in raw_output.split(";") if "|" in e]
        data = []
        for e in entries:
            name, seconds, display_time = e.split("|")
            data.append({"display": f"{name} ({display_time})", "seconds": int(seconds)})
            
        data.sort(key=lambda x: x["seconds"])
        return [item["display"] for item in data]
    except Exception:
        return []

def main():
    events = get_today_calendar()
    # Ensure it returns an empty string to core/runner.py if no events found
    if not events:
        return "" 
    
    formatted = "\n".join([f"* {e}" for e in events])
    return f"### 📅 Calendar Events\n{formatted}"

if __name__ == "__main__":
    print(main())