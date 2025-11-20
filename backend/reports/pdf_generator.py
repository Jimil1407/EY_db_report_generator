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
            story.extend(self._create_metadata_section())
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
            
            # Automated Insights
            story.append(Paragraph("Automated Insights", self.styles['CustomHeading']))
            story.extend(self._create_automated_insights(df))
            story.append(Spacer(1, 0.2*inch))
            
            # Numeric Highlights
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                story.append(Paragraph("Numeric Highlights", self.styles['CustomSubHeading']))
                story.extend(self._create_numeric_highlights(df[numeric_cols]))
                story.append(Spacer(1, 0.2*inch))
            
            # Categorical Highlights
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns
            if len(categorical_cols) > 0:
                story.append(Paragraph("Categorical Highlights", self.styles['CustomSubHeading']))
                story.extend(self._create_categorical_highlights(df[categorical_cols]))
            
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
    
    def _create_automated_insights(self, df: pd.DataFrame) -> List:
        """Create textual insights summarizing dataset characteristics."""
        insights = []
        row_count = len(df)
        col_count = len(df.columns)
        numeric_cols = df.select_dtypes(include=['number'])
        categorical_cols = df.select_dtypes(include=['object', 'category'])
        
        bullet_points = [
            f"Dataset contains {row_count:,} rows across {col_count} columns.",
            f"{len(numeric_cols.columns)} numeric columns and {len(categorical_cols.columns)} categorical columns detected."
        ]
        
        null_counts = df.isna().sum()
        if null_counts.max() > 0:
            worst_col = null_counts.idxmax()
            worst_pct = (null_counts[worst_col] / max(row_count, 1)) * 100
            bullet_points.append(
                f"Highest missing data observed in '{worst_col}' "
                f"({null_counts[worst_col]:,} cells • {worst_pct:.1f}% of records)."
            )
        
        if not numeric_cols.empty:
            std_series = numeric_cols.std(numeric_only=True).dropna()
            if not std_series.empty:
                volatile_col = std_series.idxmax()
                bullet_points.append(
                    f"'{volatile_col}' shows the greatest variability (std dev {std_series[volatile_col]:,.2f})."
                )
            sum_series = numeric_cols.sum(numeric_only=True).dropna()
            if not sum_series.empty:
                top_sum = sum_series.idxmax()
                bullet_points.append(
                    f"'{top_sum}' contributes the largest aggregate value ({sum_series[top_sum]:,.2f})."
                )
        
        if not categorical_cols.empty:
            unique_counts = categorical_cols.nunique(dropna=True)
            if not unique_counts.empty:
                richest_col = unique_counts.idxmax()
                bullet_points.append(
                    f"'{richest_col}' has the widest categorical diversity ({unique_counts[richest_col]:,} unique values)."
                )
        
        for text in bullet_points:
            insights.append(Paragraph(f"• {text}", self.styles['CustomBody']))
        return insights
    
    def _create_numeric_highlights(self, numeric_df: pd.DataFrame, limit: int = 6) -> List:
        """Create aggregated statistics table for top numeric columns."""
        highlights = []
        summary_rows = []
        
        for col in numeric_df.columns:
            series = numeric_df[col].dropna()
            if series.empty:
                continue
            summary_rows.append({
                "column": str(col),
                "sum": series.sum(),
                "mean": series.mean(),
                "median": series.median(),
                "std": series.std(),
                "min": series.min(),
                "max": series.max(),
            })
        
        if not summary_rows:
            return [Paragraph("No numeric metrics available.", self.styles['CustomBody'])]
        
        summary_rows = sorted(summary_rows, key=lambda x: abs(x["sum"]), reverse=True)[:limit]
        
        table_data = [
            ["Column", "Sum", "Mean", "Median", "Std Dev", "Min", "Max"]
        ]
        for row in summary_rows:
            table_data.append([
                row["column"],
                f"{row['sum']:,.2f}",
                f"{row['mean']:,.2f}",
                f"{row['median']:,.2f}",
                f"{row['std']:,.2f}" if pd.notna(row['std']) else "N/A",
                f"{row['min']:,.2f}",
                f"{row['max']:,.2f}",
            ])
        
        table = Table(
            table_data,
            colWidths=[1.5*inch, 1.1*inch, 1.1*inch, 1.1*inch, 1.1*inch, 1.1*inch, 1.1*inch],
            repeatRows=1
        )
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        ]))
        
        highlights.append(table)
        if len(numeric_df.columns) > limit:
            highlights.append(Spacer(1, 0.1*inch))
            highlights.append(Paragraph(
                f"Note: Showing top {limit} numeric columns by aggregate magnitude "
                f"(total numeric columns: {len(numeric_df.columns)}).",
                self.styles['Metadata']
            ))
        return highlights
    
    def _create_categorical_highlights(self, categorical_df: pd.DataFrame, limit: int = 3, top_values: int = 5) -> List:
        """Summarize most frequent categories for selected columns."""
        highlights = []
        categorical_columns = [col for col in categorical_df.columns if categorical_df[col].notna().any()]
        
        if not categorical_columns:
            return [Paragraph("No categorical insights available.", self.styles['CustomBody'])]
        
        for col in categorical_columns[:limit]:
            value_counts = categorical_df[col].value_counts(dropna=True).head(top_values)
            total = value_counts.sum()
            table_data = [["Category", "Records", "Share of non-null"]]
            for category, count in value_counts.items():
                share = (count / total) * 100 if total else 0
                label = str(category) if pd.notna(category) else "N/A"
                if len(label) > 25:
                    label = label[:25] + "..."
                table_data.append([label, f"{count:,}", f"{share:.1f}%"])
            
            highlights.append(Paragraph(str(col), self.styles['CustomSubHeading']))
            table = Table(table_data, colWidths=[3.0*inch, 1.2*inch, 1.5*inch], repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7f8c8d')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ecf0f1')]),
            ]))
            highlights.append(table)
            highlights.append(Spacer(1, 0.1*inch))
        
        if len(categorical_columns) > limit:
            highlights.append(Paragraph(
                f"Note: Displaying first {limit} categorical columns (of {len(categorical_columns)}) "
                f"with their top {top_values} categories.",
                self.styles['Metadata']
            ))
        
        return highlights
    
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

