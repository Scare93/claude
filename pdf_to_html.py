#!/usr/bin/env python3
"""
PDF to HTML Converter

This script converts PDF files to well-structured HTML documents.
It extracts text, images, and maintains document structure.
"""

import sys
import os
from pathlib import Path
from typing import Optional, Dict, List
import argparse
from datetime import datetime

try:
    import pdfplumber
    from bs4 import BeautifulSoup
    import base64
except ImportError as e:
    print(f"Error: Missing required package. Please install dependencies:")
    print(f"  pip install -r requirements.txt")
    sys.exit(1)


class PDFToHTMLConverter:
    """Convert PDF files to HTML with structure preservation."""

    def __init__(self, pdf_path: str, output_path: Optional[str] = None):
        """
        Initialize the converter.

        Args:
            pdf_path: Path to the PDF file
            output_path: Path for output HTML file (optional)
        """
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        if output_path:
            self.output_path = Path(output_path)
        else:
            self.output_path = self.pdf_path.with_suffix('.html')

        self.metadata: Dict = {}
        self.pages_content: List[Dict] = []

    def extract_metadata(self, pdf) -> Dict:
        """Extract PDF metadata."""
        metadata = pdf.metadata or {}
        return {
            'title': metadata.get('Title', self.pdf_path.stem),
            'author': metadata.get('Author', 'Unknown'),
            'subject': metadata.get('Subject', ''),
            'creator': metadata.get('Creator', ''),
            'producer': metadata.get('Producer', ''),
            'creation_date': metadata.get('CreationDate', ''),
            'total_pages': len(pdf.pages)
        }

    def extract_text_with_layout(self, page) -> str:
        """Extract text from a page while preserving layout."""
        text = page.extract_text(layout=True)
        return text if text else ""

    def extract_tables(self, page) -> List[List[List[str]]]:
        """Extract tables from a page."""
        try:
            tables = page.extract_tables()
            return tables if tables else []
        except:
            return []

    def extract_images(self, page, page_num: int) -> List[Dict]:
        """Extract images from a page."""
        images = []
        try:
            if hasattr(page, 'images'):
                for i, img in enumerate(page.images):
                    images.append({
                        'index': i,
                        'page': page_num,
                        'x0': img.get('x0', 0),
                        'y0': img.get('y0', 0),
                        'width': img.get('width', 0),
                        'height': img.get('height', 0)
                    })
        except:
            pass
        return images

    def table_to_html(self, table: List[List[str]]) -> str:
        """Convert a table to HTML."""
        if not table:
            return ""

        html = '<table class="pdf-table">\n'

        # First row as header
        if table:
            html += '  <thead>\n    <tr>\n'
            for cell in table[0]:
                cell_content = cell if cell else ''
                html += f'      <th>{self._escape_html(cell_content)}</th>\n'
            html += '    </tr>\n  </thead>\n'

        # Remaining rows as body
        if len(table) > 1:
            html += '  <tbody>\n'
            for row in table[1:]:
                html += '    <tr>\n'
                for cell in row:
                    cell_content = cell if cell else ''
                    html += f'      <td>{self._escape_html(cell_content)}</td>\n'
                html += '    </tr>\n'
            html += '  </tbody>\n'

        html += '</table>\n'
        return html

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (text.replace('&', '&amp;')
                   .replace('<', '&lt;')
                   .replace('>', '&gt;')
                   .replace('"', '&quot;')
                   .replace("'", '&#39;'))

    def process_pdf(self) -> None:
        """Process the PDF and extract all content."""
        print(f"Processing PDF: {self.pdf_path}")

        with pdfplumber.open(self.pdf_path) as pdf:
            # Extract metadata
            self.metadata = self.extract_metadata(pdf)
            print(f"Total pages: {self.metadata['total_pages']}")

            # Process each page
            for page_num, page in enumerate(pdf.pages, start=1):
                print(f"Processing page {page_num}/{self.metadata['total_pages']}")

                page_data = {
                    'page_number': page_num,
                    'text': self.extract_text_with_layout(page),
                    'tables': self.extract_tables(page),
                    'images': self.extract_images(page, page_num),
                    'width': page.width,
                    'height': page.height
                }

                self.pages_content.append(page_data)

    def generate_html(self) -> str:
        """Generate HTML from extracted content."""
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self._escape_html(self.metadata.get('title', 'PDF Document'))}</title>
    <style>
        * {{
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}

        .document-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}

        .document-header h1 {{
            margin: 0 0 10px 0;
            font-size: 2em;
        }}

        .metadata {{
            background: rgba(255,255,255,0.1);
            padding: 15px;
            border-radius: 5px;
            margin-top: 15px;
        }}

        .metadata-item {{
            display: inline-block;
            margin-right: 20px;
            margin-bottom: 5px;
        }}

        .page {{
            background: white;
            padding: 40px;
            margin-bottom: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            position: relative;
        }}

        .page-number {{
            position: absolute;
            top: 10px;
            right: 20px;
            background: #667eea;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
        }}

        .page-content {{
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            font-size: 0.95em;
            line-height: 1.5;
        }}

        .pdf-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}

        .pdf-table th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}

        .pdf-table td {{
            padding: 10px 12px;
            border-bottom: 1px solid #e0e0e0;
        }}

        .pdf-table tr:hover {{
            background: #f8f9fa;
        }}

        .table-container {{
            margin: 30px 0;
            overflow-x: auto;
        }}

        .image-placeholder {{
            background: #f0f0f0;
            border: 2px dashed #ccc;
            padding: 20px;
            text-align: center;
            margin: 20px 0;
            border-radius: 5px;
            color: #666;
        }}

        footer {{
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
        }}

        @media print {{
            body {{
                background: white;
            }}
            .page {{
                box-shadow: none;
                page-break-after: always;
            }}
        }}
    </style>
</head>
<body>
    <div class="document-header">
        <h1>{self._escape_html(self.metadata.get('title', 'PDF Document'))}</h1>
        <div class="metadata">
'''

        # Add metadata
        if self.metadata.get('author'):
            html += f'            <span class="metadata-item"><strong>Author:</strong> {self._escape_html(self.metadata["author"])}</span>\n'

        html += f'            <span class="metadata-item"><strong>Pages:</strong> {self.metadata["total_pages"]}</span>\n'

        if self.metadata.get('subject'):
            html += f'            <span class="metadata-item"><strong>Subject:</strong> {self._escape_html(self.metadata["subject"])}</span>\n'

        html += f'            <span class="metadata-item"><strong>Converted:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M")}</span>\n'

        html += '''        </div>
    </div>

'''

        # Add pages
        for page_data in self.pages_content:
            html += f'    <div class="page">\n'
            html += f'        <div class="page-number">Page {page_data["page_number"]}</div>\n'

            # Add text content
            if page_data['text']:
                html += f'        <div class="page-content">{self._escape_html(page_data["text"])}</div>\n'

            # Add tables
            for table in page_data['tables']:
                html += '        <div class="table-container">\n'
                html += self.table_to_html(table)
                html += '        </div>\n'

            # Add image placeholders
            for img in page_data['images']:
                html += f'        <div class="image-placeholder">\n'
                html += f'            📷 Image {img["index"] + 1} (Position: {img["x0"]:.0f}, {img["y0"]:.0f} | Size: {img["width"]:.0f}x{img["height"]:.0f})\n'
                html += '        </div>\n'

            html += '    </div>\n\n'

        # Add footer
        html += f'''    <footer>
        <p>Converted from <strong>{self._escape_html(self.pdf_path.name)}</strong></p>
        <p>PDF to HTML Converter | Generated on {datetime.now().strftime("%Y-%m-%d at %H:%M:%S")}</p>
    </footer>
</body>
</html>'''

        return html

    def convert(self) -> str:
        """
        Main conversion method.

        Returns:
            Path to the generated HTML file
        """
        self.process_pdf()
        html_content = self.generate_html()

        # Write HTML file
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"\n✓ Conversion completed successfully!")
        print(f"  Output: {self.output_path}")
        print(f"  Size: {self.output_path.stat().st_size / 1024:.2f} KB")

        return str(self.output_path)


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description='Convert PDF files to well-structured HTML documents',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s document.pdf
  %(prog)s document.pdf -o output.html
  %(prog)s report.pdf --output report.html
        '''
    )

    parser.add_argument('pdf_file', help='Path to the PDF file to convert')
    parser.add_argument('-o', '--output', help='Output HTML file path (optional)')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 1.0.0')

    args = parser.parse_args()

    try:
        converter = PDFToHTMLConverter(args.pdf_file, args.output)
        converter.convert()
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error during conversion: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
