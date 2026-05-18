import pandas as pd
from datetime import datetime


def parse_jma(filepath):
    data = []
    current_cyclone_id = None

    with open(filepath, 'r') as file:
        for line in file:
            parts = line.split()
            if not parts:
                continue

            if parts[0] == '66666':
                current_cyclone_id = parts[1]
            else:
                date_str = parts[0]
                lat = float(parts[3]) / 10.0  # Широта
                lon = float(parts[4]) / 10.0  # Долгота
                pressure = int(parts[5])  # Давление

                year_part = int(date_str[:2])
                year = 1900 + year_part if year_part > 50 else 2000 + year_part
                month = int(date_str[2:4])
                day = int(date_str[4:6])
                hour = int(date_str[6:8])

                dt = datetime(year, month, day, hour)

                data.append({
                    'tc_id': current_cyclone_id,
                    'datetime': dt,
                    'lat': lat,
                    'lon': lon,
                    'pressure': pressure
            })
    return pd.DataFrame(data)


def parse_wwlln(filepath):

    df = pd.read_csv(filepath, sep=r'\s+', header=None, usecols=[0, 1, 2, 3, 4, 5, 6, 7],
                     names=['year', 'month', 'day', 'hour', 'minute', 'second', 'lat', 'lon'])

    df['second'] = df['second'].astype(int)

    df['datetime'] = pd.to_datetime(df[['year', 'month', 'day', 'hour', 'minute', 'second']])

    return df[['datetime', 'lat', 'lon']]