from pathlib import Path
from config_dataclasses import PropertiesListConfig, PropertyConfig
from custom_types import MortgageResult

MONTHS_IN_YEAR = 12


class ValidationError(Exception):
    """Raised when configuration validation fails."""
    pass


def validate_property_config(property_cfg: PropertyConfig, loan_cfg: PropertiesListConfig) -> None:
    """
    Validate property and loan configuration values.
    
    Args:
        property_cfg: Property configuration to validate
        loan_cfg: Loan configuration to validate
        
    Raises:
        ValidationError: If any configuration value is invalid
    """
    errors = []
    
    # Property value validation
    if property_cfg.value <= 0:
        errors.append(f"Property value must be positive, got {property_cfg.value}")
    
    # Tax rate validation (should be percentages, typically 0-10%)
    if property_cfg.property_tax < 0:
        errors.append(f"Property tax rate cannot be negative, got {property_cfg.property_tax}")
    if property_cfg.school_tax < 0:
        errors.append(f"School tax rate cannot be negative, got {property_cfg.school_tax}")
    
    # Fee and cost validation
    if property_cfg.condo_fees < 0:
        errors.append(f"Condo fees cannot be negative, got {property_cfg.condo_fees}")
    if property_cfg.home_insurance < 0:
        errors.append(f"Home insurance cannot be negative, got {property_cfg.home_insurance}")
    
    # Loan parameter validation
    if loan_cfg.loan_parameters.interest_rate < 0 or loan_cfg.loan_parameters.interest_rate > 100:
        errors.append(f"Interest rate must be between 0 and 100%, got {loan_cfg.loan_parameters.interest_rate}")
    if loan_cfg.loan_parameters.years_of_loan <= 0:
        errors.append(f"Loan term must be positive, got {loan_cfg.loan_parameters.years_of_loan}")
    if loan_cfg.loan_parameters.down_payment < 0:
        errors.append(f"Down payment cannot be negative, got {loan_cfg.loan_parameters.down_payment}")
    if loan_cfg.loan_parameters.down_payment >= property_cfg.value:
        errors.append(f"Down payment ({loan_cfg.loan_parameters.down_payment}) cannot be >= property value ({property_cfg.value})")
    if loan_cfg.loan_parameters.monthly_salary <= 0:
        errors.append(f"Monthly salary must be positive, got {loan_cfg.loan_parameters.monthly_salary}")
    
    # Expense validation
    if loan_cfg.necessary_expenses.notary_cost < 0:
        errors.append(f"Notary cost cannot be negative, got {loan_cfg.necessary_expenses.notary_cost}")
    if loan_cfg.necessary_expenses.inspection_cost < 0:
        errors.append(f"Inspection cost cannot be negative, got {loan_cfg.necessary_expenses.inspection_cost}")
    
    if errors:
        raise ValidationError("Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors))


def percent_to_decimal(percentage: float) -> float:
    """Convert a percentage value to decimal (e.g., 5.0 -> 0.05)."""
    return percentage / 100


def land_transfer_tax_rate_decimal(value: float) -> float:
    """
    Calculate land transfer tax rate based on property value.
    
    Based on values found on https://www.nesto.ca/calculators/land-transfer-tax/quebec/
    
    Args:
        value: Property value in dollars
        
    Returns:
        Tax rate as decimal (e.g., 0.015 for 1.5%)
    """
    if value > 276200:
        return 0.015
    elif value > 5520:
        return 0.01
    else:
        return 0.005


def calculate_land_transfer_tax(value: float) -> float:
    """Calculate the land transfer tax amount for a property."""
    return value * land_transfer_tax_rate_decimal(value)


def calculate_monthly_interest_rate(yearly_rate_decimal: float) -> float:
    """Convert yearly interest rate (decimal) to monthly interest rate (decimal)."""
    return yearly_rate_decimal / MONTHS_IN_YEAR


def calculate_mortgage_payment(yearly_rate_decimal: float, years: int, principal: float) -> float:
    """
    Calculate monthly mortgage payment.
    
    Based on the formula found on https://en.wikipedia.org/wiki/Mortgage_calculator
    
    Args:
        yearly_rate_decimal: Yearly interest rate as decimal (e.g., 0.05 for 5%)
        years: Number of years of mortgage
        principal: Principal amount of mortgage
        
    Returns:
        Monthly mortgage payment amount
    """
    monthly_rate = calculate_monthly_interest_rate(yearly_rate_decimal)
    months = years * MONTHS_IN_YEAR
    return (principal * monthly_rate * pow(1 + monthly_rate, months)) / (pow(1 + monthly_rate, months) - 1)


def calculate_yearly_tax(value: float, rate_decimal: float) -> float:
    """Calculate yearly tax based on property value and tax rate (as decimal)."""
    return value * rate_decimal


def calculate_max_principal(yearly_rate_decimal: float, years: int, monthly_housing: float) -> float:
    """
    Calculate maximum principal based on monthly housing budget.
    
    Based on the formula found on https://en.wikipedia.org/wiki/Mortgage_calculator
    
    Args:
        yearly_rate_decimal: Yearly interest rate as decimal (e.g., 0.05 for 5%)
        years: Number of years of mortgage
        monthly_housing: Monthly amount available for housing costs
        
    Returns:
        Maximum principal that can be afforded
    """
    monthly_rate = calculate_monthly_interest_rate(yearly_rate_decimal)
    months = years * MONTHS_IN_YEAR
    return (monthly_housing * (pow(1 + monthly_rate, months) - 1)) / (monthly_rate * pow(1 + monthly_rate, months))


class CalculatedMortgage:
    def __init__(self, property_details: PropertyConfig, cfg: PropertiesListConfig):
        self.cfg = cfg
        self.property_details = property_details
        
        # Convert percentages to decimals at the boundary
        interest_rate_decimal = percent_to_decimal(cfg.loan_parameters.interest_rate)
        property_tax_decimal = percent_to_decimal(property_details.property_tax)
        school_tax_decimal = percent_to_decimal(property_details.school_tax)
        
        #Calculate all mortgage related values
        self.land_transfer_tax_rate = round(land_transfer_tax_rate_decimal(property_details.value), 4)
        self.land_transfer_tax = round(calculate_land_transfer_tax(property_details.value), 2)
        one_time_costs = [cfg.necessary_expenses.notary_cost, cfg.necessary_expenses.inspection_cost, self.land_transfer_tax]
        self.all_one_time_costs = round(sum(one_time_costs), 2)
        self.yearly_property_tax = round(calculate_yearly_tax(property_details.value, property_tax_decimal), 2)
        self.yearly_school_tax = round(calculate_yearly_tax(property_details.value, school_tax_decimal), 2)
        yearly_costs = [self.yearly_property_tax, self.yearly_school_tax, property_details.home_insurance]
        self.total_yearly_costs = round(sum(yearly_costs), 2)
        self.principal = round(property_details.value - cfg.loan_parameters.down_payment, 2)
        self.mortgage_payment = round(calculate_mortgage_payment(interest_rate_decimal, cfg.loan_parameters.years_of_loan, self.principal), 2)
        monthly_costs = [self.mortgage_payment, property_details.condo_fees]
        self.total_monthly_costs = round(sum(monthly_costs), 2)
        self.percentage_of_salary = round(self.total_monthly_costs / cfg.loan_parameters.monthly_salary, 2)

    def to_result(self) -> MortgageResult:
        """Convert the calculated mortgage to a MortgageResult for reporting.
        
        Returns:
            A flattened MortgageResult dictionary suitable for CSV export and reports.
        """
        return MortgageResult(
            Description=self.property_details.description or "",
            Address=self.property_details.address or "",
            Link=self.property_details.link or "",
            Bedrooms=self.property_details.bedrooms or "",
            Bathrooms=self.property_details.bathrooms or "",
            Area=self.property_details.area_sqft or "",
            Year_Built=self.property_details.year_built or "",
            Property_Value=self.property_details.value,
            Down_Payment=self.cfg.loan_parameters.down_payment,
            Principal=self.principal,
            Interest_Rate=self.cfg.loan_parameters.interest_rate,
            Years_of_Loan=self.cfg.loan_parameters.years_of_loan,
            Monthly_Mortgage_Payment=self.mortgage_payment,
            Condo_Fees=self.property_details.condo_fees,
            Total_Monthly_Costs=self.total_monthly_costs,
            Percentage_of_Salary=self.percentage_of_salary * 100,
            Land_Transfer_Tax_Rate=self.land_transfer_tax_rate * 100,
            Land_Transfer_Tax=self.land_transfer_tax,
            Notary_Cost=self.cfg.necessary_expenses.notary_cost,
            Inspection_Cost=self.cfg.necessary_expenses.inspection_cost,
            Total_One_Time_Costs=self.all_one_time_costs,
            Property_Tax_Rate=self.property_details.property_tax,
            Yearly_Property_Tax=self.yearly_property_tax,
            School_Tax_Rate=self.property_details.school_tax,
            Yearly_School_Tax=self.yearly_school_tax,
            Home_Insurance=self.property_details.home_insurance,
            Total_Yearly_Costs=self.total_yearly_costs,
        )

def calculate_mortgage_from_settings(config: PropertyConfig, cfg: PropertiesListConfig) -> CalculatedMortgage:
    """Calculate mortgage details from property and loan settings.
    
    Args:
        config: Property configuration
        cfg: Overall calculation configuration including loan parameters
        
    Returns:
        CalculatedMortgage object with all computed values
        
    Raises:
        ValidationError: If configuration values are invalid
    """
    validate_property_config(config, cfg)
    return CalculatedMortgage(config, cfg)


def calculate_max_mortgage_from_settings(config: PropertyConfig, cfg: PropertiesListConfig) -> CalculatedMortgage:
    """Calculate maximum mortgage from property and loan settings.
    
    Args:
        config: Property configuration
        cfg: Overall calculation configuration including loan parameters
        
    Returns:
        CalculatedMortgage object with all computed values
        
    Raises:
        ValidationError: If configuration values are invalid
    """
    validate_property_config(config, cfg)
    return CalculatedMortgage(config, cfg)