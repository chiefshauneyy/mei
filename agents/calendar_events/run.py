import subprocess

def get_today_calendar():
    # AppleScript to fetch events for the current day
    script = '''
    set midnight to (current date) + 1 * days
    set time of midnight to 0
    set output to ""
    
    tell application "Calendar"
        -- Look at all calendars
        set allCalendars to calendars
        repeat with theCal in allCalendars
            -- Find events starting today but before tomorrow's midnight
            set todayEvents to (events of theCal whose start date is less than midnight and start date is greater than or equal to (current date))
            repeat with e in todayEvents
                set eventName to summary of e
                set eventDate to start date of e
                
                -- Convert time to 12h format
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
        end repeat
    end tell
    return output
    '''
    try:
        process = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
        raw_output = process.stdout.strip()
        if not raw_output: return []
        
        entries = [e for e in raw_output.split(";") if "|" in e]
        data = []
        for e in entries:
            name, seconds, display_time = e.split("|")
            data.append({"display": f"{name} ({display_time})", "seconds": int(seconds)})
            
        data.sort(key=lambda x: x["seconds"])
        return [item["display"] for item in data]
    except Exception as e:
        return [f"Error: {e}"]

def main():
    events = get_today_calendar()
    if not events:
        return "" # Don't show header if calendar is empty
    
    formatted = "\n".join([f"* {e}" for e in events])
    return f"### 📅 Calendar Events\n{formatted}"

if __name__ == "__main__":
    print(main())