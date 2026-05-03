from pathlib import Path
import pandas as pd

from reportwriter import ReportWriter, register_class

@register_class("MarkdownWriter")
class MarkdownWriter(ReportWriter):
    @classmethod
    def print_header(cls, header: str, level: int = 1) -> str:
        return f"{'#' * level} {header}\n\n"

    @classmethod
    def print_paragraph(cls, text: str) -> str:
        return f"{text}\n\n"

    @classmethod
    def print_bold(cls, text: str) -> str:
        return f"**{text}**"

    @classmethod
    def print_table(cls, df: pd.DataFrame) -> str:
        """Convert a DataFrame to a Markdown table string."""
        if df.empty:
            return "No data available.\n\n"
        
        # Header
        header = "| " + " | ".join(df.columns) + " |\n"
        separator = "| " + " | ".join(['---'] * len(df.columns)) + " |\n"
        
        # Rows
        rows = ""
        for _, row in df.iterrows():
            rows += "| " + " | ".join(str(cell) for cell in row) + " |\n"
        
        return header + separator + rows + "\n"

    @classmethod
    def print_list(cls, items: list[str], numbered: bool = False) -> str:

        def get_prefix(i: int) -> str:
            return f"{i+1}." if numbered else "-"
        return "\n".join(f"{get_prefix(i)} {item}" for i, item in enumerate(items)) + "\n\n"

    @classmethod
    def print_empty_line(cls) -> str:
        return "\n"

    @classmethod
    def print_image(cls, image_path: Path, alt_text: str = "") -> str:
        return f"![{alt_text}]({image_path})\n\n"

    @classmethod
    def print_link(cls, text: str, url: str) -> str:
        return f"[{text}]({url})"
    
    @classmethod
    def get_property_section_link(cls, property_id: int) -> str:
        return f"#property-{property_id}"

    @classmethod
    def get_extension(cls) -> str:
        return "md"
    
    @classmethod
    def initialize_report(cls, title: str) -> str:
        return cls.print_header(title, level=1)
    
    @classmethod
    def finalize_report(cls) -> str:
        return ""
    