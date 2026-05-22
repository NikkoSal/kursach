from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QFileDialog, QSpinBox, QTextEdit,
                             QGroupBox, QComboBox, QLineEdit, QTabWidget, QProgressBar,
                             QDoubleSpinBox, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, QUrl
from gui.worker import AnalysisWorker
from visual.plotter import CyclonePlotCanvas
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
from visual.map_builder import build_interactive_map
from core.analyzer import haversine_array
import os
import pandas as pd


class CycloneApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Анализ влияния ТЦ на молниевую активность")
        self.resize(1200, 700)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        left_panel = QVBoxLayout()

        file_group = QGroupBox("1. Входные данные")
        file_layout = QVBoxLayout()
        self.btn_load_jma = QPushButton("Выбрать файл ТЦ (JMA)")
        self.lbl_jma = QLabel(".../bst_all.txt")
        self.btn_load_wwlln = QPushButton("Выбрать файл молний (WWLLN)")
        self.lbl_wwlln = QLabel(".../JS202209_U.dat")
        file_layout.addWidget(self.btn_load_jma)
        file_layout.addWidget(self.lbl_jma)
        file_layout.addWidget(self.btn_load_wwlln)
        file_layout.addWidget(self.lbl_wwlln)
        file_group.setLayout(file_layout)

        param_group = QGroupBox("2. Параметры поиска")
        param_layout = QVBoxLayout()

        self.combo_region = QComboBox()
        self.combo_region.addItems(["Японское море", "Южно-Китайское море", "Свой регион"])

        coord_layout = QHBoxLayout()
        col1 = QVBoxLayout()
        self.spin_lat_min = QDoubleSpinBox();
        self.spin_lat_min.setRange(-90, 90)
        self.spin_lat_max = QDoubleSpinBox();
        self.spin_lat_max.setRange(-90, 90)
        col1.addWidget(QLabel("Широта (Мин/Макс):"))
        col1.addWidget(self.spin_lat_min)
        col1.addWidget(self.spin_lat_max)

        col2 = QVBoxLayout()
        self.spin_lon_min = QDoubleSpinBox();
        self.spin_lon_min.setRange(-180, 180)
        self.spin_lon_max = QDoubleSpinBox();
        self.spin_lon_max.setRange(-180, 180)
        col2.addWidget(QLabel("Долгота (Мин/Макс):"))
        col2.addWidget(self.spin_lon_min)
        col2.addWidget(self.spin_lon_max)
        coord_layout.addLayout(col1)
        coord_layout.addLayout(col2)

        self.input_tc_id = QLineEdit()
        self.input_tc_id.setPlaceholderText("Оставьте пустым для автопоиска")

        self.spin_radius = QSpinBox()
        self.spin_radius.setRange(100, 2000)
        self.spin_radius.setValue(500)
        self.spin_radius.setSuffix(" км")

        self.spin_top_zones = QSpinBox()
        self.spin_top_zones.setRange(1, 50)
        self.spin_top_zones.setValue(5)
        self.spin_top_zones.setSuffix(" зон")

        param_layout.addWidget(QLabel("Регион исследования:"))
        param_layout.addWidget(self.combo_region)
        param_layout.addLayout(coord_layout)
        param_layout.addWidget(QLabel("ID циклона:"))
        param_layout.addWidget(self.input_tc_id)
        param_layout.addWidget(QLabel("Радиус зоны влияния:"))
        param_layout.addWidget(self.spin_radius)
        param_layout.addWidget(QLabel("Отображать очагов активности:"))
        param_layout.addWidget(self.spin_top_zones)
        param_group.setLayout(param_layout)

        self.tc_selector_layout = QVBoxLayout()
        self.tc_selector_layout.addWidget(QLabel("<b>Выберите тайфун для просмотра:</b>"))
        self.combo_tc_selector = QComboBox()
        self.combo_tc_selector.setEnabled(False)
        self.combo_tc_selector.currentIndexChanged.connect(self.update_detail_views)
        self.tc_selector_layout.addWidget(self.combo_tc_selector)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.btn_run = QPushButton("CALCULATE IMPACT")
        self.btn_run.setMinimumHeight(50)
        self.btn_run.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; font-size: 14px;")

        left_panel.addWidget(file_group)
        left_panel.addWidget(param_group)
        left_panel.addStretch()
        left_panel.addLayout(self.tc_selector_layout)
        left_panel.addWidget(self.progress_bar)
        left_panel.addWidget(self.btn_run)

        right_panel = QVBoxLayout()
        self.tabs = QTabWidget()

        self.tab_stats = QWidget()
        stats_layout = QVBoxLayout(self.tab_stats)
        self.stats_log = QTextEdit()
        self.stats_log.setReadOnly(True)
        stats_layout.addWidget(self.stats_log)
        self.tabs.addTab(self.tab_stats, "Сводная статистика")

        self.tab_map = QWidget()
        map_layout = QVBoxLayout(self.tab_map)
        self.web_view = QWebEngineView()
        self.web_view.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        self.web_view.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        self.web_view.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        map_layout.addWidget(self.web_view)
        self.tabs.addTab(self.tab_map, "Интерактивная карта")

        self.tab_plot = QWidget()
        plot_layout = QVBoxLayout(self.tab_plot)
        self.plot_canvas = CyclonePlotCanvas(self, width=8, height=6, dpi=100)
        plot_layout.addWidget(self.plot_canvas)
        self.tabs.addTab(self.tab_plot, "График ТЦ")

        self.tab_log = QWidget()
        log_layout = QVBoxLayout(self.tab_log)

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(4)
        self.table_widget.setHorizontalHeaderLabels(
            ["Дата и время", "Координаты (Шир, Долг)", "Давление (гПа)", "Кол-во молний"])
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        log_layout.addWidget(self.table_widget)

        self.btn_export = QPushButton("💾 Экспорт таблицы в CSV")
        self.btn_export.setEnabled(False)
        self.btn_export.clicked.connect(self.export_data)
        log_layout.addWidget(self.btn_export)
        self.tabs.addTab(self.tab_log, "Детализация ТЦ")

        right_panel.addWidget(self.tabs)

        main_layout.addLayout(left_panel, stretch=1)
        main_layout.addLayout(right_panel, stretch=2)

        self.btn_load_jma.clicked.connect(self.load_jma)
        self.btn_load_wwlln.clicked.connect(self.load_wwlln)
        self.btn_run.clicked.connect(self.start_analysis)
        self.combo_region.currentIndexChanged.connect(self.change_region)

        self.jma_path = "data/bst_all.txt"
        self.wwlln_path = "data/JS202209_U.dat"
        self.change_region()

        self.all_results = []
        self.light_df = None

    def change_region(self):
        region = self.combo_region.currentText()
        if region == "Японское море":
            self.spin_lat_min.setValue(35.0);
            self.spin_lat_max.setValue(52.0)
            self.spin_lon_min.setValue(127.0);
            self.spin_lon_max.setValue(142.0)
            self.toggle_coords(False)
        elif region == "Южно-Китайское море":
            self.spin_lat_min.setValue(0.0);
            self.spin_lat_max.setValue(23.0)
            self.spin_lon_min.setValue(100.0);
            self.spin_lon_max.setValue(121.0)
            self.toggle_coords(False)
        else:
            self.toggle_coords(True)

    def toggle_coords(self, enable):
        self.spin_lat_min.setEnabled(enable);
        self.spin_lat_max.setEnabled(enable)
        self.spin_lon_min.setEnabled(enable);
        self.spin_lon_max.setEnabled(enable)

    def load_jma(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите файл JMA", "", "Text Files (*.txt);;All Files (*)")
        if path:
            self.jma_path = path;
            self.lbl_jma.setText(path.split('/')[-1])

    def load_wwlln(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выберите файл WWLLN", "",
                                              "Data Files (*.dat *.loc);;All Files (*)")
        if path:
            self.wwlln_path = path;
            self.lbl_wwlln.setText(path.split('/')[-1])

    def start_analysis(self):
        self.btn_run.setEnabled(False)
        self.progress_bar.setValue(0)
        self.stats_log.clear()
        self.combo_tc_selector.clear()
        self.combo_tc_selector.setEnabled(False)
        self.btn_export.setEnabled(False)
        self.tabs.setCurrentIndex(0)

        tc_id = self.input_tc_id.text().strip()
        radius = self.spin_radius.value()
        coords = (
        self.spin_lat_min.value(), self.spin_lat_max.value(), self.spin_lon_min.value(), self.spin_lon_max.value())

        self.worker = AnalysisWorker(self.jma_path, self.wwlln_path, tc_id, radius, coords)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.log.connect(self.stats_log.append)
        self.worker.error.connect(self.show_error)
        self.worker.finished.connect(self.process_all_results)
        self.worker.start()

    def show_error(self, err_msg):
        self.stats_log.append(f"ОШИБКА: {err_msg}")
        self.btn_run.setEnabled(True)

    def process_all_results(self, data):
        self.all_results, self.light_df = data
        self.btn_export.setEnabled(True)

        self.stats_log.append(f"Общее количество молний в заданном регионе: {len(self.light_df)}")

        self.combo_tc_selector.blockSignals(True)
        self.combo_tc_selector.clear()

        for item in self.all_results:
            tc_id = item['tc_id']

            self.stats_log.append(f"\nАнализ тропического циклона (ID: {tc_id})")
            self.stats_log.append("Общая активность:")
            self.stats_log.append(f"Зафиксировано молний в зоне влияния ТЦ: {item['total_tc']}")
            self.stats_log.append(f" Доля ТЦ от региональной активности: {item['perc_total']:.1f}%")
            self.stats_log.append("\nПиковые дни грозовой активности:")

            for line in item['peaks']:
                self.stats_log.append(line)

            self.combo_tc_selector.addItem(f"Тайфун {tc_id} ({item['total_tc']} молний)")

        self.combo_tc_selector.blockSignals(False)
        self.combo_tc_selector.setEnabled(True)
        self.btn_run.setEnabled(True)

        self.update_detail_views()
    def update_detail_views(self):
        current_idx = self.combo_tc_selector.currentIndex()
        if current_idx < 0 or current_idx >= len(self.all_results):
            return

        selected_df = self.all_results[current_idx]['track_df']

        active = selected_df[selected_df['lightning_count'] > 0]
        self.table_widget.setRowCount(0)
        self.table_widget.setSortingEnabled(False)

        if active.empty:
            self.table_widget.setRowCount(1)
            self.table_widget.setItem(0, 0, QTableWidgetItem("Молний не найдено"))
        else:
            self.table_widget.setRowCount(len(active))
            for row_idx, (_, row) in enumerate(active.iterrows()):
                dt_str = row['datetime'].strftime("%Y-%m-%d %H:00")
                coord_str = f"{row['lat']:.1f}, {row['lon']:.1f}"

                item_dt = QTableWidgetItem(dt_str)
                item_coord = QTableWidgetItem(coord_str)
                item_press = QTableWidgetItem();
                item_press.setData(Qt.ItemDataRole.DisplayRole, int(row['pressure']))
                item_light = QTableWidgetItem();
                item_light.setData(Qt.ItemDataRole.DisplayRole, int(row['lightning_count']))

                self.table_widget.setItem(row_idx, 0, item_dt)
                self.table_widget.setItem(row_idx, 1, item_coord)
                self.table_widget.setItem(row_idx, 2, item_press)
                self.table_widget.setItem(row_idx, 3, item_light)

            self.table_widget.setSortingEnabled(True)
            self.table_widget.sortItems(3, Qt.SortOrder.DescendingOrder)

        self.plot_canvas.plot_data(selected_df)

        radius = self.spin_radius.value()
        top_zones = self.spin_top_zones.value()
        map_filepath = build_interactive_map(selected_df, self.light_df, radius, top_zones)

        abs_path = os.path.abspath(map_filepath)
        self.web_view.load(QUrl.fromLocalFile(abs_path))

    def export_data(self):
        current_idx = self.combo_tc_selector.currentIndex()
        if current_idx < 0: return

        selected_df = self.all_results[current_idx]['track_df']
        tc_id = self.all_results[current_idx]['tc_id']

        filepath, _ = QFileDialog.getSaveFileName(self, "Сохранить результаты", f"cyclone_{tc_id}.csv",
                                                  "CSV Files (*.csv)")
        if filepath:
            export_df = selected_df[['datetime', 'lat', 'lon', 'pressure', 'lightning_count']]
            export_df.to_csv(filepath, index=False, sep=';')
            self.stats_log.append(f"Успешно сохранено: {filepath}")