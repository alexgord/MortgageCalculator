from pathlib import Path
import logging

import matplotlib
import matplotlib.pyplot as plt

from config_dataclasses import PropertiesListConfig
from custom_types import MortgageInformation, MortgageResult, ResultKeys as K

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
        compact_labels: bool = False,
        ymin_padding: float | None = None,
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
            compact_labels: Use compact currency labels (e.g. $625k, $1.2M) If True, overrides fmt
            ymin_padding: Fraction below the lowest value to set as the y-axis minimum
                          (e.g. 0.10 = 10% below min value). None (default) starts the
                          axis at 0, matching the standard matplotlib bar chart behavior.
        """
        if values is None or len(values) == 0 or labels is None or len(labels) == 0:
            raise cls.ChartGenerationError("Labels and values must be non-empty lists.")
        
        if any(v < 0 for v in values):
            raise cls.ChartGenerationError("Negative values are not supported for bar charts.")
        
        if len(labels) != len(values):
            raise cls.ChartGenerationError("Labels and values lists must be of the same length.")

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
        
        bar_label_kwargs = {'padding': 3}
        if label_fontsize is not None:
            bar_label_kwargs['fontsize'] = label_fontsize
        if compact_labels:
            bar_label_kwargs['labels'] = [cls._format_compact_currency(value) for value in values]
        else:
            bar_label_kwargs['fmt'] = fmt
            
        ax.bar_label(bars, **bar_label_kwargs)
        
        plt.tight_layout()
        ymin = 0 if ymin_padding is None else min(values) * (1 - ymin_padding)
        ymax = max(values) + (max(values) - ymin) * cfg.chart.top_padding
        ax.set_ylim(ymin, ymax)
        
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
    def _format_compact_currency(cls, value: float) -> str:
        """Format currency with compact suffixes to reduce label overlap."""
        abs_value = abs(value)
        if abs_value >= 1_000_000:
            return f'${value / 1_000_000:.1f}M'
        if abs_value >= 1_000:
            return f'${value / 1_000:.0f}k'
        return f'${value:.0f}'

    @classmethod
    def generate_monthly_report_chart(cls, results: list[MortgageInformation], labels: list[str], output_dir: Path, cfg: PropertiesListConfig) -> None:
        """Generate monthly costs comparison chart."""
        monthly_costs = [mi.mortgage_result[K.TOTAL_MONTHLY_COSTS] for mi in results]
        cls.create_bar_chart(
            labels=labels,
            values=monthly_costs,
            output_path=output_dir / 'monthly_summary.png',
            cfg=cfg,
            title='Total Monthly Costs by Property',
            ylabel='Total Monthly Cost ($)',
            colors=cls._cycle_colors(len(results)),
            ymin_padding=0.10,
        )

    @classmethod
    def generate_annual_fixed_non_mortgage_costs_chart(cls, results: list[MortgageInformation], labels: list[str], output_dir: Path, cfg: PropertiesListConfig) -> None:
        """Generate annual fixed non-mortgage costs comparison chart."""
        annual_fixed_non_mortgage_costs = [mi.mortgage_result[K.ANNUAL_FIXED_NON_MORTGAGE_COSTS] for mi in results]
        cls.create_bar_chart(
            labels=labels,
            values=annual_fixed_non_mortgage_costs,
            output_path=output_dir / 'annual_fixed_non_mortgage_costs_summary.png',
            cfg=cfg,
            title='Annual Fixed Non-Mortgage Costs by Property',
            ylabel='Amount ($)',
            colors=cls._cycle_colors(len(results)),
            label_fontsize=8,
            ymin_padding=0.10,
        )

    @classmethod
    def generate_yearly_cost_comparison_chart(cls, results: list[MortgageInformation], labels: list[str], output_dir: Path, cfg: PropertiesListConfig) -> None:
        """Generate yearly cost comparison chart."""
        yearly_costs = [mi.mortgage_result[K.TOTAL_YEARLY_COSTS] for mi in results]
        cls.create_bar_chart(
            labels=labels,
            values=yearly_costs,
            output_path=output_dir / 'yearly_cost_summary.png',
            cfg=cfg,
            title='Total Yearly Costs by Property',
            ylabel='Total Yearly Cost ($)',
            colors=cls._cycle_colors(len(results)),
            label_fontsize=8,
            compact_labels=True,
            ymin_padding=0.10,
        )

    @classmethod
    def generate_property_value_report_chart(cls, results: list[MortgageInformation], labels: list[str], output_dir: Path, cfg: PropertiesListConfig) -> None:
        """Generate property value comparison chart."""
        property_values = [mi.mortgage_result[K.PROPERTY_VALUE] for mi in results]
        cls.create_bar_chart(
            labels=labels,
            values=property_values,
            output_path=output_dir / 'property_value_summary.png',
            cfg=cfg,
            title='Property Values by Property',
            ylabel='Property Value ($)',
            colors=cls._cycle_colors(len(results)),
            label_fontsize=8,
            compact_labels=True,
            ymin_padding=0.10,
        )

    @classmethod
    def generate_one_time_report_chart(cls, results: list[MortgageInformation], labels: list[str], output_dir: Path, cfg: PropertiesListConfig) -> None:
        """Generate one-time costs comparison chart."""
        one_time_costs = [mi.mortgage_result[K.TOTAL_ONE_TIME_COSTS] for mi in results]
        cls.create_bar_chart(
            labels=labels,
            values=one_time_costs,
            output_path=output_dir / 'one_time_summary.png',
            cfg=cfg,
            title='Total One-Time Costs by Property',
            ylabel='Amount ($)',
            colors=cls._cycle_colors(len(results)),
            label_fontsize=8,
            ymin_padding=0.10,
        )

    @classmethod
    def generate_monthly_breakdown_chart(cls, property_number: int, result: MortgageInformation, output_dir: Path, cfg: PropertiesListConfig) -> None:
        """Generate monthly cost breakdown chart for a single property."""
        categories = ['Mortgage Payment', 'Condo Fees', 'Property Tax', 'School Tax', 'Home Insurance']
        values = [result.mortgage_result[K.MONTHLY_MORTGAGE_PAYMENT], result.mortgage_result[K.CONDO_FEES], result.mortgage_result[K.MONTHLY_PROPERTY_TAX], result.mortgage_result[K.MONTHLY_SCHOOL_TAX], result.mortgage_result[K.MONTHLY_HOME_INSURANCE]]
        cls.create_bar_chart(
            labels=categories,
            values=values,
            output_path=output_dir / f'{property_number}_monthly_breakdown.png',
            cfg=cfg,
            title=f'Monthly Cost Breakdown for Property {property_number}',
            ylabel='Amount ($)',
            colors=['#2196F3', '#FFC107', '#4CAF50', '#FF5722', '#9C27B0'],
            xlabel=None,
            fmt='$%.2f',
        )

    @classmethod
    def generate_yearly_breakdown_chart(cls, property_number: int, result: MortgageInformation, output_dir: Path, cfg: PropertiesListConfig) -> None:
        """Generate yearly cost breakdown chart for a single property."""
        categories = ['Property Tax', 'School Tax', 'Home Insurance', 'Condo Fees', 'Mortgage Payment']
        values = [result.mortgage_result[K.YEARLY_PROPERTY_TAX], result.mortgage_result[K.YEARLY_SCHOOL_TAX], result.mortgage_result[K.YEARLY_HOME_INSURANCE], result.mortgage_result[K.YEARLY_CONDO_FEE_COST], result.mortgage_result[K.YEARLY_MORTGAGE_PAYMENT]]
        cls.create_bar_chart(
            labels=categories,
            values=values,
            output_path=output_dir / f'{property_number}_yearly_breakdown.png',
            cfg=cfg,
            title=f'Yearly Cost Breakdown for Property {property_number}',
            ylabel='Amount ($)',
            colors=['#8BC34A', '#FF5722', '#9C27B0', '#FFC107', '#2196F3'],
            xlabel=None,
            fmt='$%.2f',
        )

    @classmethod
    def generate_one_time_breakdown_chart(cls, property_number: int, result: MortgageInformation, output_dir: Path, cfg: PropertiesListConfig) -> None:
        """Generate one-time cost breakdown chart for a single property."""
        categories = ['Land Transfer Tax', 'Notary Cost', 'Inspection Cost']
        values = [result.mortgage_result[K.LAND_TRANSFER_TAX], result.mortgage_result[K.NOTARY_COST], result.mortgage_result[K.INSPECTION_COST]]
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
    def generate_property_report_chart(cls, property_number: int, result: MortgageInformation, output_dir: Path, cfg: PropertiesListConfig) -> None:
        cls.generate_monthly_breakdown_chart(property_number, result, output_dir, cfg)
        cls.generate_yearly_breakdown_chart(property_number, result, output_dir, cfg)
        cls.generate_one_time_breakdown_chart(property_number, result, output_dir, cfg)

    @classmethod
    def generate_monthly_mortgage_chart(cls, results: list[MortgageInformation], labels: list[str], output_dir: Path, cfg: PropertiesListConfig) -> None:
        """Generate monthly mortgage payment comparison chart."""
        monthly_mortgages = [mi.mortgage_result[K.MONTHLY_MORTGAGE_PAYMENT] for mi in results]
        cls.create_bar_chart(
            labels=labels,
            values=monthly_mortgages,
            output_path=output_dir / 'monthly_mortgage_summary.png',
            cfg=cfg,
            title='Monthly Mortgage Payment by Property',
            ylabel='Monthly Mortgage Payment ($)',
            colors=cls._cycle_colors(len(results)),
            ymin_padding=0.10,
        )

    @classmethod
    def generate_monthly_condo_fees_chart(cls, results: list[MortgageInformation], labels: list[str], output_dir: Path, cfg: PropertiesListConfig) -> None:
        """Generate monthly condo fees comparison chart."""
        condo_fees = [mi.mortgage_result[K.CONDO_FEES] for mi in results]
        filtered = [(lbl, val) for lbl, val in zip(labels, condo_fees) if val > 0]
        if not filtered:
            logger.info("Skipping monthly condo fees chart: no properties have condo fees.")
            return
        filtered_labels, filtered_values = zip(*filtered)
        cls.create_bar_chart(
            labels=list(filtered_labels),
            values=list(filtered_values),
            output_path=output_dir / 'monthly_condo_fees_summary.png',
            cfg=cfg,
            title='Monthly Condo Fees by Property',
            ylabel='Monthly Condo Fees ($)',
            colors=cls._cycle_colors(len(filtered_labels)),
            ymin_padding=0.10,
        )

    @classmethod
    def generate_price_per_sqft_chart(cls, results: list[MortgageInformation], labels: list[str], output_dir: Path, cfg: PropertiesListConfig) -> None:
        """Generate price per square foot comparison chart."""
        price_per_sqft = [mi.mortgage_result[K.PRICE_PER_SQFT] for mi in results]
        filtered = [(lbl, val) for lbl, val in zip(labels, price_per_sqft) if val > 0]
        if not filtered:
            logger.info("Skipping price per sqft chart: no properties have area data.")
            return
        filtered_labels, filtered_values = zip(*filtered)
        cls.create_bar_chart(
            labels=list(filtered_labels),
            values=list(filtered_values),
            output_path=output_dir / 'price_per_sqft_summary.png',
            cfg=cfg,
            title='Price per Square Foot by Property',
            ylabel='Price per sqft ($)',
            colors=cls._cycle_colors(len(filtered_labels)),
            fmt='$%.0f',
            ymin_padding=0.10,
        )

    @classmethod
    def generate_cost_comparison_charts(cls, results: list[MortgageInformation], output_dir: Path, cfg: PropertiesListConfig) -> None:
        labels = [f"Property {i + 1}" for i, row in enumerate(results)]

        cls.generate_monthly_report_chart(results, labels, output_dir, cfg)
        cls.generate_monthly_mortgage_chart(results, labels, output_dir, cfg)
        cls.generate_monthly_condo_fees_chart(results, labels, output_dir, cfg)
        cls.generate_price_per_sqft_chart(results, labels, output_dir, cfg)
        cls.generate_one_time_report_chart(results, labels, output_dir, cfg)
        cls.generate_annual_fixed_non_mortgage_costs_chart(results, labels, output_dir, cfg)
        cls.generate_property_value_report_chart(results, labels, output_dir, cfg)
        cls.generate_yearly_cost_comparison_chart(results, labels, output_dir, cfg)
