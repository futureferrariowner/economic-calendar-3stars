import requests
from icalendar import Calendar, Event
from datetime import datetime, timedelta
import pytz
import re

# Lien direct Forex Factory (This Week ICS)
ICS_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.ics"

def main():
    response = requests.get(ICS_URL)
    response.raise_for_status()
    cal = Calendar.from_ical(response.content)

    new_cal = Calendar()
    new_cal.add('prodid', '-//My Economic 3★ Calendar//')
    new_cal.add('version', '2.0')

    now = datetime.now(pytz.UTC)
    one_week = now + timedelta(days=8)

    for component in cal.walk('VEVENT'):
        summary = str(component.get('SUMMARY', ''))
        description = str(component.get('DESCRIPTION', ''))
        
        # Filtre High Impact (3 étoiles)
        if 'High Impact Expected' not in description and '***' not in summary:
            continue

        # Un seul événement par annonce (évite les sous-événements)
        if any(x in summary for x in ['Preliminary', 'Final', 'Revised', 'Flash']):
            continue  # On garde seulement la version principale

        event = Event()
        event.add('SUMMARY', re.sub(r'\s*\[.*?\]', '', summary).strip())  # Nettoie
        event.add('DTSTART', component.get('DTSTART').dt)
        event.add('DTEND', component.get('DTEND').dt if component.get('DTEND') else component.get('DTSTART').dt)
        event.add('DESCRIPTION', description + "\n\nSource: Forex Factory")
        event.add('UID', component.get('UID'))

        # Alertes : 15 min avant + à l'heure
        event.add('VALARM', {
            'ACTION': 'DISPLAY',
            'DESCRIPTION': 'Événement dans 15 minutes',
            'TRIGGER': '-PT15M'
        })
        event.add('VALARM', {
            'ACTION': 'DISPLAY',
            'DESCRIPTION': 'Événement maintenant',
            'TRIGGER': 'PT0M'
        })

        new_cal.add_component(event)

    # Sauvegarde
    with open('public/economic-3stars.ics', 'wb') as f:
        f.write(new_cal.to_ical())

    print("Calendrier généré avec succès !")

if __name__ == "__main__":
    main()
