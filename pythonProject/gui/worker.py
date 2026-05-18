from PyQt6.QtCore import QThread, pyqtSignal
from core.parsers import parse_jma, parse_wwlln
from core.analyzer import interpolate_track, analyze_lightning_impact


class AnalysisWorker(QThread):
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, jma_file, wwlln_file, tc_id, radius, coords):
        super().__init__()
        self.jma_file = jma_file
        self.wwlln_file = wwlln_file
        self.tc_id = tc_id
        self.radius = radius
        self.coords = coords
    def run(self):
        try:
            self.log.emit("1. Чтение файлов данных...")
            self.progress.emit(10)

            tc_df = parse_jma(self.jma_file)
            light_df = parse_wwlln(self.wwlln_file)

            self.log.emit("2. Поиск подходящего циклона...")
            self.progress.emit(30)

            if not self.tc_id:
                self.log.emit("ID не указан.")

                min_date = light_df['datetime'].min()
                max_date = light_df['datetime'].max()

                time_mask = (tc_df['datetime'] >= min_date) & (tc_df['datetime'] <= max_date)
                possible_tcs = tc_df[time_mask]

                lat_min, lat_max, lon_min, lon_max = self.coords
                region_mask = (possible_tcs['lat'] >= lat_min) & (possible_tcs['lat'] <= lat_max) & \
                              (possible_tcs['lon'] >= lon_min) & (possible_tcs['lon'] <= lon_max)

                tcs_in_region = possible_tcs[region_mask]

                if tcs_in_region.empty:
                    self.error.emit("В выбранном море и в даты файла молний циклонов не найдено!")
                    return

                self.tc_id = tcs_in_region['tc_id'].value_counts().index[0]
                self.log.emit(f"Атоматически выбран тайфун: ID {self.tc_id}")

            my_cyclone = tc_df[tc_df['tc_id'] == self.tc_id]
            if my_cyclone.empty:
                self.error.emit(f"Циклон с ID {self.tc_id} не найден в базе!")
                return

            self.log.emit("3. Интерполяция трека")
            self.progress.emit(50)
            my_cyclone_hourly = interpolate_track(my_cyclone, freq='1h')

            self.log.emit(f"4. Поиск молний в радиусе {self.radius} км...")
            self.progress.emit(70)

            result = analyze_lightning_impact(my_cyclone_hourly, light_df, radius_km=self.radius, time_window_hours=1)

            self.progress.emit(100)
            self.log.emit("Расчёт заверешен!")

            self.finished.emit((result, light_df))

        except Exception as e:
            self.error.emit(f"Произошла ошибка: {str(e)}")