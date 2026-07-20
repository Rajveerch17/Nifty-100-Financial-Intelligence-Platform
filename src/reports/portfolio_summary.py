"""
Portfolio Summary PDF - Day 35
Generates a comprehensive portfolio summary with one page per company
Shows company name, sector, top 6 KPIs, and trend arrows
"""

import pandas as pd
import sqlite3
from pathlib import Path
import logging
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer,
    PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from typing import Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PortfolioSummary:
    """Generate portfolio summary PDF with all companies"""
    
    def __init__(self, db_path: str = 'data/nifty100.db'):
        """Initialize with database connection"""
        self.db_path = db_path
        self.conn = None
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
        
    def setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CompanyName',
            parent=self.styles['Heading1'],
            fontSize=14,
            textColor=colors.HexColor('#1f3864'),
            spaceAfter=4,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='Sector',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.grey,
            spaceAfter=10,
            alignment=TA_CENTER,
            fontName='Helvetica'
        ))
        
    def connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(self.db_path)
        
    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def get_trend_arrow(self, current_val, prev_val) -> str:
        """Calculate trend arrow based on change"""
        if pd.isna(current_val) or pd.isna(prev_val):
            return '→'
        
        change_pct = ((current_val - prev_val) / abs(prev_val)) * 100 if prev_val != 0 else 0
        
        if abs(change_pct) <= 2:
            return '→'
        elif change_pct > 2:
            return '↑'
        else:
            return '↓'
    
    def load_company_summary(self, company_id: str) -> Dict:
        """Load summary data for a company"""
        # Get company and sector
        company_query = "SELECT company_name FROM companies WHERE id = ?"
        company_df = pd.read_sql_query(company_query, self.conn, params=(company_id,))
        
        if len(company_df) == 0:
            return None
        
        sector_query = "SELECT broad_sector FROM sectors WHERE company_id = ?"
        sector_df = pd.read_sql_query(sector_query, self.conn, params=(company_id,))
        sector = sector_df.iloc[0]['broad_sector'] if len(sector_df) > 0 else 'Unknown'
        
        # Get latest 2 years of ratios for trend
        ratios_query = """
        SELECT * FROM financial_ratios 
        WHERE company_id = ? 
        ORDER BY year DESC LIMIT 2
        """
        ratios_df = pd.read_sql_query(ratios_query, self.conn, params=(company_id,))
        
        if len(ratios_df) < 2:
            return None
        
        current = ratios_df.iloc[0]
        previous = ratios_df.iloc[1]
        
        return {
            'company_name': company_df.iloc[0]['company_name'],
            'ticker': company_id,
            'sector': sector,
            'current': current,
            'previous': previous
        }
    
    def build_company_page(self, company_id: str) -> List:
        """Build one page for a company"""
        story = []
        
        data = self.load_company_summary(company_id)
        
        if data is None:
            return []
        
        # Header
        story.append(Paragraph(f"<b>{data['company_name']}</b>", self.styles['CompanyName']))
        story.append(Paragraph(f"{data['ticker']} | {data['sector']}", self.styles['Sector']))
        story.append(Spacer(1, 0.1*inch))
        
        # Top 6 KPIs with trend arrows
        current = data['current']
        previous = data['previous']
        
        kpis = [
            ('ROE %', current['return_on_equity_pct'], previous['return_on_equity_pct']),
            ('ROCE %', current['return_on_capital_pct'], previous['return_on_capital_pct']),
            ('OPM %', current['operating_profit_margin_pct'], previous['operating_profit_margin_pct']),
            ('D/E', current['debt_to_equity'], previous['debt_to_equity']),
            ('ICR', current['interest_coverage'] if current['interest_coverage'] != 999 else 0, 
                    previous['interest_coverage'] if previous['interest_coverage'] != 999 else 0),
            ('EPS', current['earnings_per_share'], previous['earnings_per_share'])
        ]
        
        kpi_data = [['Metric', 'Value', 'Trend']]
        
        for name, curr_val, prev_val in kpis:
            arrow = self.get_trend_arrow(curr_val, prev_val)
            value_str = f"{curr_val:.2f}" if pd.notna(curr_val) else 'N/A'
            kpi_data.append([name, value_str, arrow])
        
        kpi_table = Table(kpi_data, colWidths=[2*inch, 2*inch, 1*inch])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e9ecef')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        story.append(kpi_table)
        story.append(PageBreak())
        
        return story
    
    def generate(self, output_path: str = 'reports/portfolio/portfolio_summary.pdf'):
        """Generate the complete portfolio summary PDF"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.connect()
        
        # Get all companies in alphabetical order by ticker
        companies_query = "SELECT id FROM companies ORDER BY id"
        companies_df = pd.read_sql_query(companies_query, self.conn)
        
        logger.info(f"Generating portfolio summary for {len(companies_df)} companies...")
        
        # Create PDF
        doc = SimpleDocTemplate(
            str(output_file),
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        # Build story
        story = []
        
        # Title page
        story.append(Paragraph("<b>Nifty 100 Portfolio Summary</b>", self.styles['Title']))
        story.append(Paragraph("Financial Intelligence Platform", self.styles['Normal']))
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(f"Total Companies: {len(companies_df)}", self.styles['Normal']))
        story.append(Paragraph("Key Performance Indicators with Year-over-Year Trends", self.styles['Normal']))
        story.append(PageBreak())
        
        # Add each company page
        for _, row in companies_df.iterrows():
            company_id = row['id']
            company_story = self.build_company_page(company_id)
            story.extend(company_story)
        
        # Generate PDF
        doc.build(story)
        
        self.disconnect()
        
        logger.info(f"✓ Portfolio summary generated: {output_file}")
        logger.info(f"Total pages: {len(companies_df) + 1} (1 title + {len(companies_df)} companies)")


def main():
    """Main entry point"""
    generator = PortfolioSummary()
    generator.generate()
    logger.info("✓ Portfolio summary generation completed")


if __name__ == '__main__':
    main()
