"""Type definitions for the mortgage calculator project."""

from typing import TypedDict


class ResultKeys:
    """Constants for MortgageResult dictionary keys."""
    DESCRIPTION = 'Description'
    ADDRESS = 'Address'
    LINK = 'Link'
    BEDROOMS = 'Bedrooms'
    BATHROOMS = 'Bathrooms'
    AREA = 'Area'
    YEAR_BUILT = 'Year_Built'
    PROPERTY_VALUE = 'Property_Value'
    DOWN_PAYMENT = 'Down_Payment'
    PRINCIPAL = 'Principal'
    INTEREST_RATE = 'Interest_Rate'
    YEARS_OF_LOAN = 'Years_of_Loan'
    MONTHLY_MORTGAGE_PAYMENT = 'Monthly_Mortgage_Payment'
    CONDO_FEES = 'Condo_Fees'
    TOTAL_MONTHLY_COSTS = 'Total_Monthly_Costs'
    PERCENTAGE_OF_SALARY = 'Percentage_of_Salary'
    LAND_TRANSFER_TAX_RATE = 'Land_Transfer_Tax_Rate'
    LAND_TRANSFER_TAX = 'Land_Transfer_Tax'
    NOTARY_COST = 'Notary_Cost'
    INSPECTION_COST = 'Inspection_Cost'
    TOTAL_ONE_TIME_COSTS = 'Total_One_Time_Costs'
    PROPERTY_TAX_RATE = 'Property_Tax_Rate'
    YEARLY_PROPERTY_TAX = 'Yearly_Property_Tax'
    SCHOOL_TAX_RATE = 'School_Tax_Rate'
    YEARLY_SCHOOL_TAX = 'Yearly_School_Tax'
    HOME_INSURANCE = 'Home_Insurance'
    TOTAL_YEARLY_COSTS = 'Total_Yearly_Costs'


class MortgageResult(TypedDict):
    """TypedDict representing the result of a mortgage calculation for a property.
    
    This is a flattened representation of all mortgage calculation data,
    suitable for CSV export and report generation.
    """
    Description: str
    Address: str
    Link: str
    Bedrooms: str | int
    Bathrooms: str | int
    Area: str | int
    Year_Built: str | int
    Property_Value: float
    Down_Payment: float
    Principal: float
    Interest_Rate: float
    Years_of_Loan: int
    Monthly_Mortgage_Payment: float
    Condo_Fees: float
    Total_Monthly_Costs: float
    Percentage_of_Salary: float
    Land_Transfer_Tax_Rate: float
    Land_Transfer_Tax: float
    Notary_Cost: float
    Inspection_Cost: float
    Total_One_Time_Costs: float
    Property_Tax_Rate: float
    Yearly_Property_Tax: float
    School_Tax_Rate: float
    Yearly_School_Tax: float
    Home_Insurance: float
    Total_Yearly_Costs: float
