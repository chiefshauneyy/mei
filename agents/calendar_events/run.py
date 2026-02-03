import subprocess

def get_today_calendar():
    # This script targets only standard calendars and ignores the hidden 'Reminders' overlay
    script = '''
    set midnight to (current date) + 1 * days
    set time of midnight to 0
    set output to ""
    
    tell application "Calendar"
        -- We only target calendars that aren't subscription-based or virtual reminder-mirrors
        set validCalendars to every calendar whose name is not "Reminders" and name is not "Found in Apps" and name is not "Birthdays" and name is not "US Holidays"
        
        repeat with theCal in validCalendars
            set todayEvents to (events of theCal whose start date is less than midnight and start date is greater than or equal to (current date))
            
            repeat with e in todayEvents
                -- This is the 'Silver Bullet': Reminders disguised as events usually 
                -- lack certain properties or belong to specific hidden types.
                -- We only take events that are not 'All Day' and have a summary.
                if allday event of e is false then
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
            
            # CRITICAL FILTER: If the event name is EXACTLY the same as your 
            # common reminders, we can skip it here as a safety net.
            if name in ["Gym", "Apply skincare", "Make bed"]:
                continue
                
            data.append({"display": f"{name} ({display_time})", "seconds": int(seconds)})
            
        data.sort(key=lambda x: x["seconds"])
        return [item["display"] for item in data]
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