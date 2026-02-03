import subprocess

def get_today_calendar():
    script = '''
    set midnight to (current date) + 1 * days
    set time of midnight to 0
    set output to ""
    
    tell application "Calendar"
        -- We filter out calendars usually used for reminders or 'Siri Found'
        set theCalendars to every calendar whose name is not "Reminders" and name is not "Found in Natural Language"
        
        repeat with theCal in theCalendars
            -- Only get actual events
            set todayEvents to (events of theCal whose start date is less than midnight and start date is greater than or equal to (current date))
            
            repeat with e in todayEvents
                set eventName to summary of e
                set eventDate to start date of e
                
                -- Skip if it's an all-day event or missing a summary (optional)
                if allday event of e is false then
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
                end if
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
            
        # Remove any accidental duplicates between calendars
        seen = set()
        unique_data = []
        for d in data:
            if d["display"] not in seen:
                unique_data.append(d)
                seen.add(d["display"])
                
        unique_data.sort(key=lambda x: x["seconds"])
        return [item["display"] for item in unique_data]
    except Exception as e:
        return [f"Error: {e}"]

def main():
    events = get_today_calendar()
    if not events:
        return "" 
    
    formatted = "\n".join([f"* {e}" for e in events])
    return f"### 📅 Calendar Events\n{formatted}"

if __name__ == "__main__":
    print(main())