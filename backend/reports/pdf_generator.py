"""
PDF Report Generator - Creates summary reports from CSV data.
"""
import csv
import io
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import pandas as pd

logger = logging.getLogger(__name__)


class PDFReportGenerator:
    """Generate PDF reports from CSV data with summaries and statistics."""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Heading style
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=12,
            spaceBefore=20,
            fontName='Helvetica-Bold'
        ))
        
        # Subheading style
        self.styles.add(ParagraphStyle(
            name='CustomSubHeading',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#34495e'),
            spaceAfter=8,
            spaceBefore=12,
            fontName='Helvetica-Bold'
        ))
        
        # Body text style
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#333333'),
            spaceAfter=6,
            leading=14
        ))
        
        # Metadata style
        self.styles.add(ParagraphStyle(
            name='Metadata',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#666666'),
            spaceAfter=4
        ))
    
    def generate_pdf_from_csv(
        self, 
        csv_data: str, 
        title: str = "Data Report",
        report_description: Optional[str] = None
    ) -> bytes:
        """
        Generate PDF report from CSV data.
        
        Args:
            csv_data: CSV data as string
            title: Report title
            report_description: Optional description of the report
            
        Returns:
            PDF file as bytes
        """
        try:
            # Parse CSV data
            df = pd.read_csv(io.StringIO(csv_data))
            
            # Create PDF buffer
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=0.75*inch,
                leftMargin=0.75*inch,
                topMargin=0.75*inch,
                bottomMargin=0.75*inch
            )
            
            # Build PDF content
            story = []
            
            # Title
            story.append(Paragraph(title, self.styles['CustomTitle']))
            story.append(Spacer(1, 0.2*inch))
            
            # Report metadata
            story.append(self._create_metadata_section())
            story.append(Spacer(1, 0.3*inch))
            
            # Description if provided
            if report_description:
                story.append(Paragraph("Report Description", self.styles['CustomHeading']))
                story.append(Paragraph(report_description, self.styles['CustomBody']))
                story.append(Spacer(1, 0.2*inch))
            
            # Summary Statistics
            story.append(Paragraph("Summary Statistics", self.styles['CustomHeading']))
            story.extend(self._create_summary_statistics(df))
            story.append(Spacer(1, 0.2*inch))
            
            # Data Preview Table (first 20 rows)
            story.append(Paragraph("Data Preview", self.styles['CustomHeading']))
            story.append(Paragraph(
                f"Showing first {min(20, len(df))} rows of {len(df)} total rows",
                self.styles['Metadata']
            ))
            story.append(Spacer(1, 0.1*inch))
            story.extend(self._create_data_table(df.head(20)))
            
            # If more rows, add note
            if len(df) > 20:
                story.append(Spacer(1, 0.1*inch))
                story.append(Paragraph(
                    f"Note: Only first 20 rows shown. Total rows: {len(df)}",
                    self.styles['Metadata']
                ))
            
            # Build PDF
            doc.build(story)
            
            # Get PDF bytes
            buffer.seek(0)
            pdf_bytes = buffer.read()
            buffer.close()
            
            logger.info(f"Successfully generated PDF report: {title}, {len(df)} rows")
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            raise
    
    def _create_metadata_section(self) -> List:
        """Create metadata section with generation date/time."""
        metadata = []
        now = datetime.now()
        metadata.append(Paragraph(
            f"<b>Generated:</b> {now.strftime('%B %d, %Y at %I:%M %p')}",
            self.styles['Metadata']
        ))
        return metadata
    
    def _create_summary_statistics(self, df: pd.DataFrame) -> List:
        """Create summary statistics section."""
        stats = []
        
        # Basic info
        stats.append(Paragraph(f"<b>Total Records:</b> {len(df):,}", self.styles['CustomBody']))
        stats.append(Paragraph(f"<b>Total Columns:</b> {len(df.columns)}", self.styles['CustomBody']))
        stats.append(Spacer(1, 0.1*inch))
        
        # Column statistics
        stats.append(Paragraph("Column Information", self.styles['CustomSubHeading']))
        
        # Create table for column stats
        col_data = [['Column Name', 'Data Type', 'Non-Null Count', 'Null Count']]
        
        for col in df.columns:
            non_null = df[col].notna().sum()
            null_count = df[col].isna().sum()
            dtype = str(df[col].dtype)
            col_data.append([str(col), dtype, f"{non_null:,}", f"{null_count:,}"])
        
        col_table = Table(col_data, colWidths=[2.5*inch, 1.5*inch, 1.2*inch, 1.2*inch])
        col_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        
        stats.append(col_table)
        stats.append(Spacer(1, 0.15*inch))
        
        # Numeric column statistics
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            stats.append(Paragraph("Numeric Column Statistics", self.styles['CustomSubHeading']))
            
            num_stats_data = [['Column', 'Sum', 'Mean', 'Min', 'Max']]
            
            for col in numeric_cols[:10]:  # Limit to first 10 numeric columns
                col_sum = df[col].sum()
                col_mean = df[col].mean()
                col_min = df[col].min()
                col_max = df[col].max()
                
                num_stats_data.append([
                    str(col),
                    f"{col_sum:,.2f}" if pd.notna(col_sum) else "N/A",
                    f"{col_mean:,.2f}" if pd.notna(col_mean) else "N/A",
                    f"{col_min:,.2f}" if pd.notna(col_min) else "N/A",
                    f"{col_max:,.2f}" if pd.notna(col_max) else "N/A"
                ])
            
            num_table = Table(num_stats_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.2*inch, 1.2*inch])
            num_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ]))
            
            stats.append(num_table)
            if len(numeric_cols) > 10:
                stats.append(Spacer(1, 0.05*inch))
                stats.append(Paragraph(
                    f"Note: Showing statistics for first 10 numeric columns. Total numeric columns: {len(numeric_cols)}",
                    self.styles['Metadata']
                ))
        
        return stats
    
    def _create_data_table(self, df: pd.DataFrame) -> List:
        """Create data preview table."""
        table_data = []
        
        # Header row
        header = [str(col) for col in df.columns]
        table_data.append(header)
        
        # Data rows (limit columns if too many)
        max_cols = 8  # Limit columns for readability
        display_cols = df.columns[:max_cols] if len(df.columns) > max_cols else df.columns
        
        for idx, row in df.iterrows():
            row_data = []
            for col in display_cols:
                value = row[col]
                # Format the value
                if pd.isna(value):
                    row_data.append("N/A")
                elif isinstance(value, (int, float)):
                    row_data.append(f"{value:,.2f}" if isinstance(value, float) else f"{value:,}")
                else:
                    # Truncate long strings
                    str_val = str(value)
                    row_data.append(str_val[:30] + "..." if len(str_val) > 30 else str_val)
            table_data.append(row_data)
        
        # Create table
        # Calculate column widths
        num_cols = len(display_cols)
        if num_cols > 0:
            col_width = (7.5 * inch) / num_cols
            col_widths = [col_width] * num_cols
        else:
            col_widths = None
        
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        
        # Style the table
        table.setStyle(TableStyle([
            # Header style
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        result = [table]
        
        # Add note if columns were truncated
        if len(df.columns) > max_cols:
            result.append(Spacer(1, 0.1*inch))
            result.append(Paragraph(
                f"Note: Showing first {max_cols} columns. Total columns: {len(df.columns)}",
                self.styles['Metadata']
            ))
        
        return result
    
    def generate_pdf_from_file(self, csv_file_path: str, title: str = "Data Report") -> bytes:
        """
        Generate PDF from CSV file.
        
        Args:
            csv_file_path: Path to CSV file
            title: Report title
            
        Returns:
            PDF file as bytes
        """
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            csv_data = f.read()
        
        return self.generate_pdf_from_csv(csv_data, title)

