import matplotlib

matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates


class CyclonePlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=8, height=5.5, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax1 = self.fig.add_subplot(111)
        self.ax2 = self.ax1.twinx()
        super().__init__(self.fig)
        self.setParent(parent)

    def plot_data(self, df):
        self.ax1.clear()
        self.ax2.clear()

        if df['lightning_count'].sum() == 0:
            self.ax1.text(0.5, 0.5, "Молний не зафиксировано",
                          horizontalalignment='center', verticalalignment='center', fontsize=14)
            self.draw()
            return

        active_df = df[df['lightning_count'] > 0]
        start_idx = max(0, active_df.index[0] - 12)
        end_idx = min(len(df) - 1, active_df.index[-1] + 12)
        plot_df = df.iloc[start_idx:end_idx]

        times = plot_df['datetime']
        lightnings = plot_df['lightning_count']
        pressure = plot_df['pressure']

        self.ax1.bar(times, lightnings, color='#FF6666', edgecolor='#CC0000', width=0.035, alpha=0.8,
                     label='Кол-во вспышек')
        self.ax1.set_ylabel('Количество вспышек (шт/час)', color='#CC0000', fontsize=12, fontweight='bold')
        self.ax1.tick_params(axis='y', labelcolor='#CC0000')

        self.ax2.plot(times, pressure, color='#0033CC', linewidth=2.5, marker='o', markersize=5,
                      label='Давление в центре')
        self.ax2.yaxis.set_label_position("right")
        self.ax2.yaxis.tick_right()
        self.ax2.set_ylabel('Атмосферное давление (гПа)', color='#0033CC', fontsize=12, fontweight='bold')
        self.ax2.invert_yaxis()
        self.ax2.tick_params(axis='y', labelcolor='#0033CC')

        self.ax1.set_xlabel('Дата и время (UTC)', fontsize=12, fontweight='bold')
        self.ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m %H:00'))
        self.fig.autofmt_xdate(rotation=45)
        self.ax1.grid(True, linestyle='--', alpha=0.6)

        tc_id = df['tc_id'].iloc[0]
        self.ax1.set_title(f"Динамика интенсивности тайфуна (ID: {tc_id})", fontsize=14, fontweight='bold', pad=15)

        lines_1, labels_1 = self.ax1.get_legend_handles_labels()
        lines_2, labels_2 = self.ax2.get_legend_handles_labels()

        self.ax1.legend(lines_1 + lines_2, labels_1 + labels_2,
                        loc='upper center', bbox_to_anchor=(0.5, -0.27),
                        ncol=2, framealpha=1)

        self.fig.subplots_adjust(bottom=0.25)
        self.draw()