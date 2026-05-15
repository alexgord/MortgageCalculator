from pathlib import Path
import logging
import io

import pandas as pd

from config_dataclasses import PropertiesListConfig
from custom_types import MortgageInformation, MortgageResult, ResultKeys as K

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

def _write_definitions_of_terms(buffer: io.StringIO, report_writer: ReportWriter) -> None:
    buffer.write(report_writer.print_header("Definitions of Key Terms", level=2))
    definitions = {
        "Down Payment": "The initial upfront portion of the total property price that you pay out of pocket. The remaining amount is financed through the mortgage loan.",
        "Loan Amount": "The amount of money you borrow from the lender to purchase the property, calculated as Property Value minus Down Payment.",
        "Interest Rate": "The annual percentage rate charged by the lender on the loan amount. The monthly rate is derived by dividing the annual rate by 12, which determines both your monthly payment and the total interest paid over the life of the loan.",
        "School Tax (Quebec-specific)": "An annual tax levied by school boards in Quebec, calculated as a percentage of the property's assessed value. It is separate from municipal property tax and is specific to Quebec; most other Canadian provinces do not have an equivalent.",
        "Land Transfer Tax / Welcome Tax (Quebec-specific)": "A one-time provincial tax paid by the buyer upon transfer of property ownership, known in Quebec as the 'Taxe de bienvenue' (Welcome Tax). It is calculated using progressive brackets applied to the property value. Most other Canadian provinces have a similar tax under different names, but the bracket rates vary by jurisdiction.",
        "Notary Cost (Quebec-specific)": "In Quebec, real estate transactions must be completed by a notary (notaire) rather than a real estate lawyer, as required by provincial law. The notary prepares and registers the deed of sale and mortgage deed. This cost does not apply in most other provinces, where a real estate lawyer performs the equivalent role.",
        "Inspection Cost": "The fee paid to a professional home inspector to assess the physical condition of a property before purchase. While not legally required, it is strongly recommended to identify defects or needed repairs.",
        "Cash to Close": "The total amount of liquid funds you must have available on closing day, calculated here as Down Payment plus all one-time costs (land transfer tax, notary, and inspection). This is the minimum amount you need in hand to complete the purchase.",
        "Annual Fixed Non-Mortgage Costs": "The sum of recurring yearly property expenses excluding the mortgage payment: property tax, school tax, home insurance, and condo fees. This figure represents the baseline carrying cost of the property regardless of financing.",
        "Total Paid Over Loan": "The total of all mortgage payments made over the full loan term (monthly payment × number of months). This covers both principal repayment and interest, but excludes all other costs such as taxes, insurance, and condo fees.",
        "Total Cost of Ownership Over Loan": "The estimated cumulative cost of owning the property over the full loan term, calculated as the down payment plus total monthly costs (mortgage, taxes, insurance, condo fees) × number of months. This is a simplified estimate and does not account for changes in tax rates, insurance premiums, or other variable costs over time.",
        "GDS Ratio": "Gross Debt Service Ratio — a Canadian banking guideline (not commonly used internationally) representing the percentage of gross monthly income consumed by housing costs: mortgage payment, property taxes, school taxes, home insurance, and condo fees. Lenders use this to assess whether you can afford the property's carrying costs.",
        "TDS Ratio": "Total Debt Service Ratio — a Canadian banking guideline (not commonly used internationally) representing the percentage of gross monthly income consumed by all debt payments: housing costs (as counted in GDS) plus other monthly obligations such as car loans and credit card payments. Lenders use this to assess your overall debt load."
    }
    for term, definition in definitions.items():
        buffer.write(report_writer.print_header(term, level=3))
        buffer.write(report_writer.print_paragraph(definition))
    buffer.write(report_writer.print_empty_line())

def _write_personal_financial_details(buffer: io.StringIO, report_writer: ReportWriter, cfg: PropertiesListConfig, affordability: CalculatedAffordability) -> None:
    personal_details_df = pd.DataFrame({
        "Item": ["Down Payment",
                 "Monthly Salary (Gross)",
                 "Yearly Salary (Gross)",
                 "Monthly Debt Payments",
                 report_writer.print_bold("*Maximum Monthly Mortgage Payment"),
                 report_writer.print_bold("*Maximum Mortgage Amount"),
                 report_writer.print_bold("*Maximum Property Value")],
        "Value": [f"${cfg.loan_parameters.down_payment:,.2f}",
                  f"${cfg.loan_parameters.monthly_salary:,.2f}",
                  f"${affordability.yearly_salary:,.2f}",
                  f"${cfg.loan_parameters.monthly_debt_payment:,.2f}",
                  f"${affordability.max_monthly_payment:,.2f}",
                  f"${affordability.max_loan_amount:,.2f}",
                  f"${affordability.max_property_value:,.2f}"]
    })
    buffer.write(report_writer.print_header("Personal Financial Details", level=2))
    buffer.write(report_writer.print_table(personal_details_df))
    buffer.write(report_writer.print_empty_line())

    maximum_mortgage_warning = (
        "*Note: These maximums are theoretical ceilings based on standard banking guidelines (GDS and TDS) and do not guarantee loan approval. Actual approved amounts may vary based on lender criteria and other factors. "
        "Maximum mortgage amount assumes all other costs are zero, such as property taxes, insurance, and condo fees. In reality, these costs will reduce the maximum mortgage amount you may qualify for. "
        "Treat this value as a theoretical upper limit and sanity check rather than an exact figure you can expect to receive."
    )
    buffer.write(report_writer.print_paragraph(maximum_mortgage_warning))
    buffer.write(report_writer.print_empty_line())


def _write_single_property(buffer: io.StringIO, report_writer: ReportWriter, i: int, mortgage_information: MortgageInformation, cfg: PropertiesListConfig) -> None:
    buffer.write(report_writer.print_header(f"Property {i}", level=3))

    if mortgage_information.mortgage_result[K.ADDRESS]:
        buffer.write(report_writer.print_paragraph(f"{report_writer.print_bold('Address:')} {report_writer.print_link(mortgage_information.mortgage_result[K.ADDRESS], mortgage_information.mortgage_result[K.GOOGLE_MAPS_LINK])}"))

    if mortgage_information.mortgage_result[K.DESCRIPTION]:
        buffer.write(report_writer.print_paragraph(f"{report_writer.print_bold('Description:')} {mortgage_information.mortgage_result[K.DESCRIPTION] or 'No Description'}"))

    if mortgage_information.mortgage_result[K.LINK]:
        buffer.write(report_writer.print_paragraph(f"{report_writer.print_bold('Link:')} {report_writer.print_link('View Listing', mortgage_information.mortgage_result[K.LINK])}"))

    if 'pros' in mortgage_information.property_config.keys():
        buffer.write(report_writer.print_paragraph(report_writer.print_bold("Pros:")))
        buffer.write(report_writer.print_list(mortgage_information.property_config.pros))

    if 'cons' in mortgage_information.property_config.keys():
        buffer.write(report_writer.print_paragraph(report_writer.print_bold("Cons:")))
        buffer.write(report_writer.print_list(mortgage_information.property_config.cons))

    if 'status' in mortgage_information.property_config.keys():
        buffer.write(report_writer.print_paragraph(f"{report_writer.print_bold('Status:')} {mortgage_information.property_config.status}"))

    property_details_df = pd.DataFrame({
        "Item": [
            "Property Value",
            "Price/sqft",
            "Area",
            "Year Built",
            "Bedrooms",
            "Bathrooms",
        ],
        "Value": [
            f"${mortgage_information.mortgage_result[K.PROPERTY_VALUE]:,.2f}",
            f"${mortgage_information.mortgage_result[K.PRICE_PER_SQFT]:,.2f}",
            f"{mortgage_information.mortgage_result[K.AREA]} sqft",
            f"{mortgage_information.mortgage_result[K.YEAR_BUILT]}",
            f"{mortgage_information.mortgage_result[K.BEDROOMS]}",
            f"{mortgage_information.mortgage_result[K.BATHROOMS]}",
        ]
    })
    buffer.write(report_writer.print_header("Property Details", level=4))
    buffer.write(report_writer.print_table(property_details_df))
    buffer.write(report_writer.print_empty_line())

    loan_details_df = pd.DataFrame({
        "Item": [
            "Loan Amount",
            "Interest Rate",
            "Loan Term"
            ],
        "Value": [
            f"${mortgage_information.mortgage_result[K.LOAN_AMOUNT]:,.2f}",
            f"{_format_rate(mortgage_information.mortgage_result[K.INTEREST_RATE])}%",
            f"{mortgage_information.mortgage_result[K.YEARS_OF_LOAN]} years",
        ]
    })
    buffer.write(report_writer.print_header("Loan Details", level=4))
    buffer.write(report_writer.print_table(loan_details_df))
    buffer.write(report_writer.print_empty_line())

    interest_rate_df = pd.DataFrame({
        "Item": [
            "Monthly Interest (Initial)",
            "Yearly Interest (Initial)",
            "Total Interest (Loan Term)"
        ],
        "Value": [
            f"${mortgage_information.mortgage_result[K.MONTHLY_INTEREST]:,.2f}",
            f"${mortgage_information.mortgage_result[K.YEARLY_INTEREST]:,.2f}",
            f"${mortgage_information.mortgage_result[K.TOTAL_INTEREST]:,.2f}",
        ]
    })
    buffer.write(report_writer.print_header("Interest Rate Over Time", level=4))
    buffer.write(report_writer.print_table(interest_rate_df))
    buffer.write(report_writer.print_empty_line())

    monthly_costs_df = pd.DataFrame({
        "Item": ["Mortgage Payment", "Condo Fees", "Property Tax (Amortized)", "School Tax (Amortized)", "Home Insurance (Amortized)", report_writer.print_bold("Total Monthly Costs")],
        "Amount": [f"${mortgage_information.mortgage_result[K.MONTHLY_MORTGAGE_PAYMENT]:,.2f}", f"${mortgage_information.mortgage_result[K.CONDO_FEES]:,.2f}", f"${mortgage_information.mortgage_result[K.MONTHLY_PROPERTY_TAX]:,.2f}", f"${mortgage_information.mortgage_result[K.MONTHLY_SCHOOL_TAX]:,.2f}", f"${mortgage_information.mortgage_result[K.MONTHLY_HOME_INSURANCE]:,.2f}", report_writer.print_bold(f"${mortgage_information.mortgage_result[K.TOTAL_MONTHLY_COSTS]:,.2f}")]
    })
    buffer.write(report_writer.print_header("Monthly Costs", level=4))
    buffer.write(report_writer.print_table(monthly_costs_df))
    buffer.write(report_writer.print_empty_line())
    buffer.write(report_writer.print_image(Path(f"{i}_monthly_breakdown.png"), "Monthly Breakdown"))

    tds_value = mortgage_information.mortgage_result[K.TDS_RATIO]
    gds_value = mortgage_information.mortgage_result[K.GDS_RATIO]

    buffer.write(report_writer.print_header("Affordability Ratios", level=4))

    affordability_df = pd.DataFrame({
        "Ratio": ["*GDS (Gross Debt Service)", "*TDS (Total Debt Service)"] if tds_value != gds_value else ["*GDS/TDS (Gross/Total Debt Service)"],
        "Value": [f"{_format_rate(mortgage_information.mortgage_result[K.GDS_RATIO])}%", f"{_format_rate(mortgage_information.mortgage_result[K.TDS_RATIO])}%"] if tds_value != gds_value else [f"{_format_rate(tds_value)}%"],
        "Guideline": [f"≤ {cfg.standard_banking_parameters.GDS}%", f"≤ {cfg.standard_banking_parameters.TDS}%"] if tds_value != gds_value else [f"≤ {cfg.standard_banking_parameters.GDS} / {cfg.standard_banking_parameters.TDS}%"]
    })

    buffer.write(report_writer.print_table(affordability_df))
    buffer.write(report_writer.print_empty_line())
    buffer.write(report_writer.print_paragraph("*GDS = Total housing costs / Gross monthly income. TDS = (Housing costs + other debts) / Gross monthly income.*"))

    land_transfer_tax_brackets_df = pd.DataFrame(
        {
            "Rate": [f"{_format_rate(bracket.rate)}%" for bracket in mortgage_information.property_config.land_transfer_tax_brackets],
            "Above": [f"${bracket.threshold:,.2f}" for bracket in mortgage_information.property_config.land_transfer_tax_brackets]
        }
    )

    buffer.write(report_writer.print_header("Land Transfer Tax Brackets", level=4))
    buffer.write(report_writer.print_table(land_transfer_tax_brackets_df))

    one_time_costs_df = pd.DataFrame({
        "Item": [f"Land Transfer Tax", "Notary Cost", "Inspection Cost", report_writer.print_bold("Total One-Time Costs")],
        "Amount": [f"${mortgage_information.mortgage_result[K.LAND_TRANSFER_TAX]:,.2f}", f"${mortgage_information.mortgage_result[K.NOTARY_COST]:,.2f}", f"${mortgage_information.mortgage_result[K.INSPECTION_COST]:,.2f}", report_writer.print_bold(f"${mortgage_information.mortgage_result[K.TOTAL_ONE_TIME_COSTS]:,.2f}")]
    })
    buffer.write(report_writer.print_header("One-Time Costs", level=4))
    buffer.write(report_writer.print_table(one_time_costs_df))
    buffer.write(report_writer.print_empty_line())
    buffer.write(report_writer.print_image(Path(f"{i}_one_time_breakdown.png"), "One-Time Breakdown"))
    buffer.write(report_writer.print_empty_line())

    cash_to_close_df = pd.DataFrame({
        "Item": ["Down Payment", "Total One-Time Costs", report_writer.print_bold("Estimated Cash to Close")],
        "Amount": [f"${cfg.loan_parameters.down_payment:,.2f}", f"${mortgage_information.mortgage_result[K.TOTAL_ONE_TIME_COSTS]:,.2f}", report_writer.print_bold(f"${mortgage_information.mortgage_result[K.CASH_TO_CLOSE]:,.2f}")]
    })
    buffer.write(report_writer.print_header("Cash to Close", level=4))
    buffer.write(report_writer.print_table(cash_to_close_df))

    yearly_costs_df = pd.DataFrame({
        "Item": [f"Property Tax ({_format_rate(mortgage_information.mortgage_result[K.PROPERTY_TAX_RATE])}%)", f"School Tax ({_format_rate(mortgage_information.mortgage_result[K.SCHOOL_TAX_RATE])}%)", "Home Insurance", "Condo Fees (Yearly)", report_writer.print_bold("Annual Fixed Non-Mortgage Costs"), report_writer.print_bold("Total Yearly Mortgage Payment"), report_writer.print_bold("Total Yearly Costs")],
        "Amount": [f"${mortgage_information.mortgage_result[K.YEARLY_PROPERTY_TAX]:,.2f}", f"${mortgage_information.mortgage_result[K.YEARLY_SCHOOL_TAX]:,.2f}", f"${mortgage_information.mortgage_result[K.YEARLY_HOME_INSURANCE]:,.2f}", f"${mortgage_information.mortgage_result[K.YEARLY_CONDO_FEE_COST]:,.2f}", report_writer.print_bold(f"${mortgage_information.mortgage_result[K.ANNUAL_FIXED_NON_MORTGAGE_COSTS]:,.2f}"), report_writer.print_bold(f"${mortgage_information.mortgage_result[K.YEARLY_MORTGAGE_PAYMENT]:,.2f}"), report_writer.print_bold(f"${mortgage_information.mortgage_result[K.TOTAL_YEARLY_COSTS]:,.2f}")]
    })
    buffer.write(report_writer.print_header("Yearly Costs", level=4))
    buffer.write(report_writer.print_table(yearly_costs_df))
    buffer.write(report_writer.print_empty_line())
    buffer.write(report_writer.print_image(Path(f"{i}_yearly_breakdown.png"), "Yearly Breakdown"))

    cost_over_loan_df = pd.DataFrame({
        "Item": ["Total Paid Over Loan", "Total Cost of Ownership Over Loan (Excl. Down Payment)", report_writer.print_bold("Total Cost of Ownership Over Loan")],
        "Amount": [f"${mortgage_information.mortgage_result[K.TOTAL_PAID_OVER_LOAN]:,.2f}", f"${mortgage_information.mortgage_result[K.TOTAL_COST_OF_OWNERSHIP_OVER_LOAN_WITHOUT_DOWN_PAYMENT]:,.2f}", report_writer.print_bold(f"${mortgage_information.mortgage_result[K.TOTAL_COST_OF_OWNERSHIP_OVER_LOAN]:,.2f}")]
    })
    buffer.write(report_writer.print_header("Cost Over Loan Term", level=4))
    buffer.write(report_writer.print_table(cost_over_loan_df))


def _write_comparison_charts(buffer: io.StringIO, report_writer: ReportWriter) -> None:
    buffer.write(report_writer.print_header("Cost Comparison Charts", level=2))
    buffer.write(report_writer.print_header("Property Values by Property", level=3))
    buffer.write(report_writer.print_image("property_value_summary.png", "Property Values by Property"))
    buffer.write(report_writer.print_header("Total Monthly Costs by Property", level=3))
    buffer.write(report_writer.print_image("monthly_summary.png", "Total Monthly Costs by Property"))
    buffer.write(report_writer.print_header("Monthly Mortgage Payment by Property", level=3))
    buffer.write(report_writer.print_image("monthly_mortgage_summary.png", "Monthly Mortgage Payment by Property"))
    buffer.write(report_writer.print_header("Monthly Condo Fees by Property", level=3))
    buffer.write(report_writer.print_image("monthly_condo_fees_summary.png", "Monthly Condo Fees by Property"))
    buffer.write(report_writer.print_header("Price per Square Foot by Property", level=3))
    buffer.write(report_writer.print_image("price_per_sqft_summary.png", "Price per Square Foot by Property"))
    buffer.write(report_writer.print_header("Annual Fixed Non-Mortgage Costs by Property", level=3))
    buffer.write(report_writer.print_image("annual_fixed_non_mortgage_costs_summary.png", "Annual Fixed Non-Mortgage Costs by Property"))
    buffer.write(report_writer.print_header("Total Yearly Costs by Property", level=3))
    buffer.write(report_writer.print_image("yearly_cost_summary.png", "Total Yearly Costs by Property"))
    buffer.write(report_writer.print_header("One-Time Costs by Property", level=3))
    buffer.write(report_writer.print_image("one_time_summary.png", "One-Time Costs by Property"))


def _write_comparison_table(buffer: io.StringIO, report_writer: ReportWriter, mortgage_information_list: list[MortgageInformation]) -> None:
    property_columns = [
        report_writer.print_link(f"Property {i}", report_writer.get_property_section_link(i))
        for i in range(1, len(mortgage_information_list) + 1)
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
    _add_metric_row("Address", [report_writer.print_link(mortgage_information.mortgage_result[K.ADDRESS], mortgage_information.mortgage_result[K.GOOGLE_MAPS_LINK]) if mortgage_information.mortgage_result[K.ADDRESS] else "—" for mortgage_information in mortgage_information_list])
    _add_metric_row("Description", [mortgage_information.mortgage_result[K.DESCRIPTION] or "—" for mortgage_information in mortgage_information_list])
    _add_metric_row(
        "Listing",
        [report_writer.print_link("View Listing", mortgage_information.mortgage_result[K.LINK]) if mortgage_information.mortgage_result[K.LINK] else "—" for mortgage_information in mortgage_information_list],
    )

    _add_section_row("Physical Details")
    _add_metric_row("Area (sqft)", [f"{mortgage_information.mortgage_result[K.AREA]:,}" for mortgage_information in mortgage_information_list])
    _add_metric_row("Bed/Bath", [f"{mortgage_information.mortgage_result[K.BEDROOMS]}/{mortgage_information.mortgage_result[K.BATHROOMS]}" for mortgage_information in mortgage_information_list])

    _add_section_row("Financial Overview")
    _add_metric_row("Property Value", [f"${mortgage_information.mortgage_result[K.PROPERTY_VALUE]:,.2f}" for mortgage_information in mortgage_information_list])
    _add_metric_row("Price/sqft", [f"${mortgage_information.mortgage_result[K.PRICE_PER_SQFT]:,.2f}" for mortgage_information in mortgage_information_list])
    _add_section_row("Loan Details")
    _add_metric_row("Loan Amount", [f"${mortgage_information.mortgage_result[K.LOAN_AMOUNT]:,.2f}" for mortgage_information in mortgage_information_list])
    _add_metric_row("Monthly Interest (Initial)", [f"${mortgage_information.mortgage_result[K.MONTHLY_INTEREST]:,.2f}" for mortgage_information in mortgage_information_list])
    _add_metric_row("Yearly Interest (Initial)", [f"${mortgage_information.mortgage_result[K.YEARLY_INTEREST]:,.2f}" for mortgage_information in mortgage_information_list])
    _add_metric_row("Total Interest", [f"${mortgage_information.mortgage_result[K.TOTAL_INTEREST]:,.2f}" for mortgage_information in mortgage_information_list])
    _add_section_row("Monthly Costs")
    _add_metric_row("Monthly Mortgage Payment", [f"${mortgage_information.mortgage_result[K.MONTHLY_MORTGAGE_PAYMENT]:,.2f}" for mortgage_information in mortgage_information_list])
    _add_metric_row("Condo Fees", [f"${mortgage_information.mortgage_result[K.CONDO_FEES]:,.2f}" for mortgage_information in mortgage_information_list])
    _add_metric_row("Monthly Property Tax", [f"${mortgage_information.mortgage_result[K.MONTHLY_PROPERTY_TAX]:,.2f}" for mortgage_information in mortgage_information_list])
    _add_metric_row("Monthly School Tax", [f"${mortgage_information.mortgage_result[K.MONTHLY_SCHOOL_TAX]:,.2f}" for mortgage_information in mortgage_information_list])
    _add_metric_row("Monthly Home Insurance", [f"${mortgage_information.mortgage_result[K.MONTHLY_HOME_INSURANCE]:,.2f}" for mortgage_information in mortgage_information_list])
    _add_metric_row("Total Monthly Costs", [f"${mortgage_information.mortgage_result[K.TOTAL_MONTHLY_COSTS]:,.2f}" for mortgage_information in mortgage_information_list])
    _add_section_row("Annual Costs")
    _add_metric_row("Property Tax", [f"${mortgage_information.mortgage_result[K.YEARLY_PROPERTY_TAX]:,.2f}" for mortgage_information in mortgage_information_list])
    _add_metric_row("School Tax", [f"${mortgage_information.mortgage_result[K.YEARLY_SCHOOL_TAX]:,.2f}" for mortgage_information in mortgage_information_list])
    _add_metric_row("Home Insurance", [f"${mortgage_information.mortgage_result[K.YEARLY_HOME_INSURANCE]:,.2f}" for mortgage_information in mortgage_information_list])
    _add_metric_row("Condo Fees (Yearly)", [f"${mortgage_information.mortgage_result[K.YEARLY_CONDO_FEE_COST]:,.2f}" for mortgage_information in mortgage_information_list])
    _add_metric_row("Annual Non-Mortgage Costs", [f"${mortgage_information.mortgage_result[K.ANNUAL_FIXED_NON_MORTGAGE_COSTS]:,.2f}" for mortgage_information in mortgage_information_list])
    _add_metric_row("Total Yearly Mortgage Payment", [f"${mortgage_information.mortgage_result[K.YEARLY_MORTGAGE_PAYMENT]:,.2f}" for mortgage_information in mortgage_information_list])
    _add_metric_row("Total Yearly Costs", [f"${mortgage_information.mortgage_result[K.TOTAL_YEARLY_COSTS]:,.2f}" for mortgage_information in mortgage_information_list])
    _add_section_row("One-Time Costs")
    _add_metric_row("Land Transfer Tax", [f"${mortgage_information.mortgage_result[K.LAND_TRANSFER_TAX]:,.2f}" for mortgage_information in mortgage_information_list])
    _add_metric_row("Notary Cost", [f"${mortgage_information.mortgage_result[K.NOTARY_COST]:,.2f}" for mortgage_information in mortgage_information_list])
    _add_metric_row("Inspection Cost", [f"${mortgage_information.mortgage_result[K.INSPECTION_COST]:,.2f}" for mortgage_information in mortgage_information_list])
    _add_metric_row("Total One-Time Costs", [f"${mortgage_information.mortgage_result[K.TOTAL_ONE_TIME_COSTS]:,.2f}" for mortgage_information in mortgage_information_list])
    _add_metric_row("Cash to Close", [f"${mortgage_information.mortgage_result[K.CASH_TO_CLOSE]:,.2f}" for mortgage_information in mortgage_information_list])
    _add_section_row("Cost Over Loan Term")
    _add_metric_row("Total Paid Over Loan", [f"${mortgage_information.mortgage_result[K.TOTAL_PAID_OVER_LOAN]:,.2f}" for mortgage_information in mortgage_information_list])
    _add_metric_row("Total Cost of Ownership Over Loan (Excluding Down Payment)", [f"${mortgage_information.mortgage_result[K.TOTAL_COST_OF_OWNERSHIP_OVER_LOAN_WITHOUT_DOWN_PAYMENT]:,.2f}" for mortgage_information in mortgage_information_list])
    _add_metric_row("Total Cost of Ownership Over Loan", [f"${mortgage_information.mortgage_result[K.TOTAL_COST_OF_OWNERSHIP_OVER_LOAN]:,.2f}" for mortgage_information in mortgage_information_list])
    

    _add_section_row("Affordability")

    tds_ratio_values = [mortgage_information.mortgage_result[K.TDS_RATIO] for mortgage_information in mortgage_information_list]
    gds_ratio_values = [mortgage_information.mortgage_result[K.GDS_RATIO] for mortgage_information in mortgage_information_list]
    if tds_ratio_values == gds_ratio_values:
         _add_metric_row("GDS/TDS Ratio", [f"{_format_rate(mortgage_information.mortgage_result[K.GDS_RATIO])}%" for mortgage_information in mortgage_information_list])
    else:
        _add_metric_row("GDS Ratio", [f"{_format_rate(mortgage_information.mortgage_result[K.GDS_RATIO])}%" for mortgage_information in mortgage_information_list])
        _add_metric_row("TDS Ratio", [f"{_format_rate(mortgage_information.mortgage_result[K.TDS_RATIO])}%" for mortgage_information in mortgage_information_list])

    _add_section_row("Notes")
    _add_metric_row("Pros", [report_writer.print_list(mortgage_information.property_config.pros if 'pros' in mortgage_information.property_config.keys() else ["—"], inline=True) for mortgage_information in mortgage_information_list])
    _add_metric_row("Cons", [report_writer.print_list(mortgage_information.property_config.cons if 'cons' in mortgage_information.property_config.keys() else ["—"], inline=True) for mortgage_information in mortgage_information_list])
    _add_metric_row("Status", [mortgage_information.property_config.status if 'status' in mortgage_information.property_config.keys() else "—" for mortgage_information in mortgage_information_list])

    main_comparison_df = pd.DataFrame(comparison_rows)
    buffer.write(report_writer.print_header("Side-by-Side Comparison", level=3))
    buffer.write(report_writer.print_table(main_comparison_df))
    buffer.write(report_writer.print_empty_line())


def _write_rankings(buffer: io.StringIO, report_writer: ReportWriter, mortgage_information_list: list[MortgageInformation]) -> None:
    sorted_by_monthly = sorted(enumerate(mortgage_information_list, 1), key=lambda x: x[1].mortgage_result[K.TOTAL_MONTHLY_COSTS])
    buffer.write(report_writer.print_paragraph(report_writer.print_bold("Lowest Monthly Costs:")))
    buffer.write(report_writer.print_list([f"{report_writer.print_link(f'Property {idx}', report_writer.get_property_section_link(idx))} - ${mortgage_information.mortgage_result[K.TOTAL_MONTHLY_COSTS]:,.2f}/month" for idx, mortgage_information in sorted_by_monthly], numbered=True))
    buffer.write(report_writer.print_empty_line())

    sorted_by_value = sorted(
        enumerate(mortgage_information_list, 1),
        key=lambda x: x[1].mortgage_result[K.PRICE_PER_SQFT] if x[1].mortgage_result[K.PRICE_PER_SQFT] > 0 else float('inf')
    )
    buffer.write(report_writer.print_paragraph(report_writer.print_bold("Best Value (Price/sqft):")))
    buffer.write(report_writer.print_list([f"{report_writer.print_link(f'Property {idx}', report_writer.get_property_section_link(idx))} - ${mortgage_information.mortgage_result[K.PRICE_PER_SQFT]:,.2f}/sqft" for idx, mortgage_information in sorted_by_value], numbered=True))
    buffer.write(report_writer.print_empty_line())

    sorted_by_property_value = sorted(enumerate(mortgage_information_list, 1), key=lambda x: x[1].mortgage_result[K.PROPERTY_VALUE])
    buffer.write(report_writer.print_paragraph(report_writer.print_bold("Lowest Property Value:")))
    buffer.write(report_writer.print_list([f"{report_writer.print_link(f'Property {idx}', report_writer.get_property_section_link(idx))} - ${mortgage_information.mortgage_result[K.PROPERTY_VALUE]:,.2f}" for idx, mortgage_information in sorted_by_property_value], numbered=True))
    buffer.write(report_writer.print_empty_line())

    sorted_by_area = sorted(enumerate(mortgage_information_list, 1), key=lambda x: x[1].mortgage_result[K.AREA] if x[1].mortgage_result[K.AREA] else 0, reverse=True)
    buffer.write(report_writer.print_paragraph(report_writer.print_bold("Largest Area:")))
    buffer.write(report_writer.print_list([f"{report_writer.print_link(f'Property {idx}', report_writer.get_property_section_link(idx))} - {mortgage_information.mortgage_result[K.AREA]:,} sqft" for idx, mortgage_information in sorted_by_area], numbered=True))
    buffer.write(report_writer.print_empty_line())

    sorted_by_rooms = sorted(enumerate(mortgage_information_list, 1), key=lambda x: (x[1].mortgage_result[K.BEDROOMS] or 0) + (x[1].mortgage_result[K.BATHROOMS] or 0), reverse=True)
    buffer.write(report_writer.print_paragraph(report_writer.print_bold("Most Bedrooms + Bathrooms:")))
    buffer.write(report_writer.print_list([f"{report_writer.print_link(f'Property {idx}', report_writer.get_property_section_link(idx))} - {mortgage_information.mortgage_result[K.BEDROOMS]} bed / {mortgage_information.mortgage_result[K.BATHROOMS]} bath" for idx, mortgage_information in sorted_by_rooms], numbered=True))
    buffer.write(report_writer.print_empty_line())

    sorted_by_gds = sorted(enumerate(mortgage_information_list, 1), key=lambda x: x[1].mortgage_result[K.GDS_RATIO])
    buffer.write(report_writer.print_paragraph(report_writer.print_bold("Lowest GDS Ratio:")))
    buffer.write(report_writer.print_list([f"{report_writer.print_link(f'Property {idx}', report_writer.get_property_section_link(idx))} - {_format_rate(mortgage_information.mortgage_result[K.GDS_RATIO])}%" for idx, mortgage_information in sorted_by_gds], numbered=True))
    buffer.write(report_writer.print_empty_line())

    sorted_by_tds = sorted(enumerate(mortgage_information_list, 1), key=lambda x: x[1].mortgage_result[K.TDS_RATIO])
    buffer.write(report_writer.print_paragraph(report_writer.print_bold("Lowest TDS Ratio:")))
    buffer.write(report_writer.print_list([f"{report_writer.print_link(f'Property {idx}', report_writer.get_property_section_link(idx))} - {_format_rate(mortgage_information.mortgage_result[K.TDS_RATIO])}%" for idx, mortgage_information in sorted_by_tds], numbered=True))
    buffer.write(report_writer.print_empty_line())


def _write_property_comparison_summary(buffer: io.StringIO, report_writer: ReportWriter, mortgage_information_list: list[MortgageInformation]) -> None:
    buffer.write(report_writer.print_header("Property Comparison Summary", level=2))
    buffer.write(report_writer.print_empty_line())
    _write_comparison_table(buffer, report_writer, mortgage_information_list)
    buffer.write(report_writer.print_header("Rankings", level=3))
    _write_rankings(buffer, report_writer, mortgage_information_list)


def generate_report(report_type: str, output_report_file_name: Path, affordability: CalculatedAffordability, mortgage_information_list: list[MortgageInformation], cfg: PropertiesListConfig) -> None:
    if not mortgage_information_list:
        raise ValueError("Cannot generate report with empty results")

    report_writer = get_class_by_value(report_type)
    output_report_file = output_report_file_name.with_suffix(f".{report_writer.get_extension()}")

    try:
        output_report_file.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise ReportGenerationError(f"Failed to create output directory {output_report_file.parent}: {e}") from e

    with io.StringIO() as buffer:
        buffer.write(report_writer.initialize_report("Mortgage Calculation Report"))
        buffer.write(report_writer.print_paragraph(f"{report_writer.print_bold('Total Properties Analyzed:')} {len(mortgage_information_list)}"))

        _write_definitions_of_terms(buffer, report_writer)

        if cfg.useful_links:
            buffer.write(report_writer.print_header("Useful Links", level=2))
            
            buffer.write(report_writer.print_list([report_writer.print_link(link["name"], link["url"]) for link in cfg.useful_links]))

        _write_personal_financial_details(buffer, report_writer, cfg, affordability)

        buffer.write(report_writer.print_header("Properties Analyzed", level=2))
        for i, mortgage_information in enumerate(mortgage_information_list, 1):
            _write_single_property(buffer, report_writer, i, mortgage_information, cfg)

        _write_comparison_charts(buffer, report_writer)
        _write_property_comparison_summary(buffer, report_writer, mortgage_information_list)

        buffer.write(report_writer.finalize_report())

        try:
            with open(output_report_file, 'w', encoding='utf-8') as f:
                f.write(buffer.getvalue())
        except OSError as e:
            raise ReportGenerationError(f"Failed to write report to {output_report_file}: {e}") from e
