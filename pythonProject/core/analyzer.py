import numpy as np
import pandas as pd
from scipy.interpolate import pchip_interpolate

def haversine_array(lat1, lon1, lat2_array, lon2_array):
    lat1, lon1, lat2_array, lon2_array = map(np.radians, [lat1, lon1, lat2_array, lon2_array])
    dlat = lat2_array - lat1
    dlon = lon2_array - lon1
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1) * np.cos(lat2_array) * np.sin(dlon / 2.0) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    km = 6371.0 * c
    return km


def interpolate_track(tc_track, freq='1h'):
    df = tc_track.copy()

    df = df.sort_values(by='datetime')
    df = df[~df['datetime'].duplicated(keep='first')]

    base_times = (df['datetime'] - df['datetime'].iloc[0]).dt.total_seconds() / 3600.0

    start_time = df['datetime'].min()
    end_time = df['datetime'].max()
    new_dates = pd.date_range(start=start_time, end=end_time, freq=freq)

    new_times = (new_dates - start_time).total_seconds() / 3600.0

    valid_points = df['lat'].dropna().shape[0]

    resampled = pd.DataFrame({'datetime': new_dates})

    if valid_points >= 3:
        resampled['lat'] = pchip_interpolate(base_times, df['lat'].values, new_times)
        resampled['lon'] = pchip_interpolate(base_times, df['lon'].values, new_times)
        resampled['pressure'] = pchip_interpolate(base_times, df['pressure'].values, new_times)
    else:
        resampled['lat'] = np.interp(new_times, base_times, df['lat'].values)
        resampled['lon'] = np.interp(new_times, base_times, df['lon'].values)
        resampled['pressure'] = np.interp(new_times, base_times, df['pressure'].values)

    resampled['tc_id'] = df['tc_id'].iloc[0]

    return resampled


def analyze_lightning_impact(tc_track, lightning_df, radius_km=500, time_window_hours=0.5):
    counts = []
    caught_indices = set()
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
        in_radius = distances <= radius_km

        count = np.sum(in_radius)
        counts.append(count)

        if count > 0:
            caught_indices.update(subset[in_radius].index.tolist())

    result_track = tc_track.copy()
    result_track['lightning_count'] = counts
    return result_track, caught_indices