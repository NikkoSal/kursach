import numpy as np
import pandas as pd
import scipy

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
    df = df.set_index('datetime')
    df = df[~df.index.duplicated(keep='first')]
    resampled = df.resample(freq).asfreq()

    valid_points = df['lat'].dropna().shape[0]

    if valid_points >= 4:
        try:
            resampled['lat'] = resampled['lat'].interpolate(method='spline', order=3)
            resampled['lon'] = resampled['lon'].interpolate(method='spline', order=3)
            resampled['pressure'] = resampled['pressure'].interpolate(method='spline', order=3)
        except ImportError:
            resampled['lat'] = resampled['lat'].interpolate(method='linear')
            resampled['lon'] = resampled['lon'].interpolate(method='linear')
            resampled['pressure'] = resampled['pressure'].interpolate(method='linear')
    else:
        resampled['lat'] = resampled['lat'].interpolate(method='linear')
        resampled['lon'] = resampled['lon'].interpolate(method='linear')
        resampled['pressure'] = resampled['pressure'].interpolate(method='linear')

    resampled['tc_id'] = resampled['tc_id'].ffill()
    return resampled.reset_index()


def analyze_lightning_impact(tc_track, lightning_df, radius_km=500, time_window_hours=3.0):
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