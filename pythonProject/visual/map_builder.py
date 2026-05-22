import folium
import os
import pandas as pd
from core.analyzer import haversine_array


def build_interactive_map(tc_track, light_df, radius_km, top_zones=5, output_filename="temp_map.html"):
    center_lat = tc_track['lat'].mean()
    center_lon = tc_track['lon'].mean()

    m = folium.Map(location=[center_lat, center_lon], zoom_start=5)

    track_coords = list(zip(tc_track['lat'], tc_track['lon']))
    folium.PolyLine(track_coords, color="#0000CC", weight=3, opacity=0.9, tooltip="Трек циклона").add_to(m)

    top_phases = tc_track.nlargest(top_zones, 'lightning_count')
    top_phases = top_phases[top_phases['lightning_count'] > 0]

    palette = ['#FF0000', '#FF8C00', '#8A2BE2', '#00BFFF', '#00FA9A',
               '#FF1493', '#FFFF00', '#FF00FF', '#32CD32', '#DC143C']

    zone_index = 0

    for _, row in top_phases.iterrows():
        zone_color = palette[zone_index % len(palette)]

        popup_text = f"<b>Зона активности №{zone_index + 1}</b><br>Время: {row['datetime']}<br>Молний: {row['lightning_count']}"

        folium.Circle(
            location=[row['lat'], row['lon']],
            radius=radius_km * 1000,
            color=zone_color,
            weight=2,
            dash_array='5, 5',
            fill=True,
            fill_color=zone_color,
            fill_opacity=0.05,
            tooltip=popup_text
        ).add_to(m)

        folium.CircleMarker(location=[row['lat'], row['lon']], radius=4, color='black', fill=True,
                            fill_color=zone_color).add_to(m)

        t = row['datetime']
        t_delta = pd.Timedelta(hours=0.5)
        time_mask = (light_df['datetime'] >= t - t_delta) & (light_df['datetime'] <= t + t_delta)
        subset = light_df[time_mask]

        if not subset.empty:
            distances = haversine_array(row['lat'], row['lon'], subset['lat'].values, subset['lon'].values)
            caught_idx = subset[distances <= radius_km].index.tolist()

            if caught_idx:
                valid_lightnings = light_df.loc[caught_idx]

                if len(valid_lightnings) > 2000:
                    valid_lightnings = valid_lightnings.sample(n=2000, random_state=42)

                for _, l_row in valid_lightnings.iterrows():
                    folium.CircleMarker(
                        location=[l_row['lat'], l_row['lon']],
                        radius=2,
                        color=zone_color,
                        fill=True,
                        fill_color=zone_color,
                        fill_opacity=0.9
                    ).add_to(m)

        zone_index += 1

    legend_html = '''
     <div style="position: fixed; 
                 bottom: 50px; right: 50px; width: 220px; height: 100px; 
                 background-color: white; border:2px solid grey; z-index:9999; font-size:14px;
                 padding: 10px; border-radius: 5px; opacity: 0.9;">
         <b>Обозначения:</b><br>
         <i style="background:#0000CC; width: 15px; height: 3px; float: left; margin-top: 8px; margin-right: 8px;"></i> Трек циклона<br>
         <i style="border: 2px dashed #000; border-radius: 50%; width: 12px; height: 12px; float: left; margin-top: 4px; margin-right: 10px;"></i> Зоны активности<br>
         <i style="background:linear-gradient(to right, red, orange, purple); border-radius: 50%; width: 10px; height: 10px; float: left; margin-top: 6px; margin-right: 12px;"></i> Молнии<br>
      </div>
     '''
    m.get_root().html.add_child(folium.Element(legend_html))

    m.fit_bounds(track_coords)
    m.save(output_filename)
    return os.path.abspath(output_filename)