import folium
import os


def build_interactive_map(tc_track, light_df, radius_km, top_zones=5, output_filename="temp_map.html"):
    center_lat = tc_track['lat'].mean()
    center_lon = tc_track['lon'].mean()

    m = folium.Map(location=[center_lat, center_lon], zoom_start=5)

    track_coords = list(zip(tc_track['lat'], tc_track['lon']))
    folium.PolyLine(track_coords, color="cyan", weight=2, opacity=0.8).add_to(m)

    top_phases = tc_track.nlargest(top_zones, 'lightning_count')

    top_phases = top_phases[top_phases['lightning_count'] > 0]

    for _, row in top_phases.iterrows():
        popup_text = f"<b>МАКСИМУМ АКТИВНОСТИ</b><br>Время: {row['datetime']}<br>Давление: {row['pressure']} гПа<br>Молний: {row['lightning_count']}"

        folium.Circle(
            location=[row['lat'], row['lon']],
            radius=radius_km * 1000,
            color='#FF0000',
            weight=3,
            fill=True,
            fill_color='red',
            fill_opacity=0.1,
            tooltip=popup_text
        ).add_to(m)

        folium.CircleMarker(location=[row['lat'], row['lon']], radius=4, color='red', fill=True).add_to(m)


    start_time = tc_track['datetime'].min()
    end_time = tc_track['datetime'].max()

    relevant_lightning = light_df[(light_df['datetime'] >= start_time) & (light_df['datetime'] <= end_time)]

    max_dots = 2000
    if len(relevant_lightning) > max_dots:
        draw_lightning = relevant_lightning.sample(n=max_dots, random_state=42)
    else:
        draw_lightning = relevant_lightning

    for _, row in draw_lightning.iterrows():
        folium.CircleMarker(
            location=[row['lat'], row['lon']],
            radius=1,
            color='yellow',
            fill=True,
            fill_color='yellow',
            fill_opacity=0.8
        ).add_to(m)

    m.fit_bounds(track_coords)
    m.save(output_filename)

    return os.path.abspath(output_filename)