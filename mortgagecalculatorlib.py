from config_dataclasses import LandTransferTaxBracket, PropertiesListConfig, PropertyConfig
from custom_types import MortgageResult

MONTHS_IN_YEAR = 12

class ValidationError(Exception):
    """Raised when configuration validation fails."""
    pass


def validate_loan_config_and_properties(loan_cfg: PropertiesListConfig) -> None:
    """
    Validate loan and expense configuration values (call once before processing properties).
    
    Args:
        loan_cfg: Loan configuration to validate
        
    Raises:
        ValidationError: If any configuration value is invalid
    """
    errors = []
    
    # Loan parameter validation
    if loan_cfg.loan_parameters.interest_rate < 0 or loan_cfg.loan_parameters.interest_rate > 100:
        errors.append(f"Interest rate must be between 0 and 100%, got {loan_cfg.loan_parameters.interest_rate}")
    if loan_cfg.loan_parameters.years_of_loan <= 0:
        errors.append(f"Loan term must be positive, got {loan_cfg.loan_parameters.years_of_loan}")
    if loan_cfg.loan_parameters.down_payment < 0:
        errors.append(f"Down payment cannot be negative, got {loan_cfg.loan_parameters.down_payment}")
    if loan_cfg.loan_parameters.monthly_salary <= 0:
        errors.append(f"Monthly salary must be positive, got {loan_cfg.loan_parameters.monthly_salary}")
    if loan_cfg.loan_parameters.monthly_debt_payment < 0:
        errors.append(
            "Monthly debt payment cannot be negative, got "
            f"{loan_cfg.loan_parameters.monthly_debt_payment}"
        )
    
    # Expense validation
    if loan_cfg.necessary_expenses.notary_cost < 0:
        errors.append(f"Notary cost cannot be negative, got {loan_cfg.necessary_expenses.notary_cost}")
    if loan_cfg.necessary_expenses.inspection_cost < 0:
        errors.append(f"Inspection cost cannot be negative, got {loan_cfg.necessary_expenses.inspection_cost}")

    for property in loan_cfg.properties:
        errors.extend(get_property_config_errors(property, loan_cfg))
    
    if errors:
        raise ValidationError("Loan configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors))


def get_property_config_errors(property_cfg: PropertyConfig, loan_cfg: PropertiesListConfig) -> list[str]:
    """
    Validate property-specific configuration values.
    
    Args:
        property_cfg: Property configuration to validate
        loan_cfg: Loan configuration (used for cross-field checks like down payment vs value)
        
    Returns:
        List of validation error messages, empty if no errors
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
    if property_cfg.yearly_home_insurance < 0:
        errors.append(f"Home insurance cannot be negative, got {property_cfg.yearly_home_insurance}")
    

    if property_cfg.area_sqft <= 0:
        errors.append(f"Area (sqft) must be positive, got {property_cfg.area_sqft}")

    # Land transfer tax bracket validation
    if not property_cfg.land_transfer_tax_brackets:
        errors.append("Land transfer tax brackets must be configured (land_transfer_tax_brackets is empty)")
    else:
        for i, bracket in enumerate(property_cfg.land_transfer_tax_brackets):
            if bracket.rate < 0:
                errors.append(f"Land transfer tax bracket {i} rate cannot be negative, got {bracket.rate}")
            if bracket.threshold < 0:
                errors.append(f"Land transfer tax bracket {i} threshold cannot be negative, got {bracket.threshold}")
            # Ensure brackets are ordered from highest threshold to lowest
            if i > 0:
                prev_bracket = property_cfg.land_transfer_tax_brackets[i - 1]
                if prev_bracket.threshold <= bracket.threshold:
                    errors.append(
                        "Land transfer tax brackets must be ordered from highest threshold to lowest; "
                        f"bracket {i-1} threshold ({prev_bracket.threshold}) must be greater than "
                        f"bracket {i} threshold ({bracket.threshold})"
                    )

    # Cross-field validation
    if loan_cfg.loan_parameters.down_payment >= property_cfg.value:
        errors.append(f"Down payment ({loan_cfg.loan_parameters.down_payment}) cannot be >= property value ({property_cfg.value})")
    
    return errors


def percent_to_decimal(percentage: float) -> float:
    """Convert a percentage value to decimal (e.g., 5.0 -> 0.05)."""
    return percentage / 100


def land_transfer_tax_rate_decimal(value: float, brackets: list[LandTransferTaxBracket]) -> float:
    """
    Calculate land transfer tax rate based on property value and configured brackets.
    
    Brackets should be ordered from highest threshold to lowest.
    
    Args:
        value: Property value in dollars
        brackets: List of tax brackets (threshold/rate pairs, rate as percentage)
        
    Returns:
        Tax rate as decimal (e.g., 0.015 for 1.5%)
        
    Raises:
        ValueError: If no brackets are configured
    """
    if not brackets:
        raise ValueError("No land transfer tax brackets configured")
    
    for bracket in brackets:
        if value > bracket.threshold:
            return percent_to_decimal(bracket.rate)
    
    # Fall through to the last bracket's rate
    return percent_to_decimal(brackets[-1].rate)


def calculate_land_transfer_tax(value: float, brackets: list[LandTransferTaxBracket]) -> float:
    """Calculate the land transfer tax amount for a property."""
    return value * land_transfer_tax_rate_decimal(value, brackets)


def calculate_monthly_interest_rate(yearly_rate_decimal: float) -> float:
    """Convert yearly interest rate (decimal) to monthly interest rate (decimal)."""
    return yearly_rate_decimal / MONTHS_IN_YEAR


def calculate_mortgage_payment(yearly_rate_decimal: float, years: int, loan_amount: float) -> float:
    """
    Calculate monthly mortgage payment.
    
    Based on the formula found on https://en.wikipedia.org/wiki/Mortgage_calculator
    
    Args:
        yearly_rate_decimal: Yearly interest rate as decimal (e.g., 0.05 for 5%)
        years: Number of years of mortgage
        loan_amount: Loan amount of mortgage
        
    Returns:
        Monthly mortgage payment amount
    """

    #Edge case for 0% interest
    if yearly_rate_decimal == 0:
        return loan_amount / (years * MONTHS_IN_YEAR)
    
    monthly_rate = calculate_monthly_interest_rate(yearly_rate_decimal)
    months = years * MONTHS_IN_YEAR
    return (loan_amount * monthly_rate * pow(1 + monthly_rate, months)) / (pow(1 + monthly_rate, months) - 1)


def calculate_yearly_tax(value: float, rate_decimal: float) -> float:
    """Calculate yearly tax based on property value and tax rate (as decimal)."""
    return value * rate_decimal

class CalculatedMortgage:
    def __init__(self, property_details: PropertyConfig, cfg: PropertiesListConfig):
        # Convert percentages to decimals at the boundary
        interest_rate_decimal = percent_to_decimal(cfg.loan_parameters.interest_rate)
        property_tax_decimal = percent_to_decimal(property_details.property_tax)
        school_tax_decimal = percent_to_decimal(property_details.school_tax)

        area_sqft = float(property_details.area_sqft or 0)
        
        # Calculate all mortgage related values
        brackets = property_details.land_transfer_tax_brackets
        self.land_transfer_tax_rate = round(land_transfer_tax_rate_decimal(property_details.value, brackets), 7)
        self.land_transfer_tax = round(calculate_land_transfer_tax(property_details.value, brackets), 2)
        one_time_costs = [cfg.necessary_expenses.notary_cost, cfg.necessary_expenses.inspection_cost, self.land_transfer_tax]
        self.all_one_time_costs = round(sum(one_time_costs), 2)
        self.cash_to_close = round(cfg.loan_parameters.down_payment + self.all_one_time_costs, 2)
        self.yearly_property_tax = round(calculate_yearly_tax(property_details.value, property_tax_decimal), 2)
        self.monthly_property_tax = round(self.yearly_property_tax / MONTHS_IN_YEAR, 2)
        self.yearly_school_tax = round(calculate_yearly_tax(property_details.value, school_tax_decimal), 2)
        self.monthly_school_tax = round(self.yearly_school_tax / MONTHS_IN_YEAR, 2)
        yearly_home_insurance = round(property_details.yearly_home_insurance, 2)
        self.monthly_home_insurance = round(yearly_home_insurance / MONTHS_IN_YEAR, 2)
        yearly_costs = [self.yearly_property_tax, self.yearly_school_tax, yearly_home_insurance]
        self.total_yearly_costs = round(sum(yearly_costs), 2)
        self.loan_amount = round(property_details.value - cfg.loan_parameters.down_payment, 2)
        self.mortgage_payment = round(calculate_mortgage_payment(interest_rate_decimal, cfg.loan_parameters.years_of_loan, self.loan_amount), 2)
        monthly_interest_rate = calculate_monthly_interest_rate(interest_rate_decimal)
        self.monthly_interest = round(self.loan_amount * monthly_interest_rate, 2)
        self.yearly_interest = round(self.monthly_interest * MONTHS_IN_YEAR, 2)
        total_payments = self.mortgage_payment * (cfg.loan_parameters.years_of_loan * MONTHS_IN_YEAR)
        self.total_interest = round(total_payments - self.loan_amount, 2)
        self.price_per_sqft = round(property_details.value / area_sqft, 2) if area_sqft > 0 else 0.0
        monthly_costs = [
            self.mortgage_payment,
            property_details.condo_fees,
            self.monthly_property_tax,
            self.monthly_school_tax,
            self.monthly_home_insurance,
        ]
        self.total_monthly_costs = round(sum(monthly_costs), 2)
        affordability_monthly_costs = self.total_monthly_costs + cfg.loan_parameters.monthly_debt_payment
        self.gds_ratio = round(self.total_monthly_costs / cfg.loan_parameters.monthly_salary * 100, 2) if cfg.loan_parameters.monthly_salary > 0 else 0.0
        self.tds_ratio = round(affordability_monthly_costs / cfg.loan_parameters.monthly_salary * 100, 2) if cfg.loan_parameters.monthly_salary > 0 else 0.0

    def to_result(self, property_details: PropertyConfig, cfg: PropertiesListConfig) -> MortgageResult:
        """Convert the calculated mortgage to a MortgageResult for reporting.
        
        Args:
            property_details: Property configuration used for this mortgage.
            cfg: Overall calculation configuration including loan parameters.

        Returns:
            A flattened MortgageResult dictionary suitable for CSV export and reports.
        """
        return MortgageResult(
            Description=property_details.description or "",
            Address=property_details.address or "",
            Link=property_details.link or "",
            Bedrooms=property_details.bedrooms or "",
            Bathrooms=property_details.bathrooms or "",
            Area=property_details.area_sqft or "",
            Year_Built=property_details.year_built or "",
            Property_Value=property_details.value,
            Down_Payment=cfg.loan_parameters.down_payment,
            Loan_Amount=self.loan_amount,
            Interest_Rate=cfg.loan_parameters.interest_rate,
            Years_of_Loan=cfg.loan_parameters.years_of_loan,
            Monthly_Mortgage_Payment=self.mortgage_payment,
            Monthly_Interest=self.monthly_interest,
            Yearly_Interest=self.yearly_interest,
            Total_Interest=self.total_interest,
            Condo_Fees=property_details.condo_fees,
            Total_Monthly_Costs=self.total_monthly_costs,
            Land_Transfer_Tax_Rate=self.land_transfer_tax_rate * 100,
            Land_Transfer_Tax=self.land_transfer_tax,
            Notary_Cost=cfg.necessary_expenses.notary_cost,
            Inspection_Cost=cfg.necessary_expenses.inspection_cost,
            Total_One_Time_Costs=self.all_one_time_costs,
            Cash_to_Close=self.cash_to_close,
            Property_Tax_Rate=property_details.property_tax,
            Yearly_Property_Tax=self.yearly_property_tax,
            Monthly_Property_Tax=self.monthly_property_tax,
            School_Tax_Rate=property_details.school_tax,
            Yearly_School_Tax=self.yearly_school_tax,
            Monthly_School_Tax=self.monthly_school_tax,
            Yearly_Home_Insurance=property_details.yearly_home_insurance,
            Monthly_Home_Insurance=self.monthly_home_insurance,
            Total_Yearly_Costs=self.total_yearly_costs,
            Price_Per_Sqft=self.price_per_sqft,
            Monthly_Salary=cfg.loan_parameters.monthly_salary,
            Monthly_Debt_Payment=cfg.loan_parameters.monthly_debt_payment,
            GDS_Ratio=self.gds_ratio,
            TDS_Ratio=self.tds_ratio,
        )

def calculate_mortgage_from_settings(config: PropertyConfig, cfg: PropertiesListConfig) -> MortgageResult:
    """Calculate mortgage details from property and loan settings.
    
    Args:
        config: Property configuration
        cfg: Overall calculation configuration including loan parameters
        
    Returns:
        A flattened MortgageResult dictionary suitable for CSV export and reports.
    """
    calculated = CalculatedMortgage(config, cfg)
    return calculated.to_result(config, cfg)
