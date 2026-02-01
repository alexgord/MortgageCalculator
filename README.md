# Mortgage Calculator

A Python-based mortgage calculator that analyzes multiple properties and generates comprehensive reports with charts comparing costs. Uses [Hydra](https://hydra.cc/) for flexible, composable configuration management.

## Features

- **Multi-property analysis** - Compare multiple properties side-by-side
- **Composable configuration** - Define city-level defaults, reuse across properties
- **Comprehensive cost breakdown**:
  - Monthly costs (mortgage payment, condo fees)
  - Yearly costs (property tax, school tax, home insurance)
  - One-time costs (land transfer tax, notary, inspection)
- **Report generation**:
  - CSV summary for spreadsheet analysis
  - Markdown report with embedded charts
  - Bar charts comparing properties

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/MortgageCalculator.git
   cd MortgageCalculator
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   
   # Windows
   .venv\Scripts\activate
   
   # Linux/macOS
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Quick Start

Run the calculator with the default configuration:

```bash
python mortgagecalculator_batch.py -cd settings -cn properties_list
```

This will:
1. Load property configurations from `settings/`
2. Calculate mortgage details for each property
3. Generate a CSV summary at `properties_output/properties_summary.csv`
4. Generate a Markdown report with charts at `properties_output/properties_report.md`

## Configuration

### Example Settings Structure

```
example_settings/
├── city_details.yaml         # City-level defaults (taxes, insurance)
├── property1.yaml            # Example property
├── property2.yaml            # Example property
└── property_list.yaml        # Example main config
```

### Example Main Configuration (`properties_list.yaml`)

```yaml
defaults:
  - property1@property1       # Include property1.yaml as ${property1}
  - property2@property2       # Include property2.yaml as ${property2}
  - _self_
output_dir: properties_output
output_data_format: csv
output_data: properties_summary.${output_data_format}
output_report_format: md
output_report: properties_report.${output_report_format}
chart:
  width: 5                    # Chart width in inches
  height: 3                   # Chart height in inches
  top_padding: 0.15           # Padding above bars for labels
  dpi: 150                    # Image resolution
loan_parameters:
  down_payment: 30000        # Your down payment amount
  interest_rate: 3.5         # Annual interest rate (%)
  years_of_loan: 20          # Mortgage term in years
  monthly_salary: 2000       # Your monthly salary (for % calculation)
necessary_expenses:
  notary_cost: 1000          # One-time notary fees
  inspection_cost: 200       # One-time inspection cost
properties:
  - ${property1}             # Reference to included property
  - ${property2}
```

### Example City Defaults (`city_details.yaml`)

Define common values for a city/region:

```yaml
home_insurance: 200           # Yearly home insurance
property_tax: 0.4             # Property tax rate (%)
school_tax: 0.1               # School tax rate (%)
```

### Example Property Configuration (`property1.yaml`)

```yaml
defaults:
  - city_details                        # Inherit city defaults
  - _self_

description: "Cozy 2BR condo"
address: "1234 Sesame Stree, New York, NY 10001"
value: 200000                           # Property price
condo_fees: 200                         # Monthly condo fees
link: https://example.com/listing       # The URL for the listing

# Optional metadata
bedrooms: 2
bathrooms: 1
area_sqft: 1000
year_built: 2005

# Override city defaults if needed
# property_tax: 0.5
```

## Output

### CSV Summary

The CSV file contains all calculated values for each property:

| Column | Description |
|--------|-------------|
| Description | Property description |
| Address | Property address |
| Property_Value | Listed price |
| Down_Payment | Your down payment |
| Principal | Loan amount (value - down payment) |
| Interest_Rate | Annual interest rate |
| Monthly_Mortgage_Payment | Monthly mortgage amount |
| Condo_Fees | Monthly condo fees |
| Total_Monthly_Costs | Total monthly expenses |
| Percentage_of_Salary | Monthly costs as % of salary |
| Land_Transfer_Tax | Quebec land transfer tax |
| Total_One_Time_Costs | All one-time expenses |
| Yearly_Property_Tax | Annual property tax |
| Yearly_School_Tax | Annual school tax |
| Total_Yearly_Costs | All yearly expenses |

### Markdown Report

The report includes:
- Summary of your financial parameters
- Per-property breakdown with:
  - Property details and listing link
  - Monthly cost breakdown table + chart
  - One-time cost breakdown table + chart
  - Yearly cost breakdown table + chart
- Comparison charts across all properties:
  - Property values
  - Total monthly costs
  - Total yearly costs
  - One-time costs

## How It Works

### Calculation Formulas

**Monthly Mortgage Payment** (standard amortization formula):
```
M = P * [r(1+r)^n] / [(1+r)^n - 1]

Where:
  M = Monthly payment
  P = Principal (property value - down payment)
  r = Monthly interest rate (annual rate / 12 / 100)
  n = Total number of payments (years × 12)
```

**Land Transfer Tax** (Quebec rates):
- Property value > $276,200: 1.5%
- Property value > $5,520: 1.0%
- Property value ≤ $5,520: 0.5%

**Yearly Taxes**:
```
Tax = Property Value × (Tax Rate / 100)
```

### Architecture

```
mortgagecalculator_batch.py   # Entry point, Hydra integration
├── mortgagecalculatorlib.py  # Core calculation logic
│   ├── CalculatedMortgage    # Main calculation class
│   ├── validate_property_config()
│   └── calculate_*() functions
├── reportinglib.py           # Report generation
│   ├── create_bar_chart()    # Generic chart generator
│   └── generate_markdown_report()
├── config_dataclasses.py     # Configuration structure
└── custom_types.py           # TypedDict definitions
```

## Advanced Usage

### Override Configuration at Runtime

Hydra allows overriding any config value from the command line:

```bash
# Change down payment
python mortgagecalculator_batch.py -cd settings -cn properties_list \
    loan_parameters.down_payment=150000

# Change interest rate
python mortgagecalculator_batch.py -cd settings -cn properties_list \
    loan_parameters.interest_rate=5.5

# Change output directory
python mortgagecalculator_batch.py -cd settings -cn properties_list \
    output_dir=my_analysis
```

### Use Different Config Directory

```bash
python mortgagecalculator_batch.py -cd example_settings -cn property_list
```

## Error Handling

The calculator validates all configuration values:

- Property value must be positive
- Interest rate must be 0-100%
- Down payment must be less than property value
- All costs and fees must be non-negative
- Monthly salary must be positive

Invalid configurations raise `ValidationError` with detailed messages.

## Dependencies

- **hydra-core** - Configuration management
- **omegaconf** - YAML/config parsing
- **pandas** - CSV generation
- **matplotlib** - Chart generation

## License

MIT License
