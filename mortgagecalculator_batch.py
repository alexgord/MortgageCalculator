import hydra
import pandas as pd
import logging
from pathlib import Path
from hydra.core.config_store import ConfigStore
from omegaconf import OmegaConf
from config_dataclasses import PropertiesListConfig
from mortgagecalculatorlib import CalculatedAffordability, calculate_mortgage_from_settings, validate_loan_config_and_properties, ValidationError
from reporting import ReportGenerationError, generate_report
from custom_types import MortgageResult
from reportwriter import get_class_by_value
from markdownlib import MarkdownWriter
from htmllib import HTMLWriter
from chart_service import ChartService

logger = logging.getLogger(__name__)

# Register the structured config
cs = ConfigStore.instance()
cs.store(name="properties_config", node=PropertiesListConfig)

@hydra.main(version_base=None, config_path="settings", config_name="properties_list")
def batch_calculate(cfg: PropertiesListConfig) -> None:
    OmegaConf.resolve(cfg)
    
    # Define CSV output path
    output_data_file = Path(cfg.output_dir) / cfg.output_data
    output_data_file.parent.mkdir(parents=True, exist_ok=True)

    # Define Markdown report output path
    output_report_file= Path(cfg.output_dir) / cfg.output_report
    output_report_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Validate loan configuration once before processing properties
    validate_loan_config_and_properties(cfg)
    
    print(f"Processing {len(cfg.properties)} properties...")
    
    # Calculate theoretical ceiling for the largest mortgage you could get based on the loan parameters and standard banking guidelines
    affordability = CalculatedAffordability(cfg)

    # Calculate mortgages for all properties
    results: list[MortgageResult] = []
    for i, (_, prop) in enumerate(cfg.properties.items(), 1):
        result = calculate_mortgage_from_settings(prop, cfg)
        results.append(result)
    
    # Create DataFrame and write to CSV
    df = pd.DataFrame(results)
    try:
        df.to_csv(output_data_file, index=False, encoding='utf-8')
    except OSError as e:
        logger.error(f"Failed to write CSV to {output_data_file}: {e}")
        raise
    
    if cfg.report_types is None or len(cfg.report_types) == 0:
        logger.error("No report types specified in configuration.")
        raise ValueError("At least one report type must be specified in the configuration.")

    print("Generating cost comparison charts...")
    ChartService.generate_cost_comparison_charts(results, output_report_file.parent, cfg)

    print("Generating property report charts...")
    for (i,mortgage_result) in enumerate(results, 1):
        print(f"Generating property report charts for property {i}...")
        ChartService.generate_property_report_chart(i, mortgage_result, output_report_file.parent, cfg)

    for report_type in cfg.report_types:
        print(f"Generating report of type: {report_type}...")
        try:
            generate_report(report_type, output_report_file, affordability, results, cfg)
        except (ReportGenerationError, ValueError) as e:
            logger.error(f"Report generation failed: {e}")
            raise
    
    print(f"\n✓ Results written to: {output_data_file.absolute()}")
    print(f"✓ Report written to: {output_report_file.absolute()}")
    print(f"  Total properties processed: {len(results)}")

if __name__ == "__main__":
    batch_calculate()
