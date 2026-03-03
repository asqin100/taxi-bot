"""Visualization service for generating charts and heatmaps."""
import io
from datetime import datetime
from typing import List

import matplotlib
matplotlib.use('Agg')  # Non-GUI backend for server environments
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

from bot.models.shift import Shift


def generate_heatmap(shifts: List[Shift]) -> io.BytesIO:
    """
    Generate earnings heatmap by hour × day of week.

    Args:
        shifts: List of completed Shift objects

    Returns:
        BytesIO object containing PNG image
    """
    if not shifts:
        # Create empty heatmap if no shifts
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.text(0.5, 0.5, 'Нет данных для отображения',
                ha='center', va='center', fontsize=16)
        ax.axis('off')

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return buf

    # Prepare data
    data = []
    for shift in shifts:
        if shift.end_time and shift.net_earnings is not None:
            data.append({
                'hour': shift.end_time.hour,
                'weekday': shift.end_time.weekday(),  # 0=Monday, 6=Sunday
                'earnings': shift.net_earnings
            })

    if not data:
        # No valid data
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.text(0.5, 0.5, 'Нет данных для отображения',
                ha='center', va='center', fontsize=16)
        ax.axis('off')

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return buf

    df = pd.DataFrame(data)

    # Aggregate earnings by hour and weekday
    pivot_table = df.pivot_table(
        values='earnings',
        index='hour',
        columns='weekday',
        aggfunc='sum',
        fill_value=0
    )

    # Ensure all hours (0-23) are present
    all_hours = pd.Index(range(24), name='hour')
    pivot_table = pivot_table.reindex(all_hours, fill_value=0)

    # Ensure all weekdays (0-6) are present
    all_weekdays = list(range(7))
    for day in all_weekdays:
        if day not in pivot_table.columns:
            pivot_table[day] = 0
    pivot_table = pivot_table[all_weekdays]

    # Rename columns to day names
    day_names = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    pivot_table.columns = day_names

    # Create heatmap
    fig, ax = plt.subplots(figsize=(12, 10))

    # Use sequential colormap (green for higher earnings)
    sns.heatmap(
        pivot_table,
        annot=True,
        fmt='.0f',
        cmap='YlGnBu',
        cbar_kws={'label': 'Заработок (₽)'},
        linewidths=0.5,
        linecolor='gray',
        ax=ax
    )

    ax.set_title('Тепловая карта заработка (час × день недели)',
                 fontsize=16, pad=20)
    ax.set_xlabel('День недели', fontsize=12)
    ax.set_ylabel('Час дня', fontsize=12)

    plt.tight_layout()

    # Save to BytesIO
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)

    return buf
