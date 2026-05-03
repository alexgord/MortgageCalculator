from pathlib import Path
import logging

import matplotlib
import matplotlib.pyplot as plt

from config_dataclasses import PropertiesListConfig
from custom_types import MortgageResult, ResultKeys as K

matplotlib.use('Agg')  # Use non-interactive backend for saving files

logger = logging.getLogger(__name__)


class ChartService:
    # Color palette for multi-property comparison charts
    PROPERTY_COLORS = ['#E91E63', '#3F51B5', '#4CAF50', '#FF9800', '#9C27B0', '#00BCD4', '#FF5722', '#8BC34A', '#673AB7', '#009688']


    class ChartGenerationError(Exception):
        """Raised when chart generation fails."""
        pass
    
    @classmethod
    def create_bar_chart(
        cls,
        labels: list[str],
        values: list[float],
        output_path: Path,
        cfg: PropertiesListConfig,
        title: str,
        ylabel: str,
        colors: str | list[str],
        xlabel: str | None = 'Property',
        fmt: str = '$%.0f',
        label_fontsize: int | None = None,
    ) -> None:
        """
        Generic bar chart generator to reduce duplication across chart functions.
        
        Args:
            labels: X-axis labels for each bar
            values: Height values for each bar
            output_path: Path to save the chart image
            cfg: Configuration containing chart dimensions and padding
            title: Chart title
            ylabel: Y-axis label
            colors: Single color string or list of colors for each bar
            xlabel: X-axis label (None to omit)
            fmt: Format string for bar labels
            label_fontsize: Font size for bar labels (None for default)
        """
        figure_size = (cfg.chart.width, cfg.chart.height)
        fig, ax = plt.subplots(figsize=figure_size)
        
        bars = ax.bar(labels, values, color=colors)
        
        if xlabel:
            ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.tick_params(axis='x', labelrotation=30)
        for tick in ax.get_xticklabels():
            tick.set_ha('right')
        
        bar_label_kwargs = {'fmt': fmt, 'padding': 3}
        if label_fontsize is not None:
            bar_label_kwargs['fontsize'] = label_fontsize
        ax.bar_label(bars, **bar_label_kwargs)
        
        plt.tight_layout()
        ymin, ymax = ax.get_ylim()
        ax.set_ylim(ymin, ymax * (1 + cfg.chart.top_padding))
        
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(output_path, dpi=cfg.chart.dpi)
        except OSError as e:
            plt.close()
            raise cls.ChartGenerationError(f"Failed to save chart to {output_path}: {e}") from e
        finally:
            plt.close()

    @classmethod
    def _cycle_colors(cls, n: int) -> list[str]:
        """Return a list of n colors cycling through the property palette."""
        return [cls.PROPERTY_COLORS[i % len(cls.PROPERTY_COLORS)] for i in range(n)]

    @classmethod
    def generate_monthly_report_chart(cls, results: list[MortgageResult], labels: list[str], output_dir: Path, cfg: PropertiesListConfig) -> None:
        """Generate monthly costs comparison chart."""
        monthly_costs = [row[K.TOTAL_MONTHLY_COSTS] for row in results]
        cls.create_bar_chart(
            labels=labels,
            values=monthly_costs,
            output_path=output_dir / 'monthly_summary.png',
            cfg=cfg,
            title='Total Monthly Costs by Property',
            ylabel='Total Monthly Cost ($)',
            colors=cls._cycle_colors(len(results)),
        )

    @classmethod
    def generate_yearly_report_chart(cls, results: list[MortgageResult], labels: list[str], output_dir: Path, cfg: PropertiesListConfig) -> None:
        """Generate yearly costs comparison chart."""
        yearly_costs = [row[K.TOTAL_YEARLY_COSTS] for row in results]
        cls.create_bar_chart(
            labels=labels,
            values=yearly_costs,
            output_path=output_dir / 'yearly_summary.png',
            cfg=cfg,
            title='Total Yearly Costs by Property',
            ylabel='Amount ($)',
            colors=cls._cycle_colors(len(results)),
            label_fontsize=8,
        )

    @classmethod
    def generate_property_value_report_chart(cls, results: list[MortgageResult], labels: list[str], output_dir: Path, cfg: PropertiesListConfig) -> None:
        """Generate property value comparison chart."""
        property_values = [row[K.PROPERTY_VALUE] for row in results]
        cls.create_bar_chart(
            labels=labels,
            values=property_values,
            output_path=output_dir / 'property_value_summary.png',
            cfg=cfg,
            title='Property Values by Property',
            ylabel='Property Value ($)',
            colors=cls._cycle_colors(len(results)),
        )

    @classmethod
    def generate_one_time_report_chart(cls, results: list[MortgageResult], labels: list[str], output_dir: Path, cfg: PropertiesListConfig) -> None:
        """Generate one-time costs comparison chart."""
        one_time_costs = [row[K.TOTAL_ONE_TIME_COSTS] for row in results]
        cls.create_bar_chart(
            labels=labels,
            values=one_time_costs,
            output_path=output_dir / 'one_time_summary.png',
            cfg=cfg,
            title='Total One-Time Costs by Property',
            ylabel='Amount ($)',
            colors=cls._cycle_colors(len(results)),
            label_fontsize=8,
        )

    @classmethod
    def generate_monthly_breakdown_chart(cls, property_number: int, result: MortgageResult, output_dir: Path, cfg: PropertiesListConfig) -> None:
        """Generate monthly cost breakdown chart for a single property."""
        categories = ['Mortgage Payment', 'Condo Fees', 'Property Tax', 'School Tax', 'Home Insurance']
        values = [result[K.MONTHLY_MORTGAGE_PAYMENT], result[K.CONDO_FEES], result[K.MONTHLY_PROPERTY_TAX], result[K.MONTHLY_SCHOOL_TAX], result[K.MONTHLY_HOME_INSURANCE]]
        cls.create_bar_chart(
            labels=categories,
            values=values,
            output_path=output_dir / f'{property_number}_monthly_breakdown.png',
            cfg=cfg,
            title=f'Monthly Cost Breakdown for Property {property_number}',
            ylabel='Amount ($)',
            colors=['#2196F3', '#FFC107', '#4CAF50', '#FF5722', '#9C27B0'],
            xlabel=None,
            fmt='$%.2f'
        )

    @classmethod
    def generate_yearly_breakdown_chart(cls, property_number: int, result: MortgageResult, output_dir: Path, cfg: PropertiesListConfig) -> None:
        """Generate yearly cost breakdown chart for a single property."""
        categories = ['Property Tax', 'School Tax', 'Home Insurance']
        values = [result[K.YEARLY_PROPERTY_TAX], result[K.YEARLY_SCHOOL_TAX], result[K.YEARLY_HOME_INSURANCE]]
        cls.create_bar_chart(
            labels=categories,
            values=values,
            output_path=output_dir / f'{property_number}_yearly_breakdown.png',
            cfg=cfg,
            title=f'Yearly Cost Breakdown for Property {property_number}',
            ylabel='Amount ($)',
            colors=['#8BC34A', '#FF5722', '#9C27B0'],
            xlabel=None,
            fmt='$%.2f',
        )

    @classmethod
    def generate_one_time_breakdown_chart(cls, property_number: int, result: MortgageResult, output_dir: Path, cfg: PropertiesListConfig) -> None:
        """Generate one-time cost breakdown chart for a single property."""
        categories = ['Land Transfer Tax', 'Notary Cost', 'Inspection Cost']
        values = [result[K.LAND_TRANSFER_TAX], result[K.NOTARY_COST], result[K.INSPECTION_COST]]
        cls.create_bar_chart(
            labels=categories,
            values=values,
            output_path=output_dir / f'{property_number}_one_time_breakdown.png',
            cfg=cfg,
            title=f'One-Time Cost Breakdown for Property {property_number}',
            ylabel='Amount ($)',
            colors=['#3F51B5', '#009688', '#FF9800'],
            xlabel=None,
            fmt='$%.2f',
        )

    @classmethod
    def generate_property_report_chart(cls, property_number: int, result: MortgageResult, output_dir: Path, cfg: PropertiesListConfig) -> None:
        cls.generate_monthly_breakdown_chart(property_number, result, output_dir, cfg)
        cls.generate_yearly_breakdown_chart(property_number, result, output_dir, cfg)
        cls.generate_one_time_breakdown_chart(property_number, result, output_dir, cfg)

    @classmethod
    def generate_cost_comparison_charts(cls, results: list[MortgageResult], output_dir: Path, cfg: PropertiesListConfig) -> None:
        labels = [f"Property {i + 1}" for i, row in enumerate(results)]

        cls.generate_monthly_report_chart(results, labels, output_dir, cfg)
        cls.generate_one_time_report_chart(results, labels, output_dir, cfg)
        cls.generate_yearly_report_chart(results, labels, output_dir, cfg)
        cls.generate_property_value_report_chart(results, labels, output_dir, cfg)
