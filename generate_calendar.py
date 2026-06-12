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
    new_cal.add('prodid', '-//Alexandre Economic 3★ Calendar//')
    new_cal.add('version', '2.0')
    new_cal.add('X-WR-CALNAME', 'Economic 3★ EUR/GBP/USD')

    now = datetime.now(pytz.UTC)
    # On garde seulement les 8 prochains jours
    one_week_later = now + timedelta(days=8)

    added = set()

    for component in cal.walk('VEVENT'):
        summary = str(component.get('SUMMARY', ''))
        description = str(component.get('DESCRIPTION', ''))
        dtstart = component.get('DTSTART').dt

        # Filtre strict High Impact
        if not ('High Impact Expected' in description or '***' in summary):
            continue

        # Nettoyage du titre + ajout de la devise
        currency = ''
        if 'USD' in summary or 'United States' in description:
            currency = 'USD'
        elif 'EUR' in summary or 'Eurozone' in description or 'ECB' in summary:
            currency = 'EUR'
        elif 'GBP' in summary or 'United Kingdom' in description:
            currency = 'GBP'

        clean_summary = re.sub(r'\s*\[.*?\]', '', summary).strip()
        clean_summary = re.sub(r'^\d+\s*', '', clean_summary)  # retire heure si présente

        event_title = f"{currency} - {clean_summary}" if currency else clean_summary

        # Évite doublons et sous-événements
        if any(x in clean_summary for x in ['Preliminary', 'Final', 'Revised', 'Flash', 'Actual', 'Previous']):
            continue
        if event_title in added:
            continue
        added.add(event_title)

        # Filtre date : seulement futur + cette semaine
        if dtstart < now or dtstart > one_week_later:
            continue

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

    print(f"✅ {len(added)} événements High Impact générés.")

if __name__ == "__main__":
    main()
