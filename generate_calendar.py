import requests
from icalendar import Calendar, Event
from datetime import datetime, timedelta
import pytz
import re
import os

ICS_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.ics"

def main():
    response = requests.get(ICS_URL)
    response.raise_for_status()
    cal = Calendar.from_ical(response.content)

    new_cal = Calendar()
    new_cal.add('prodid', '-//Alexandre Economic 3★//')
    new_cal.add('version', '2.0')
    new_cal.add('X-WR-CALNAME', 'Economic 3★ EUR/GBP/USD')

    now = datetime.now(pytz.UTC)
    one_week_later = now + timedelta(days=8)

    added = set()

    for component in cal.walk('VEVENT'):
        summary = str(component.get('SUMMARY', ''))
        description = str(component.get('DESCRIPTION', ''))
        dtstart = component.get('DTSTART').dt

        # Seulement High Impact (3 étoiles)
        if not ('High Impact Expected' in description or '***' in summary):
            continue

        # Seulement EUR, GBP, USD
        if not any(x in summary.upper() or x in description.upper() for x in ['USD', 'EUR', 'GBP', 'UNITED STATES', 'EUROZONE', 'UNITED KINGDOM', 'ECB', 'BOE', 'FED']):
            continue

        # Pas d'événements passés
        if dtstart < now:
            continue

        # Nettoyage + devise dans le titre
        clean_summary = re.sub(r'\s*\[.*?\]', '', summary).strip()
        clean_summary = re.sub(r'^\d+\s*', '', clean_summary)

        currency = 'USD' if any(x in summary.upper() or x in description.upper() for x in ['USD', 'UNITED STATES', 'FED']) else \
                   'EUR' if any(x in summary.upper() or x in description.upper() for x in ['EUR', 'EUROZONE', 'ECB']) else \
                   'GBP' if any(x in summary.upper() or x in description.upper() for x in ['GBP', 'UNITED KINGDOM', 'BOE']) else ''

        event_title = f"{currency} - {clean_summary}" if currency else clean_summary

        # Évite doublons et sous-versions
        if any(x in clean_summary for x in ['Preliminary', 'Final', 'Revised', 'Flash', 'Actual', 'Previous']):
            continue
        if event_title in added:
            continue
        added.add(event_title)

        event = Event()
        event.add('SUMMARY', event_title)
        event.add('DTSTART', dtstart)
        event.add('DTEND', component.get('DTEND').dt if component.get('DTEND') else dtstart + timedelta(minutes=30))
        event.add('DESCRIPTION', description + "\n\nSource: Forex Factory")
        event.add('UID', component.get('UID'))

        # Alertes
        event.add('VALARM', {'ACTION': 'DISPLAY', 'DESCRIPTION': 'Dans 15 minutes', 'TRIGGER': '-PT15M'})
        event.add('VALARM', {'ACTION': 'DISPLAY', 'DESCRIPTION': 'Maintenant', 'TRIGGER': 'PT0M'})

        new_cal.add_component(event)

    os.makedirs('public', exist_ok=True)
    with open('public/economic-3stars.ics', 'wb') as f:
        f.write(new_cal.to_ical())

    print(f"✅ {len(added)} événements 3★ (EUR/GBP/USD) générés.")

if __name__ == "__main__":
    main()
