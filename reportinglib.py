from pathlib import Path
import logging
import io

import matplotlib
import matplotlib.pyplot as plt

from mortgagecalculatorlib import CalculatedMortgage
from config_dataclasses import PropertiesListConfig, PropertyConfig
from custom_types import MortgageResult, ResultKeys as K

matplotlib.use('Agg')  # Use non-interactive backend for saving files

logger = logging.getLogger(__name__)


class ReportGenerationError(Exception):
    """Raised when report generation fails."""
    pass


def create_bar_chart(
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
        raise ReportGenerationError(f"Failed to save chart to {output_path}: {e}") from e
    finally:
        plt.close()

def generate_monthly_report_chart(results: list[MortgageResult], labels: list[str], output_dir: Path, cfg: PropertiesListConfig) -> None:
    """Generate monthly costs comparison chart."""
    monthly_costs = [row[K.TOTAL_MONTHLY_COSTS] for row in results]
    create_bar_chart(
        labels=labels,
        values=monthly_costs,
        output_path=output_dir / 'monthly_summary.png',
        cfg=cfg,
        title='Total Monthly Costs by Property',
        ylabel='Total Monthly Cost ($)',
        colors='#E91E63',
    )

def generate_yearly_report_chart(results: list[MortgageResult], labels: list[str], output_dir: Path, cfg: PropertiesListConfig) -> None:
    """Generate yearly costs comparison chart."""
    yearly_costs = [row[K.TOTAL_YEARLY_COSTS] for row in results]
    create_bar_chart(
        labels=labels,
        values=yearly_costs,
        output_path=output_dir / 'yearly_summary.png',
        cfg=cfg,
        title='Total Yearly Costs by Property',
        ylabel='Amount ($)',
        colors='#9C27B0',
        label_fontsize=8,
    )

def generate_property_value_report_chart(results: list[MortgageResult], labels: list[str], output_dir: Path, cfg: PropertiesListConfig) -> None:
    """Generate property value comparison chart."""
    property_values = [row[K.PROPERTY_VALUE] for row in results]
    create_bar_chart(
        labels=labels,
        values=property_values,
        output_path=output_dir / 'property_value_summary.png',
        cfg=cfg,
        title='Property Values by Property',
        ylabel='Property Value ($)',
        colors='#3F51B5',
    )

def generate_one_time_report_chart(results: list[MortgageResult], labels: list[str], output_dir: Path, cfg: PropertiesListConfig) -> None:
    """Generate one-time costs comparison chart."""
    one_time_costs = [row[K.TOTAL_ONE_TIME_COSTS] for row in results]
    create_bar_chart(
        labels=labels,
        values=one_time_costs,
        output_path=output_dir / 'one_time_summary.png',
        cfg=cfg,
        title='Total One-Time Costs by Property',
        ylabel='Amount ($)',
        colors='#4CAF50',
        label_fontsize=8,
    )

def generate_monthly_breakdown_chart(property_number: int, result: MortgageResult, output_dir: Path, cfg: PropertiesListConfig) -> None:
    """Generate monthly cost breakdown chart for a single property."""
    categories = ['Mortgage Payment', 'Condo Fees']
    values = [result[K.MONTHLY_MORTGAGE_PAYMENT], result[K.CONDO_FEES]]
    create_bar_chart(
        labels=categories,
        values=values,
        output_path=output_dir / f'{property_number}_monthly_breakdown.png',
        cfg=cfg,
        title=f'Monthly Cost Breakdown for Property {property_number}',
        ylabel='Amount ($)',
        colors=['#2196F3', '#FFC107'],
        xlabel=None,
        fmt='$%.2f',
    )

def generate_yearly_breakdown_chart(property_number: int, result: MortgageResult, output_dir: Path, cfg: PropertiesListConfig) -> None:
    """Generate yearly cost breakdown chart for a single property."""
    categories = ['Property Tax', 'School Tax', 'Home Insurance']
    values = [result[K.YEARLY_PROPERTY_TAX], result[K.YEARLY_SCHOOL_TAX], result[K.HOME_INSURANCE]]
    create_bar_chart(
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

def generate_one_time_breakdown_chart(property_number: int, result: MortgageResult, output_dir: Path, cfg: PropertiesListConfig) -> None:
    """Generate one-time cost breakdown chart for a single property."""
    categories = ['Land Transfer Tax', 'Notary Cost', 'Inspection Cost']
    values = [result[K.LAND_TRANSFER_TAX], result[K.NOTARY_COST], result[K.INSPECTION_COST]]
    create_bar_chart(
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

def generate_property_report_chart(property_number: int, result: MortgageResult, output_dir: Path, cfg: PropertiesListConfig) -> None:
    generate_monthly_breakdown_chart(property_number, result, output_dir, cfg)
    generate_yearly_breakdown_chart(property_number, result, output_dir, cfg)
    generate_one_time_breakdown_chart(property_number, result, output_dir, cfg)

def generate_cost_comparison_charts(results: list[MortgageResult], output_dir: Path, cfg: PropertiesListConfig) -> None:
    labels = [f"Property {i + 1}" for i, row in enumerate(results)]

    generate_monthly_report_chart(results, labels, output_dir, cfg)
    generate_one_time_report_chart(results, labels, output_dir, cfg)
    generate_yearly_report_chart(results, labels, output_dir, cfg)
    generate_property_value_report_chart(results, labels, output_dir, cfg)

def generate_markdown_report(output_report_file: Path, results: list[MortgageResult], cfg: PropertiesListConfig) -> None:
    """Generate a Markdown report from mortgage calculation results.
    
    Args:
        output_report_file: Path to write the report to
        results: List of mortgage calculation results
        cfg: Configuration object
        
    Raises:
        ValueError: If results is empty
        ReportGenerationError: If report generation fails
    """
    if not results:
        raise ValueError("Cannot generate report with empty results")
    
    try:
        output_report_file.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise ReportGenerationError(f"Failed to create output directory {output_report_file.parent}: {e}") from e

    generate_cost_comparison_charts(results, output_report_file.parent, cfg)

    # Generate markdown content using StringIO buffer
    with io.StringIO() as buffer:
        buffer.write("# Mortgage Calculation Report\n")
        buffer.write(f"**Total Properties Analyzed:** {len(results)}\n\n")

        buffer.write("## Personal Financial Details\n")
        buffer.write("| Item | Value |\n")
        buffer.write("|------|-------|\n")
        buffer.write(f"| Down Payment | ${cfg.loan_parameters.down_payment:,.2f} |\n")
        buffer.write(f"| Monthly Salary | ${cfg.loan_parameters.monthly_salary:,.2f} |\n")
        
        buffer.write("## Properties Analyzed:\n")

        for i, row in enumerate(results, 1):
            generate_property_report_chart(i, row, output_report_file.parent, cfg)

            buffer.write(f"### Property {i}\n")

            if row[K.ADDRESS]:
                buffer.write(f"**Address:** {row[K.ADDRESS]}\n\n")
            
            if row[K.DESCRIPTION]:
                buffer.write(f"**Description:** {row[K.DESCRIPTION] or 'No Description'}\n\n")

            if row[K.LINK]:
                buffer.write(f"**Link:** [View Listing]({row[K.LINK]})\n\n")

            buffer.write("#### Property Details\n")
            buffer.write("| Item | Value |\n")
            buffer.write("|------|-------|\n")
            buffer.write(f"| Property Value | ${row[K.PROPERTY_VALUE]:,.2f} |\n")
            buffer.write(f"| Area | {row[K.AREA]} sqft |\n")
            buffer.write(f"| Year Built | {row[K.YEAR_BUILT]} |\n")
            buffer.write(f"| Bedrooms | {row[K.BEDROOMS]} |\n")
            buffer.write(f"| Bathrooms | {row[K.BATHROOMS]} |\n")
            buffer.write(f"| Principal | ${row[K.PRINCIPAL]:,.2f} |\n")
            buffer.write(f"| Interest Rate | {row[K.INTEREST_RATE]:.2f}% |\n")
            buffer.write(f"| Loan Term | {row[K.YEARS_OF_LOAN]} years |\n")
            
            buffer.write("#### Monthly Costs\n")
            buffer.write("| Item | Amount |\n")
            buffer.write("|------|--------|\n")
            buffer.write(f"| Mortgage Payment | ${row[K.MONTHLY_MORTGAGE_PAYMENT]:,.2f} |\n")
            buffer.write(f"| Condo Fees | ${row[K.CONDO_FEES]:,.2f} |\n")
            buffer.write(f"| **Total Monthly Costs** | **${row[K.TOTAL_MONTHLY_COSTS]:,.2f}** |\n")
            buffer.write(f"| Percentage of Salary | {row[K.PERCENTAGE_OF_SALARY] * 100:.2f}% |\n")

            buffer.write(f"![Monthly Breakdown]({i}_monthly_breakdown.png)\n")
            
            buffer.write("#### One-Time Costs\n")
            buffer.write("| Item | Amount |\n")
            buffer.write("|------|--------|\n")
            buffer.write(f"| Land Transfer Tax ({row[K.LAND_TRANSFER_TAX_RATE] * 100:.2f}%) | ${row[K.LAND_TRANSFER_TAX]:,.2f} |\n")
            buffer.write(f"| Notary Cost | ${row[K.NOTARY_COST]:,.2f} |\n")
            buffer.write(f"| Inspection Cost | ${row[K.INSPECTION_COST]:,.2f} |\n")
            buffer.write(f"| **Total One-Time Costs** | **${row[K.TOTAL_ONE_TIME_COSTS]:,.2f}** |\n")
            
            buffer.write(f"![One-Time Breakdown]({i}_one_time_breakdown.png)\n")

            buffer.write("#### Yearly Costs\n")
            buffer.write("| Item | Amount |\n")
            buffer.write("|------|--------|\n")
            buffer.write(f"| Property Tax ({row[K.PROPERTY_TAX_RATE]:.2f}%) | ${row[K.YEARLY_PROPERTY_TAX]:,.2f} |\n")
            buffer.write(f"| School Tax ({row[K.SCHOOL_TAX_RATE]:.2f}%) | ${row[K.YEARLY_SCHOOL_TAX]:,.2f} |\n")
            buffer.write(f"| Home Insurance | ${row[K.HOME_INSURANCE]:,.2f} |\n")
            buffer.write(f"| **Total Yearly Costs** | **${row[K.TOTAL_YEARLY_COSTS]:,.2f}** |\n")
            
            buffer.write(f"![Yearly Breakdown]({i}_yearly_breakdown.png)\n")

            buffer.write("---\n")

        # Add charts section
        buffer.write("## Cost Comparison Charts\n")
        buffer.write("### Property Values by Property\n")
        buffer.write("![Property Values by Property](property_value_summary.png)\n")
        buffer.write("### Total Monthly Costs by Property\n")
        buffer.write("![Total Monthly Costs by Property](monthly_summary.png)\n")
        buffer.write("### Total Yearly Costs by Property\n")
        buffer.write("![Yearly Costs by Property](yearly_summary.png)\n")
        buffer.write("### One-Time Costs by Property\n")
        buffer.write("![One-Time Costs by Property](one_time_summary.png)\n")
        
        # Add comprehensive summary section
        buffer.write("## Property Comparison Summary\n\n")
        
        # Main comparison table
        buffer.write("### Side-by-Side Comparison\n")
        buffer.write("| Metric |")
        for i in range(1, len(results) + 1):
            buffer.write(f" [Property {i}](#property-{i}) |")
        buffer.write("\n")
        
        buffer.write("|--------|")
        buffer.write("----------|" * len(results))
        buffer.write("\n")
        
        # Property Value
        buffer.write("| **Property Value** |")
        for row in results:
            buffer.write(f" ${row[K.PROPERTY_VALUE]:,.0f} |")
        buffer.write("\n")
        
        # Monthly Costs
        buffer.write("| **Monthly Costs** |")
        for row in results:
            buffer.write(f" ${row[K.TOTAL_MONTHLY_COSTS]:,.2f} |")
        buffer.write("\n")
        
        # % of Salary
        buffer.write("| **% of Salary** |")
        for row in results:
            buffer.write(f" {row[K.PERCENTAGE_OF_SALARY] * 100:.1f}% |")
        buffer.write("\n")
        
        # Yearly Costs
        buffer.write("| **Yearly Costs** |")
        for row in results:
            buffer.write(f" ${row[K.TOTAL_YEARLY_COSTS]:,.2f} |")
        buffer.write("\n")
        
        # One-Time Costs
        buffer.write("| **One-Time Costs** |")
        for row in results:
            buffer.write(f" ${row[K.TOTAL_ONE_TIME_COSTS]:,.2f} |")
        buffer.write("\n")
        
        # Area
        buffer.write("| **Area (sqft)** |")
        for row in results:
            buffer.write(f" {row[K.AREA]:,} |")
        buffer.write("\n")
        
        # Price per sqft
        buffer.write("| **Price/sqft** |")
        for row in results:
            price_per_sqft = row[K.PROPERTY_VALUE] / row[K.AREA] if row[K.AREA] > 0 else 0
            buffer.write(f" ${price_per_sqft:,.2f} |")
        buffer.write("\n")
        
        # Bedrooms/Bathrooms
        buffer.write("| **Bed/Bath** |")
        for row in results:
            buffer.write(f" {row[K.BEDROOMS]}/{row[K.BATHROOMS]} |")
        buffer.write("\n\n")
        
        # Rankings section
        buffer.write("### Rankings\n\n")
        
        # Lowest monthly cost
        sorted_by_monthly = sorted(enumerate(results, 1), key=lambda x: x[1][K.TOTAL_MONTHLY_COSTS])
        buffer.write("**Lowest Monthly Costs:**\n")
        for rank, (idx, row) in enumerate(sorted_by_monthly, 1):
            buffer.write(f"{rank}. [Property {idx}](#property-{idx}) - ${row[K.TOTAL_MONTHLY_COSTS]:,.2f}/month\n")
        buffer.write("\n")
        
        # Best value (lowest price per sqft)
        sorted_by_value = sorted(
            enumerate(results, 1),
            key=lambda x: x[1][K.PROPERTY_VALUE] / x[1][K.AREA] if x[1][K.AREA] > 0 else float('inf')
        )
        buffer.write("**Best Value (Price/sqft):**\n")
        for rank, (idx, row) in enumerate(sorted_by_value, 1):
            price_per_sqft = row[K.PROPERTY_VALUE] / row[K.AREA] if row[K.AREA] > 0 else 0
            buffer.write(f"{rank}. [Property {idx}](#property-{idx}) - ${price_per_sqft:,.2f}/sqft\n")
        buffer.write("\n")
        
        # Lowest % of salary
        sorted_by_salary = sorted(enumerate(results, 1), key=lambda x: x[1][K.PERCENTAGE_OF_SALARY])
        buffer.write("**Most Affordable (% of Salary):**\n")
        for rank, (idx, row) in enumerate(sorted_by_salary, 1):
            buffer.write(f"{rank}. [Property {idx}](#property-{idx}) - {row[K.PERCENTAGE_OF_SALARY] * 100:.1f}%\n")
        buffer.write("\n")

        buffer.write("---\n")

        # Write to file
        try:
            with open(output_report_file, 'w', encoding='utf-8') as f:
                f.write(buffer.getvalue())
        except OSError as e:
            raise ReportGenerationError(f"Failed to write report to {output_report_file}: {e}") from e
    
    logger.info(f"Report generated successfully: {output_report_file}")
