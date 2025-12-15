# PDF to HTML Converter

A powerful Python tool to convert PDF files into well-structured, beautifully formatted HTML documents. This converter preserves document structure, extracts tables, and maintains layout while creating responsive HTML output.

## Features

- **Text Extraction**: Extracts text while preserving layout and formatting
- **Table Detection**: Automatically detects and converts tables to HTML tables
- **Image Detection**: Identifies images and their positions in the document
- **Metadata Preservation**: Extracts and displays PDF metadata (title, author, etc.)
- **Beautiful Styling**: Generates modern, responsive HTML with built-in CSS
- **Easy to Use**: Simple command-line interface
- **Customizable Output**: Specify custom output file names

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Install Dependencies

```bash
pip install -r requirements.txt
```

Or install packages individually:

```bash
pip install pdfplumber beautifulsoup4 Pillow pdfminer.six
```

## Usage

### Basic Usage

Convert a PDF file to HTML (output will be saved with the same name but .html extension):

```bash
python pdf_to_html.py document.pdf
```

### Specify Output File

Convert and specify a custom output filename:

```bash
python pdf_to_html.py document.pdf -o output.html
```

or

```bash
python pdf_to_html.py document.pdf --output my_document.html
```

### Make Script Executable (Linux/Mac)

```bash
chmod +x pdf_to_html.py
./pdf_to_html.py document.pdf
```

## Command Line Options

```
usage: pdf_to_html.py [-h] [-o OUTPUT] [-v] pdf_file

positional arguments:
  pdf_file              Path to the PDF file to convert

optional arguments:
  -h, --help            Show help message and exit
  -o OUTPUT, --output OUTPUT
                        Output HTML file path (optional)
  -v, --version         Show program's version number and exit
```

## Examples

### Example 1: Convert a Simple Document

```bash
python pdf_to_html.py report.pdf
```

Output: `report.html`

### Example 2: Convert with Custom Output

```bash
python pdf_to_html.py /path/to/scientific_paper.pdf -o /path/to/output/paper.html
```

### Example 3: Batch Conversion (Bash)

```bash
for pdf in *.pdf; do
    python pdf_to_html.py "$pdf"
done
```

### Example 4: Using as a Module

```python
from pdf_to_html import PDFToHTMLConverter

# Create converter instance
converter = PDFToHTMLConverter('document.pdf', 'output.html')

# Convert PDF to HTML
output_path = converter.convert()
print(f"HTML saved to: {output_path}")
```

## Output Features

The generated HTML includes:

- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Modern Styling**: Beautiful gradient headers and clean typography
- **Document Metadata**: Title, author, page count, conversion date
- **Page Numbers**: Each page clearly numbered
- **Table Formatting**: Tables converted with proper headers and styling
- **Image Placeholders**: Indicators for image positions and sizes
- **Print-Friendly**: Optimized CSS for printing

## How It Works

1. **PDF Processing**: Uses `pdfplumber` to open and parse PDF files
2. **Metadata Extraction**: Retrieves document information (title, author, etc.)
3. **Content Extraction**: Extracts text with layout preservation
4. **Table Detection**: Identifies and extracts tabular data
5. **Image Detection**: Locates images and their dimensions
6. **HTML Generation**: Creates structured HTML with embedded CSS
7. **File Output**: Writes the formatted HTML to disk

## Technical Details

### Libraries Used

- **pdfplumber**: Advanced PDF parsing and text extraction
- **beautifulsoup4**: HTML generation and manipulation
- **Pillow**: Image processing support
- **pdfminer.six**: Low-level PDF parsing (dependency)

### Supported PDF Features

✅ Text content
✅ Tables
✅ Image detection and positioning
✅ Multi-page documents
✅ Document metadata
✅ Layout preservation

⚠️ Note: Actual image embedding is shown as placeholders (positions and sizes). For full image embedding, additional implementation is required.

## Limitations

- **Images**: Currently shows placeholders with position/size info. Image extraction requires additional implementation.
- **Complex Layouts**: Very complex multi-column layouts may not convert perfectly.
- **Forms**: PDF forms and interactive elements are not converted.
- **Fonts**: Font information is not preserved (uses standard web fonts).
- **Colors**: Text and background colors from the original PDF are not preserved.

## Troubleshooting

### ImportError: No module named 'pdfplumber'

Install the required dependencies:

```bash
pip install -r requirements.txt
```

### FileNotFoundError

Make sure the PDF file path is correct and the file exists.

### Permission Denied

Ensure you have read permissions for the input PDF and write permissions for the output directory.

### Memory Issues with Large PDFs

For very large PDF files (100+ pages), the conversion might be slow or memory-intensive. Consider processing page ranges separately if needed.

## Development

### Project Structure

```
.
├── pdf_to_html.py      # Main converter script
├── requirements.txt    # Python dependencies
├── README.md          # Documentation (this file)
└── examples/          # Example PDFs and outputs (optional)
```

### Contributing

Feel free to submit issues or pull requests for improvements!

## License

This project is open source and available for educational and commercial use.

## Version History

- **1.0.0** (2025-12-15): Initial release
  - Basic PDF to HTML conversion
  - Table extraction
  - Image detection
  - Metadata preservation
  - Beautiful default styling

## Author

Created with Claude Code - PDF to HTML Conversion Project

## Support

For issues, questions, or suggestions, please open an issue in the repository.

---

**Happy Converting! 📄 → 🌐**
