import matplotlib

matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
import pandas as pd


class CyclonePlotCanvas(FigureCanvas):
    def __init__(self, parent=None, width=8, height=5, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.ax1 = self.fig.add_subplot(111)
        self.ax2 = self.ax1.twinx()
        super().__init__(self.fig)
        self.setParent(parent)

    def plot_data(self, df):
        self.ax1.clear()
        self.ax2.clear()

        active_df = df[df['lightning_count'] > 0]
        if active_df.empty:
            return

        start_idx = max(0, active_df.index[0] - 12)
        end_idx = min(len(df) - 1, active_df.index[-1] + 12)
        plot_df = df.iloc[start_idx:end_idx]

        times = plot_df['datetime']
        lightnings = plot_df['lightning_count']
        pressure = plot_df['pressure']

        self.ax1.bar(
            times,
            lightnings,
            color='red',
            alpha=0.6,
            width=0.04,
            label='Молнии'
        )

        self.ax1.set_ylabel(
            'Количество вспышек',
            color='red',
            fontsize=12,
            fontweight='bold'
        )

        self.ax1.tick_params(axis='y', labelcolor='red')

        self.ax2.plot(
            times,
            pressure,
            color='blue',
            linewidth=2,
            marker='o',
            markersize=4,
            label='Давление (гПа)'
        )

        self.ax2.set_ylabel(
            'Атмосферное давление (гПа)',
            color='blue',
            fontsize=12,
            fontweight='bold'
        )

        self.ax2.yaxis.set_label_position("right")
        self.ax2.yaxis.tick_right()
        self.ax2.tick_params(axis='y', labelcolor='blue')

        self.ax2.invert_yaxis()

        self.ax1.set_xlabel('Дата и время', fontsize=12)
        self.ax1.xaxis.set_major_formatter(
            mdates.DateFormatter('%d %b %H:00')
        )

        self.fig.autofmt_xdate()

        self.ax1.grid(True, linestyle='--', alpha=0.5)

        correlation = active_df['pressure'].corr(
            active_df['lightning_count']
        )

        if not pd.isna(correlation):
            corr_text = f"Корреляция (r): {correlation:.2f}"

            self.ax1.text(
                0,
                -0.18,
                corr_text,
                transform=self.ax1.transAxes,
                fontsize=12,
                fontweight='bold',
                color='purple',
                ha='left',
                va='top',
                bbox=dict(
                    facecolor='white',
                    alpha=0.8,
                    edgecolor='purple'
                )
            )

        self.fig.tight_layout(rect=[0, 0.02, 1, 1])

        self.draw()