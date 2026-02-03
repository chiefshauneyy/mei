import subprocess

def get_today_calendar():
    script = '''
    -- Set "startOfToday" to 00:00:00 of the current day
    set startOfToday to (current date)
    set time of startOfToday to 0
    
    -- Set "endOfToday" to 23:59:59 of the current day
    set endOfToday to startOfToday + (24 * hours) - 1
    
    set output to ""
    
    tell application "Calendar"
        set allCals to every calendar whose name is not "Scheduled Reminders" and name is not "Siri Suggestions" and name is not "Birthdays" and name is not "US Holidays"
        
        repeat with theCal in allCals
            -- Get events that fall within the 24-hour window of today
            set todayEvents to (events of theCal whose start date is less than or equal to endOfToday and start date is greater than or equal to startOfToday)
            
            repeat with e in todayEvents
                set eventName to summary of e
                set eventDate to start date of e
                set isAllDay to allday event of e
                
                if isAllDay then
                    set displayTime to " (All Day)"
                    set sortTime to -1 -- All-day at the very top
                else
                    set hr to hours of eventDate
                    set mn to minutes of eventDate
                    set ampm to "AM"
                    if hr ≥ 12 then set ampm to "PM"
                    if hr > 12 then set hr to hr - 12
                    if hr = 0 then set hr to 12
                    set mnStr to mn as string
                    if (length of mnStr) < 2 then set mnStr to "0" & mnStr
                    set displayTime to " (" & hr & ":" & mnStr & " " & ampm & ")"
                    set sortTime to time of eventDate
                end if
                
                set output to output & eventName & "|" & sortTime & "|" & displayTime & ";"
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
            data.append({"display": f"{name}{display_time}", "seconds": int(seconds)})
            
        # Deduplicate and Sort
        unique_results = {d['display']: d for d in data}.values()
        final_list = sorted(unique_results, key=lambda x: x["seconds"])
        return [item["display"] for item in final_list]
    except Exception:
        return []

def main():
    events = get_today_calendar()
    if not events:
        return "" 
    
    formatted = "\n".join([f"* {e}" for e in events])
    return f"### 📅 Calendar Events\n{formatted}"

if __name__ == "__main__":
    print(main())