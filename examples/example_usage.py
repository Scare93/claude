#!/usr/bin/env python3
"""
Example usage of the PDF to HTML Converter

This script demonstrates how to use the PDFToHTMLConverter class
in your own Python projects.
"""

import sys
from pathlib import Path

# Add parent directory to path to import the converter
sys.path.insert(0, str(Path(__file__).parent.parent))

from pdf_to_html import PDFToHTMLConverter


def example_basic_conversion():
    """Example 1: Basic conversion with automatic output filename."""
    print("Example 1: Basic Conversion")
    print("-" * 50)

    try:
        # Create converter - output filename will be auto-generated
        converter = PDFToHTMLConverter('sample.pdf')

        # Perform conversion
        output_path = converter.convert()

        print(f"Success! HTML file created at: {output_path}\n")

    except FileNotFoundError:
        print("Note: 'sample.pdf' not found. Place a PDF file here to test.\n")
    except Exception as e:
        print(f"Error: {e}\n")


def example_custom_output():
    """Example 2: Conversion with custom output path."""
    print("Example 2: Custom Output Path")
    print("-" * 50)

    try:
        # Specify custom output filename
        converter = PDFToHTMLConverter(
            pdf_path='document.pdf',
            output_path='custom_output.html'
        )

        output_path = converter.convert()

        print(f"Success! HTML file created at: {output_path}\n")

    except FileNotFoundError:
        print("Note: 'document.pdf' not found. Place a PDF file here to test.\n")
    except Exception as e:
        print(f"Error: {e}\n")


def example_batch_conversion():
    """Example 3: Batch convert all PDFs in a directory."""
    print("Example 3: Batch Conversion")
    print("-" * 50)

    # Get all PDF files in current directory
    pdf_files = list(Path('.').glob('*.pdf'))

    if not pdf_files:
        print("No PDF files found in current directory.\n")
        return

    print(f"Found {len(pdf_files)} PDF file(s)")

    for pdf_file in pdf_files:
        try:
            print(f"\nConverting: {pdf_file.name}")
            converter = PDFToHTMLConverter(str(pdf_file))
            output_path = converter.convert()
            print(f"  ✓ Saved to: {output_path}")

        except Exception as e:
            print(f"  ✗ Error: {e}")

    print()


def example_with_metadata():
    """Example 4: Access PDF metadata after processing."""
    print("Example 4: Accessing Metadata")
    print("-" * 50)

    try:
        converter = PDFToHTMLConverter('sample.pdf')

        # Process the PDF (doesn't write HTML yet)
        converter.process_pdf()

        # Access metadata
        print("PDF Metadata:")
        print(f"  Title: {converter.metadata.get('title')}")
        print(f"  Author: {converter.metadata.get('author')}")
        print(f"  Total Pages: {converter.metadata.get('total_pages')}")
        print(f"  Subject: {converter.metadata.get('subject')}")

        # Now generate and save HTML
        html_content = converter.generate_html()

        with open(converter.output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"\nHTML saved to: {converter.output_path}\n")

    except FileNotFoundError:
        print("Note: 'sample.pdf' not found. Place a PDF file here to test.\n")
    except Exception as e:
        print(f"Error: {e}\n")


def main():
    """Run all examples."""
    print("\n" + "=" * 50)
    print("PDF to HTML Converter - Usage Examples")
    print("=" * 50 + "\n")

    # Run examples
    example_basic_conversion()
    example_custom_output()
    example_batch_conversion()
    example_with_metadata()

    print("=" * 50)
    print("Examples completed!")
    print("=" * 50 + "\n")


if __name__ == '__main__':
    main()
