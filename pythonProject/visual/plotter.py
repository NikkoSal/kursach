import matplotlib

matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates


class CyclonePlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=8, height=5.5, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax1 = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)

    def plot_data(self, df):
        self.ax1.clear()

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

        self.ax1.bar(times, lightnings, color='#FF6666', edgecolor='#CC0000', width=0.035, alpha=0.9)
        self.ax1.set_ylabel('Количество вспышек (шт/час)', color='#CC0000', fontsize=13, fontweight='bold')
        self.ax1.tick_params(axis='y', labelcolor='#CC0000', labelsize=11)

        self.ax1.set_xlabel('Дата и время (UTC)', fontsize=10, fontweight='bold')
        self.ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m %H:00'))
        self.fig.autofmt_xdate(rotation=45)
        self.ax1.grid(True, linestyle='--', alpha=0.6)

        tc_id = df['tc_id'].iloc[0]
        self.ax1.set_title(f"Распределение молниевой активности (Тайфун ID: {tc_id})", fontsize=15, fontweight='bold',
                           pad=15)

        total_light = int(df['lightning_count'].sum())
        max_hour = int(df['lightning_count'].max())

        stats_text = (
            f"Всего молний в радиусе ТЦ: {total_light} шт.  |  "
            f"Абсолютный пик активности: {max_hour} шт/час"
        )

        strict_style = dict(
            boxstyle='square,pad=0.5',
            facecolor='white',
            edgecolor='#B0B0B0',
            linewidth=1.2,
            alpha=0.9
        )

        self.ax1.text(0.5, -0.35, stats_text, transform=self.ax1.transAxes,
                      horizontalalignment='center', fontsize=11, color='#333333',
                      bbox=strict_style)

        self.fig.subplots_adjust(bottom=0.3)
        self.draw()