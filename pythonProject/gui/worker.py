from PyQt6.QtCore import QThread, pyqtSignal
from core.parsers import parse_jma, parse_wwlln
from core.analyzer import interpolate_track, analyze_lightning_impact
import pandas as pd


class AnalysisWorker(QThread):
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, jma_file, wwlln_file, tc_id, radius, coords):
        super().__init__()
        self.jma_file = jma_file;
        self.wwlln_file = wwlln_file
        self.tc_id = tc_id;
        self.radius = radius;
        self.coords = coords

    def run(self):
        try:
            self.log.emit("1. Чтение файлов данных...")
            self.progress.emit(5)

            tc_df = parse_jma(self.jma_file)
            full_light_df = parse_wwlln(self.wwlln_file)

            self.log.emit("2. Фильтрация молний по региону...")
            lat_min, lat_max, lon_min, lon_max = self.coords
            region_light_mask = (full_light_df['lat'] >= lat_min) & (full_light_df['lat'] <= lat_max) & \
                                (full_light_df['lon'] >= lon_min) & (full_light_df['lon'] <= lon_max)

            light_df = full_light_df[region_light_mask]

            self.progress.emit(10)
            self.log.emit("3. Поиск тайфунов...")

            target_ids = []
            if self.tc_id:
                target_ids.append(self.tc_id)
            else:
                min_date = light_df['datetime'].min()
                max_date = light_df['datetime'].max()
                time_mask = (tc_df['datetime'] >= min_date) & (tc_df['datetime'] <= max_date)
                possible_tcs = tc_df[time_mask]
                region_mask = (possible_tcs['lat'] >= lat_min) & (possible_tcs['lat'] <= lat_max) & \
                              (possible_tcs['lon'] >= lon_min) & (possible_tcs['lon'] <= lon_max)
                tcs_in_region = possible_tcs[region_mask]

                if tcs_in_region.empty:
                    self.error.emit("В выбранном море и в даты файла молний циклонов не найдено!")
                    return
                target_ids = tcs_in_region['tc_id'].unique().tolist()
                self.log.emit(f"Найдено тайфунов: {len(target_ids)} шт.")

            all_results = []
            total_file_lightnings = len(light_df)
            progress_step = 80 / len(target_ids) if target_ids else 80
            current_progress = 10

            for i, tid in enumerate(target_ids):
                self.log.emit(f"\nОбработка тайфуна {tid}")

                my_cyclone = tc_df[tc_df['tc_id'] == tid]
                if my_cyclone.empty: continue

                my_cyclone_hourly = interpolate_track(my_cyclone, freq='1h')

                result_track, caught_indices = analyze_lightning_impact(
                    my_cyclone_hourly, light_df, radius_km=self.radius, time_window_hours=0.5
                )

                unique_tc_lightnings = light_df.loc[list(caught_indices)]
                total_tc_lightnings = len(unique_tc_lightnings)
                perc_total = (total_tc_lightnings / total_file_lightnings * 100) if total_file_lightnings > 0 else 0

                peak_days_info = []
                if total_tc_lightnings > 0:
                    daily_tc = unique_tc_lightnings.groupby(unique_tc_lightnings['datetime'].dt.date).size()
                    daily_total = light_df.groupby(light_df['datetime'].dt.date).size()
                    top_days = daily_tc.nlargest(3)
                    for day, count in top_days.items():
                        total_in_day = daily_total.get(day, 0)
                        perc_day = (count / total_in_day * 100) if total_in_day > 0 else 0
                        peak_days_info.append(f"{day.strftime('%d.%m.%Y')}: {total_in_day} региональных молний (вклад ТЦ: {perc_day:.1f}%, {count} шт.)")


                all_results.append({
                    'tc_id': tid,
                    'track_df': result_track,
                    'total_tc': total_tc_lightnings,
                    'perc_total': perc_total,
                    'peaks': peak_days_info
                })

                current_progress += progress_step
                self.progress.emit(int(current_progress))

            self.progress.emit(100)
            self.log.emit("\nРасчёт завершен!")
            self.finished.emit((all_results, light_df))

        except Exception as e:
            self.error.emit(f"Произошла критическая ошибка: {str(e)}")