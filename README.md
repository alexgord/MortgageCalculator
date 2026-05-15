# Mortgage Calculator

Python mortgage analysis tool for comparing multiple properties side-by-side. The project uses [Hydra](https://hydra.cc/) for composable YAML configuration and generates CSV, Markdown, and HTML outputs with charts.

## Features

- Multi-property analysis in one run
- Composable config inheritance (province -> city -> property)
- Detailed breakdowns for:
  - Monthly costs
  - Yearly costs
  - One-time costs
- Affordability metrics:
  - GDS ratio
  - TDS ratio
  - Theoretical maximum mortgage ceiling (GDS/TDS bounded)
- Report sections:
  - Personal financial details (salary, debt, affordability ceiling)
  - Per-property breakdowns (monthly, yearly, one-time costs, cash to close, affordability ratios, land transfer tax brackets)
  - Per-property pros, cons, and status notes
  - Address links auto-resolved to Google Maps
  - Side-by-side comparison table across all properties (property info, physical details, monthly/annual/one-time costs, cost over loan term, affordability, notes)
  - Rankings (by monthly cost, price/sqft, property value, area, rooms, GDS/TDS)
  - Cost comparison charts
- Report generation in multiple formats via pluggable writers:
  - Markdown (`MarkdownWriter`)
  - HTML (`HTMLWriter`)
- Auto-generated charts for per-property breakdowns and global comparisons

## Installation

1. Clone the repository.
2. Create and activate a virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Quick Start

Run with the included example configuration:

```bash
python mortgagecalculator_batch.py -cd example_settings -cn property_list
```

Each run will:
1. Validate loan/expense settings and property settings.
2. Compute mortgage and cost metrics for each property.
3. Write CSV output to `output_dir/output_data`.
4. Generate comparison and breakdown charts in `output_dir`.
5. Generate one report file per value in `report_types` (for example `.md` and `.html`).

## Configuration

### Example Folder Structure

```text
example_settings/
  province_details.yaml
  city_details.yaml
  property1.yaml
  property2.yaml
  property_list.yaml
```

### Main Config (`property_list.yaml`)

```yaml
defaults:
  - property1@properties.property1
  - property2@properties.property2
  - _self_

output_dir: example_properties_output
output_data_format: csv
output_data: properties_summary.${output_data_format}
output_report: properties_report

report_types:
  - MarkdownWriter
  - HTMLWriter

chart:
  width: 6
  height: 4
  top_padding: 0.15
  dpi: 150

standard_banking_parameters:
  GDS: 32.0
  TDS: 40.0

loan_parameters:
  down_payment: 30000
  interest_rate: 3.57
  years_of_loan: 20
  monthly_salary: 2000
  monthly_debt_payment: 0

necessary_expenses:
  notary_cost: 1000
  inspection_cost: 200
```

Notes:
- `properties` is a dictionary populated through Hydra defaults (`@properties.<name>`).
- `output_report` is a basename. Extensions are added from `report_types`.
- `standard_banking_parameters` sets the GDS and TDS ratio thresholds (as percentages) used for affordability ceiling calculations.
- An optional `useful_links` list can be added at the top level:

```yaml
useful_links:
  - name: Bank rate calculator
    url: https://www.ratehub.ca/mortgage-payment-calculator
  - name: CMHC affordability tool
    url: https://www.cmhc-schl.gc.ca/consumers/home-buying/calculators
```

### Province Defaults (`province_details.yaml`)

```yaml
land_transfer_tax_brackets:
  - threshold: 276200
    rate: 1.5
  - threshold: 5520
    rate: 1.0
  - threshold: 0
    rate: 0.5
```

### City Defaults (`city_details.yaml`)

```yaml
defaults:
  - province_details
  - _self_

yearly_home_insurance: 200
property_tax: 0.4
school_tax: 0.1
```

### Property Config (`property1.yaml`)

```yaml
defaults:
  - city_details
  - _self_

description: Property 1 Description
address: "1234 Sesame Street, New York, NY 10001"
value: 200000
condo_fees: 200
link: https://www.sesamestreet.com/realestate/property1
bedrooms: 2
bathrooms: 1
area_sqft: 1000
year_built: 2000

# Optional notes
pros:
  - Close to transit
  - New kitchen
cons:
  - Small backyard
status: Available
```

The `pros`, `cons`, and `status` fields are optional. They appear in the per-property report section and in the side-by-side comparison table.

## Outputs

Typical output files:

- `properties_summary.csv`
- `properties_report.md` (when `MarkdownWriter` is enabled)
- `properties_report.html` (when `HTMLWriter` is enabled)
- Global comparison charts:
  - `monthly_summary.png`
  - `annual_fixed_non_mortgage_costs_summary.png`
  - `one_time_summary.png`
  - `property_value_summary.png`
- Per-property charts:
  - `{i}_monthly_breakdown.png`
  - `{i}_yearly_breakdown.png`
  - `{i}_one_time_breakdown.png`

### CSV Columns

The CSV includes a flattened `MortgageResult` per property, including:

- Property metadata: `Description`, `Address`, `Google_Maps_Link`, `Link`, `Bedrooms`, `Bathrooms`, `Area`, `Year_Built`
- Core financing: `Property_Value`, `Down_Payment`, `Loan_Amount`, `Interest_Rate`, `Years_of_Loan`
- Mortgage cost metrics: `Monthly_Mortgage_Payment`, `Monthly_Interest`, `Yearly_Interest`, `Total_Interest`
- Monthly costs and totals: `Condo_Fees`, `Monthly_Property_Tax`, `Monthly_School_Tax`, `Monthly_Home_Insurance`, `Total_Monthly_Costs`
- One-time costs and cash-to-close: `Land_Transfer_Tax_Rate`, `Land_Transfer_Tax`, `Notary_Cost`, `Inspection_Cost`, `Total_One_Time_Costs`, `Cash_to_Close`
- Yearly taxes/insurance and totals: `Yearly_Property_Tax`, `Yearly_School_Tax`, `Yearly_Home_Insurance`, `Annual_Fixed_Non_Mortgage_Costs`, `Yearly_Mortgage_Payment`, `Total_Yearly_Costs`
- Loan-term totals: `Total_Paid_Over_Loan`, `Total_Cost_of_Ownership_Over_Loan`, `Total_Cost_of_Ownership_Over_Loan_Without_Down_Payment`
- Value metric: `Price_Per_Sqft`
- Affordability metrics: `Monthly_Salary`, `Monthly_Debt_Payment`, `GDS_Ratio`, `TDS_Ratio`

`Google_Maps_Link` is auto-generated from `address` using the Google Maps search URL.

## How Calculations Work

### Monthly Mortgage Payment

Standard amortization formula:

$$
M = P \cdot \frac{r(1+r)^n}{(1+r)^n - 1}
$$

Where:
- $M$ is the monthly payment
- $P$ is the loan amount (`property value - down payment`)
- $r$ is the monthly interest rate (`annual rate / 12 / 100`)
- $n$ is total number of payments (`years * 12`)

Edge case: if yearly interest is `0`, payment is `loan_amount / (years * 12)`.

### Land Transfer Tax

Tax is calculated from configured `land_transfer_tax_brackets` (ordered by descending threshold), then applied as:

$$
Land\ Transfer\ Tax = Property\ Value \cdot Bracket\ Rate
$$

### Yearly Tax

$$
Yearly\ Tax = Property\ Value \cdot \frac{Tax\ Rate}{100}
$$

### Affordability Ceiling

The maximum monthly mortgage payment is the binding (lower) constraint of the GDS and TDS limits:

$$
\text{GDS max} = \frac{GDS\%}{100} \times \text{monthly salary}
$$

$$
\text{TDS max} = \frac{TDS\%}{100} \times \text{monthly salary} - \text{monthly debt payment}
$$

$$
\text{max payment} = \min(\text{GDS max},\ \text{TDS max})
$$

The mortgage payment formula is then inverted to derive the maximum loan principal:

$$
\text{max loan} = \text{max payment} \times \frac{(1+r)^n - 1}{r(1+r)^n} + \text{down payment}
$$

This is a theoretical ceiling — actual lender approval may differ.

## Runtime Overrides

Hydra lets you override any value from the command line:

```bash
python mortgagecalculator_batch.py -cd settings -cn properties_list loan_parameters.down_payment=150000
python mortgagecalculator_batch.py -cd settings -cn properties_list loan_parameters.interest_rate=5.5
python mortgagecalculator_batch.py -cd settings -cn properties_list output_dir=my_analysis
python mortgagecalculator_batch.py -cd settings -cn properties_list report_types=[MarkdownWriter]
```

## Validation and Errors

Before writing outputs, the app validates:

- Loan config (`interest_rate`, `years_of_loan`, `down_payment`, salary/debt values)
- Expense config (`notary_cost`, `inspection_cost`)
- Per-property values (`value`, taxes, fees, insurance, area)
- Land transfer tax bracket configuration (non-negative values + descending thresholds)
- Cross-field check: down payment must be less than property value

Invalid data raises `ValidationError` with a combined list of issues.

Report file writing failures raise `ReportGenerationError`.

## Project Structure

```text
mortgagecalculator_batch.py   # Entry point, Hydra integration, orchestration
mortgagecalculatorlib.py      # Core validation + mortgage calculations
reporting.py                  # Report assembly and writing
reportwriter.py               # Report writer interface + registry
markdownlib.py                # Markdown writer implementation
htmllib.py                    # HTML writer implementation
chart_service.py              # Chart generation service
config_dataclasses.py         # Structured config dataclasses
custom_types.py               # TypedDict result model and key constants
```

## Dependencies

- `hydra-core`
- `omegaconf`
- `pandas`
- `matplotlib`
- `selenium`

## License

MIT
