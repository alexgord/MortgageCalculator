import hydra
import pandas as pd
import logging
from pathlib import Path
from hydra.core.config_store import ConfigStore
from omegaconf import OmegaConf
from config_dataclasses import PropertiesListConfig
from mortgagecalculatorlib import calculate_mortgage_from_settings, ValidationError
from reportinglib import generate_markdown_report, ReportGenerationError
from custom_types import MortgageResult

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
    
    print(f"Processing {len(cfg.properties)} properties...")
    
    # Calculate mortgages for all properties
    results: list[MortgageResult] = []
    for i, prop in enumerate(cfg.properties, 1):
        try:
            calculated = calculate_mortgage_from_settings(prop, cfg)
            results.append(calculated.to_result())
        except ValidationError as e:
            logger.error(f"Property {i} validation failed: {e}")
            raise
    
    # Create DataFrame and write to CSV
    df = pd.DataFrame(results)
    try:
        df.to_csv(output_data_file, index=False, encoding='utf-8')
    except OSError as e:
        logger.error(f"Failed to write CSV to {output_data_file}: {e}")
        raise
    
    try:
        generate_markdown_report(output_report_file, results, cfg)
    except (ReportGenerationError, ValueError) as e:
        logger.error(f"Report generation failed: {e}")
        raise
    
    print(f"\n✓ Results written to: {output_data_file.absolute()}")
    print(f"✓ Report written to: {output_report_file.absolute()}")
    print(f"  Total properties processed: {len(results)}")

if __name__ == "__main__":
    batch_calculate()
