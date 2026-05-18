import numpy as np
import pandas as pd


def haversine_array(lat1, lon1, lat2_array, lon2_array):

    lat1, lon1, lat2_array, lon2_array = map(np.radians, [lat1, lon1, lat2_array, lon2_array])

    dlat = lat2_array - lat1
    dlon = lon2_array - lon1

    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2_array) * np.sin(dlon / 2.0) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    km = 6371.0 * c
    return km


def interpolate_track(tc_track, freq='1H'):

    df = tc_track.copy()
    df = df.set_index('datetime')
    df = df[~df.index.duplicated(keep='first')]

    resampled = df.resample(freq).asfreq()

    resampled['lat'] = resampled['lat'].interpolate(method='linear')
    resampled['lon'] = resampled['lon'].interpolate(method='linear')
    resampled['pressure'] = resampled['pressure'].interpolate(method='linear')
    resampled['tc_id'] = resampled['tc_id'].ffill()

    return resampled.reset_index()


def analyze_lightning_impact(tc_track, lightning_df, radius_km=500, time_window_hours=1):

    counts = []

    for _, row in tc_track.iterrows():
        t = row['datetime']
        lat = row['lat']
        lon = row['lon']

        t_delta = pd.Timedelta(hours=time_window_hours)
        time_mask = (lightning_df['datetime'] >= t - t_delta) & (lightning_df['datetime'] <= t + t_delta)
        subset = lightning_df[time_mask]

        if subset.empty:
            counts.append(0)
            continue

        distances = haversine_array(lat, lon, subset['lat'].values, subset['lon'].values)
        count = np.sum(distances <= radius_km)
        counts.append(count)

    result_track = tc_track.copy()
    result_track['lightning_count'] = counts
    return result_track