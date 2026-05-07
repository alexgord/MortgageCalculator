from pathlib import Path
import logging
import io

import pandas as pd

from config_dataclasses import PropertiesListConfig
from custom_types import MortgageResult, ResultKeys as K

from mortgagecalculatorlib import CalculatedAffordability
from reportwriter import ReportWriter, get_class_by_value
from markdownlib import MarkdownWriter
from htmllib import HTMLWriter

logger = logging.getLogger(__name__)

class ReportGenerationError(Exception):
    """Raised when report generation fails."""
    pass

def _format_rate(value: float) -> str:
    """Format a rate/percentage value with up to 5 decimal places, stripping trailing zeros.
    
    Examples:
        0.5337  -> '0.5337'
        0.08423 -> '0.08423'
        4.69    -> '4.69'
        1.5     -> '1.5'
    """
    return f"{value:.5f}".rstrip('0').rstrip('.')


def _write_personal_financial_details(buffer: io.StringIO, report_writer: ReportWriter, cfg: PropertiesListConfig, affordability: CalculatedAffordability) -> None:
    personal_details_df = pd.DataFrame({
        "Item": ["Down Payment",
                 "Monthly Salary (Gross)",
                 "Monthly Debt Payments",
                 report_writer.print_bold("*Maximum Monthly Mortgage Payment (Based on GDS/TDS guidelines)"),
                 report_writer.print_bold("*Maximum Mortgage Amount (Based on GDS/TDS guidelines)")],
        "Value": [f"${cfg.loan_parameters.down_payment:,.2f}",
                  f"${cfg.loan_parameters.monthly_salary:,.2f}",
                  f"${cfg.loan_parameters.monthly_debt_payment:,.2f}",
                  f"${affordability.max_monthly_payment:,.2f}",
                  f"${affordability.max_loan_amount:,.2f}"]
    })
    buffer.write(report_writer.print_header("Personal Financial Details", level=2))
    buffer.write(report_writer.print_table(personal_details_df))
    buffer.write(report_writer.print_empty_line())

    maximum_mortgage_warning = (
        "*Note: These maximums are theoretical ceilings based on standard banking guidelines and do not guarantee loan approval. Actual approved amounts may vary based on lender criteria and other factors. "
        "Maximum mortgage amount assumes all other costs are zero, such as property taxes, insurance, and condo fees. In reality, these costs will reduce the maximum mortgage amount you may qualify for. "
        "Treat this value as a theoretical upper limit and sanity check rather than an exact figure you can expect to receive."
    )
    buffer.write(report_writer.print_paragraph(maximum_mortgage_warning))
    buffer.write(report_writer.print_empty_line())


def _write_single_property(buffer: io.StringIO, report_writer: ReportWriter, i: int, row: MortgageResult, cfg: PropertiesListConfig) -> None:
    buffer.write(report_writer.print_header(f"Property {i}", level=3))

    if row[K.ADDRESS]:
        buffer.write(report_writer.print_paragraph(f"{report_writer.print_bold('Address:')} {row[K.ADDRESS]}"))

    if row[K.DESCRIPTION]:
        buffer.write(report_writer.print_paragraph(f"{report_writer.print_bold('Description:')} {row[K.DESCRIPTION] or 'No Description'}"))

    if row[K.LINK]:
        buffer.write(report_writer.print_paragraph(f"{report_writer.print_bold('Link:')} {report_writer.print_link('View Listing', row[K.LINK])}"))

    property_details_df = pd.DataFrame({
        "Item": ["Property Value", "Area", "Year Built", "Bedrooms", "Bathrooms", "Loan Amount", "Interest Rate", "Loan Term", "Monthly Interest (Initial)", "Yearly Interest (Initial)", "Total Interest (Loan Term)"],
        "Value": [f"${row[K.PROPERTY_VALUE]:,.2f}", f"{row[K.AREA]} sqft", f"{row[K.YEAR_BUILT]}", f"{row[K.BEDROOMS]}", f"{row[K.BATHROOMS]}", f"${row[K.LOAN_AMOUNT]:,.2f}", f"{_format_rate(row[K.INTEREST_RATE])}%", f"{row[K.YEARS_OF_LOAN]} years", f"${row[K.MONTHLY_INTEREST]:,.2f}", f"${row[K.YEARLY_INTEREST]:,.2f}", f"${row[K.TOTAL_INTEREST]:,.2f}"]
    })
    buffer.write(report_writer.print_header("Property Details", level=4))
    buffer.write(report_writer.print_table(property_details_df))
    buffer.write(report_writer.print_empty_line())

    monthly_costs_df = pd.DataFrame({
        "Item": ["Mortgage Payment", "Condo Fees", "Property Tax (Amortized)", "School Tax (Amortized)", "Home Insurance (Amortized)", report_writer.print_bold("Total Monthly Costs")],
        "Amount": [f"${row[K.MONTHLY_MORTGAGE_PAYMENT]:,.2f}", f"${row[K.CONDO_FEES]:,.2f}", f"${row[K.MONTHLY_PROPERTY_TAX]:,.2f}", f"${row[K.MONTHLY_SCHOOL_TAX]:,.2f}", f"${row[K.MONTHLY_HOME_INSURANCE]:,.2f}", report_writer.print_bold(f"${row[K.TOTAL_MONTHLY_COSTS]:,.2f}")]
    })
    buffer.write(report_writer.print_header("Monthly Costs", level=4))
    buffer.write(report_writer.print_table(monthly_costs_df))
    buffer.write(report_writer.print_empty_line())
    buffer.write(report_writer.print_image(Path(f"{i}_monthly_breakdown.png"), "Monthly Breakdown"))

    affordability_df = pd.DataFrame({
        "Ratio": ["GDS (Gross Debt Service)", "TDS (Total Debt Service)"],
        "Value": [f"{_format_rate(row[K.GDS_RATIO])}%", f"{_format_rate(row[K.TDS_RATIO])}%"],
        "Guideline": [f"≤ {cfg.standard_banking_parameters.GDS}%", f"≤ {cfg.standard_banking_parameters.TDS}%"]
    })
    buffer.write(report_writer.print_header("Affordability Ratios", level=4))
    buffer.write(report_writer.print_table(affordability_df))
    buffer.write(report_writer.print_empty_line())
    buffer.write(report_writer.print_paragraph("*GDS = Total housing costs / Gross monthly income. TDS = (Housing costs + other debts) / Gross monthly income.*"))

    one_time_costs_df = pd.DataFrame({
        "Item": [f"Land Transfer Tax ({_format_rate(row[K.LAND_TRANSFER_TAX_RATE])}%)", "Notary Cost", "Inspection Cost", report_writer.print_bold("Total One-Time Costs")],
        "Amount": [f"${row[K.LAND_TRANSFER_TAX]:,.2f}", f"${row[K.NOTARY_COST]:,.2f}", f"${row[K.INSPECTION_COST]:,.2f}", report_writer.print_bold(f"${row[K.TOTAL_ONE_TIME_COSTS]:,.2f}")]
    })
    buffer.write(report_writer.print_header("One-Time Costs", level=4))
    buffer.write(report_writer.print_table(one_time_costs_df))
    buffer.write(report_writer.print_empty_line())
    buffer.write(report_writer.print_image(Path(f"{i}_one_time_breakdown.png"), "One-Time Breakdown"))
    buffer.write(report_writer.print_empty_line())

    cash_to_close_df = pd.DataFrame({
        "Item": ["Down Payment", "Total One-Time Costs", report_writer.print_bold("Estimated Cash to Close")],
        "Amount": [f"${cfg.loan_parameters.down_payment:,.2f}", f"${row[K.TOTAL_ONE_TIME_COSTS]:,.2f}", report_writer.print_bold(f"${row[K.CASH_TO_CLOSE]:,.2f}")]
    })
    buffer.write(report_writer.print_header("Cash to Close", level=4))
    buffer.write(report_writer.print_table(cash_to_close_df))

    yearly_costs_df = pd.DataFrame({
        "Item": [f"Property Tax ({_format_rate(row[K.PROPERTY_TAX_RATE])}%)", f"School Tax ({_format_rate(row[K.SCHOOL_TAX_RATE])}%)", "Home Insurance", report_writer.print_bold("Total Yearly Costs")],
        "Amount": [f"${row[K.YEARLY_PROPERTY_TAX]:,.2f}", f"${row[K.YEARLY_SCHOOL_TAX]:,.2f}", f"${row[K.YEARLY_HOME_INSURANCE]:,.2f}", report_writer.print_bold(f"${row[K.TOTAL_YEARLY_COSTS]:,.2f}")]
    })
    buffer.write(report_writer.print_header("Yearly Costs", level=4))
    buffer.write(report_writer.print_table(yearly_costs_df))
    buffer.write(report_writer.print_empty_line())
    buffer.write(report_writer.print_image(Path(f"{i}_yearly_breakdown.png"), "Yearly Breakdown"))


def _write_comparison_charts(buffer: io.StringIO, report_writer: ReportWriter) -> None:
    buffer.write(report_writer.print_header("Cost Comparison Charts", level=2))
    buffer.write(report_writer.print_header("Property Values by Property", level=3))
    buffer.write(report_writer.print_image("property_value_summary.png", "Property Values by Property"))
    buffer.write(report_writer.print_header("Total Monthly Costs by Property", level=3))
    buffer.write(report_writer.print_image("monthly_summary.png", "Total Monthly Costs by Property"))
    buffer.write(report_writer.print_header("Total Yearly Costs by Property", level=3))
    buffer.write(report_writer.print_image("yearly_summary.png", "Total Yearly Costs by Property"))
    buffer.write(report_writer.print_header("One-Time Costs by Property", level=3))
    buffer.write(report_writer.print_image("one_time_summary.png", "One-Time Costs by Property"))


def _write_comparison_table(buffer: io.StringIO, report_writer: ReportWriter, results: list[MortgageResult]) -> None:
    property_columns = [
        report_writer.print_link(f"Property {i}", report_writer.get_property_section_link(i))
        for i in range(1, len(results) + 1)
    ]

    comparison_rows: list[dict[str, str]] = []

    def _add_section_row(title: str) -> None:
        section_row = {"": report_writer.print_bold(title)}
        for property_col in property_columns:
            section_row[property_col] = ""
        comparison_rows.append(section_row)

    def _add_metric_row(label: str, values: list[str]) -> None:
        metric_row = {"": label}
        for property_col, value in zip(property_columns, values):
            metric_row[property_col] = value
        comparison_rows.append(metric_row)

    _add_section_row("Property Info")
    _add_metric_row("Address", [row[K.ADDRESS] or "—" for row in results])
    _add_metric_row("Description", [row[K.DESCRIPTION] or "—" for row in results])
    _add_metric_row(
        "Listing",
        [report_writer.print_link("View Listing", row[K.LINK]) if row[K.LINK] else "—" for row in results],
    )

    _add_section_row("Physical Details")
    _add_metric_row("Area (sqft)", [f"{row[K.AREA]:,}" for row in results])
    _add_metric_row("Bed/Bath", [f"{row[K.BEDROOMS]}/{row[K.BATHROOMS]}" for row in results])

    _add_section_row("Financial Overview")
    _add_metric_row("Property Value", [f"${row[K.PROPERTY_VALUE]:,.2f}" for row in results])
    _add_metric_row("Price/sqft", [f"${row[K.PRICE_PER_SQFT]:,.2f}" for row in results])
    _add_metric_row("Monthly Costs", [f"${row[K.TOTAL_MONTHLY_COSTS]:,.2f}" for row in results])
    _add_metric_row("Yearly Costs", [f"${row[K.TOTAL_YEARLY_COSTS]:,.2f}" for row in results])
    _add_metric_row("One-Time Costs", [f"${row[K.TOTAL_ONE_TIME_COSTS]:,.2f}" for row in results])
    _add_metric_row("Cash to Close", [f"${row[K.CASH_TO_CLOSE]:,.2f}" for row in results])

    _add_section_row("Affordability")
    _add_metric_row("GDS Ratio", [f"{_format_rate(row[K.GDS_RATIO])}%" for row in results])
    _add_metric_row("TDS Ratio", [f"{_format_rate(row[K.TDS_RATIO])}%" for row in results])

    main_comparison_df = pd.DataFrame(comparison_rows)
    buffer.write(report_writer.print_header("Side-by-Side Comparison", level=3))
    buffer.write(report_writer.print_table(main_comparison_df))
    buffer.write(report_writer.print_empty_line())


def _write_rankings(buffer: io.StringIO, report_writer: ReportWriter, results: list[MortgageResult]) -> None:
    sorted_by_monthly = sorted(enumerate(results, 1), key=lambda x: x[1][K.TOTAL_MONTHLY_COSTS])
    buffer.write(report_writer.print_paragraph(report_writer.print_bold("Lowest Monthly Costs:")))
    buffer.write(report_writer.print_list([f"{report_writer.print_link(f'Property {idx}', report_writer.get_property_section_link(idx))} - ${row[K.TOTAL_MONTHLY_COSTS]:,.2f}/month" for idx, row in sorted_by_monthly], numbered=True))
    buffer.write(report_writer.print_empty_line())

    sorted_by_value = sorted(
        enumerate(results, 1),
        key=lambda x: x[1][K.PRICE_PER_SQFT] if x[1][K.PRICE_PER_SQFT] > 0 else float('inf')
    )
    buffer.write(report_writer.print_paragraph(report_writer.print_bold("Best Value (Price/sqft):")))
    buffer.write(report_writer.print_list([f"{report_writer.print_link(f'Property {idx}', report_writer.get_property_section_link(idx))} - ${row[K.PRICE_PER_SQFT]:,.2f}/sqft" for idx, row in sorted_by_value], numbered=True))
    buffer.write(report_writer.print_empty_line())

    sorted_by_property_value = sorted(enumerate(results, 1), key=lambda x: x[1][K.PROPERTY_VALUE])
    buffer.write(report_writer.print_paragraph(report_writer.print_bold("Lowest Property Value:")))
    buffer.write(report_writer.print_list([f"{report_writer.print_link(f'Property {idx}', report_writer.get_property_section_link(idx))} - ${row[K.PROPERTY_VALUE]:,.2f}" for idx, row in sorted_by_property_value], numbered=True))
    buffer.write(report_writer.print_empty_line())

    sorted_by_area = sorted(enumerate(results, 1), key=lambda x: x[1][K.AREA] if x[1][K.AREA] else 0, reverse=True)
    buffer.write(report_writer.print_paragraph(report_writer.print_bold("Largest Area:")))
    buffer.write(report_writer.print_list([f"{report_writer.print_link(f'Property {idx}', report_writer.get_property_section_link(idx))} - {row[K.AREA]:,} sqft" for idx, row in sorted_by_area], numbered=True))
    buffer.write(report_writer.print_empty_line())

    sorted_by_rooms = sorted(enumerate(results, 1), key=lambda x: (x[1][K.BEDROOMS] or 0) + (x[1][K.BATHROOMS] or 0), reverse=True)
    buffer.write(report_writer.print_paragraph(report_writer.print_bold("Most Bedrooms + Bathrooms:")))
    buffer.write(report_writer.print_list([f"{report_writer.print_link(f'Property {idx}', report_writer.get_property_section_link(idx))} - {row[K.BEDROOMS]} bed / {row[K.BATHROOMS]} bath" for idx, row in sorted_by_rooms], numbered=True))
    buffer.write(report_writer.print_empty_line())

    sorted_by_gds = sorted(enumerate(results, 1), key=lambda x: x[1][K.GDS_RATIO])
    buffer.write(report_writer.print_paragraph(report_writer.print_bold("Lowest GDS Ratio:")))
    buffer.write(report_writer.print_list([f"{report_writer.print_link(f'Property {idx}', report_writer.get_property_section_link(idx))} - {_format_rate(row[K.GDS_RATIO])}%" for idx, row in sorted_by_gds], numbered=True))
    buffer.write(report_writer.print_empty_line())

    sorted_by_tds = sorted(enumerate(results, 1), key=lambda x: x[1][K.TDS_RATIO])
    buffer.write(report_writer.print_paragraph(report_writer.print_bold("Lowest TDS Ratio:")))
    buffer.write(report_writer.print_list([f"{report_writer.print_link(f'Property {idx}', report_writer.get_property_section_link(idx))} - {_format_rate(row[K.TDS_RATIO])}%" for idx, row in sorted_by_tds], numbered=True))
    buffer.write(report_writer.print_empty_line())


def _write_property_comparison_summary(buffer: io.StringIO, report_writer: ReportWriter, results: list[MortgageResult]) -> None:
    buffer.write(report_writer.print_header("Property Comparison Summary", level=2))
    buffer.write(report_writer.print_empty_line())
    _write_comparison_table(buffer, report_writer, results)
    buffer.write(report_writer.print_header("Rankings", level=3))
    _write_rankings(buffer, report_writer, results)


def generate_report(report_type: str, output_report_file_name: Path, affordability: CalculatedAffordability, results: list[MortgageResult], cfg: PropertiesListConfig) -> None:
    if not results:
        raise ValueError("Cannot generate report with empty results")

    report_writer = get_class_by_value(report_type)
    output_report_file = output_report_file_name.with_suffix(f".{report_writer.get_extension()}")

    try:
        output_report_file.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise ReportGenerationError(f"Failed to create output directory {output_report_file.parent}: {e}") from e

    with io.StringIO() as buffer:
        buffer.write(report_writer.initialize_report("Mortgage Calculation Report"))
        buffer.write(report_writer.print_paragraph(f"{report_writer.print_bold('Total Properties Analyzed:')} {len(results)}"))

        _write_personal_financial_details(buffer, report_writer, cfg, affordability)

        buffer.write(report_writer.print_header("Properties Analyzed", level=2))
        for i, row in enumerate(results, 1):
            _write_single_property(buffer, report_writer, i, row, cfg)

        _write_comparison_charts(buffer, report_writer)
        _write_property_comparison_summary(buffer, report_writer, results)

        buffer.write(report_writer.finalize_report())

        try:
            with open(output_report_file, 'w', encoding='utf-8') as f:
                f.write(buffer.getvalue())
        except OSError as e:
            raise ReportGenerationError(f"Failed to write report to {output_report_file}: {e}") from e
