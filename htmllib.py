from pathlib import Path
import pandas as pd

from reportwriter import ReportWriter, register_class

@register_class("HTMLWriter")
class HTMLWriter(ReportWriter):
    @classmethod
    def print_header(cls, header: str, level: int = 1) -> str:
        return f"<h{level} id='header-{header.replace(" ", "")}'>{header}</h{level}>\n\n"

    @classmethod
    def print_paragraph(cls, text: str) -> str:
        return f"<p>{text}</p>\n\n"

    @classmethod
    def print_bold(cls, text: str) -> str:
        return f"<strong>{text}</strong>"

    @classmethod
    def print_table(cls, df: pd.DataFrame) -> str:
        """Convert a DataFrame to a HTML table string."""
        if df.empty:
            return "<p>No data available.</p>\n\n"
        
        # Header
        header = "<tr>" + "".join(f"<th>{col}</th>" for col in df.columns) + "</tr>\n"
        
        # Rows
        rows = ""
        for _, row in df.iterrows():
            rows += "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>\n"
        

        return "<table>\n" + header + rows + "</table>\n\n"

    @classmethod
    def print_list(cls, items: list[str], numbered: bool = False) -> str:
        tag = "ol" if numbered else "ul"
        return f"<{tag}>\n" + "".join(f"  <li>{item}</li>\n" for item in items) + f"</{tag}>\n\n"

    @classmethod
    def print_empty_line(cls) -> str:
        return "<br />\n\n"

    @classmethod
    def print_image(cls, image_path: Path, alt_text: str = "") -> str:
        return f"<img src='{image_path}' alt='{alt_text}' />\n\n"

    @classmethod
    def print_link(cls, text: str, url: str) -> str:
        return f"<a href='{url}'>{text}</a>"
    
    @classmethod
    def get_property_section_link(cls, property_id: int) -> str:
        return f"#header-Property{property_id}"

    @classmethod
    def get_extension(cls) -> str:
        return "html"
    
    @classmethod
    def initialize_report(cls, title: str) -> str:
        return f"<!DOCTYPE html>\n<html>\n<head>\n<title>{title}</title>\n</head>\n<body>\n\n{cls.print_header(title, level=1)}"
    
    @classmethod
    def finalize_report(cls) -> str:
        return "</body>\n</html>\n"
