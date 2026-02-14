from dataclasses import dataclass
from typing import Optional, List


@dataclass
class PropertyConfig:
    """Configuration for mortgage and property calculations"""
    
    # Property details
    value: float
    condo_fees: float
    area_sqft: float
    bedrooms: int
    bathrooms: int
    year_built: int
    
    # Loan details
    interest_rate: float
    years_of_loan: int
    
    # Taxes (as percentages, up to 5 decimal places e.g. 0.08423 = 0.08423%)
    property_tax: float
    school_tax: float
    
    # Insurance and costs
    yearly_home_insurance: float
    notary_cost: float
    inspection_cost: float
    
    # Optional metadata
    description: Optional[str] = None
    address: Optional[str] = None
    link: Optional[str] = None

@dataclass
class ChartConfig:
    """Configuration for chart dimensions and rendering."""
    width: int = 6
    height: int = 4
    top_padding: float = 0.15
    dpi: int = 150

@dataclass
class LoanParametersConfig:
    """Configuration for loan parameters"""
    down_payment: float
    interest_rate: float
    years_of_loan: int
    monthly_salary: float
    monthly_debt_payment: float

@dataclass
class NecessaryExpensesConfig:
    """Configuration for necessary expenses"""
    notary_cost: float
    inspection_cost: float

@dataclass
class PropertiesListConfig:
    """Configuration for multiple properties"""
    properties: List[PropertyConfig]
    output_dir: str
    output_data: str
    output_report: str
    chart: ChartConfig
    loan_parameters: LoanParametersConfig
    necessary_expenses: NecessaryExpensesConfig
    