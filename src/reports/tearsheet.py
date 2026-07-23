"""
PDF Tearsheet Generator - Days 33-35
Generates 2-page company tearsheets with financial metrics, pros/cons, and key insights
Simplified text-based approach for reliability
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
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from typing import Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TearsheetGenerator:
    """Generate 2-page PDF tearsheets for companies"""
    
    def __init__(self, db_path: str = 'data/nifty100.db'):
        """Initialize with database connection"""
        self.db_path = db_path
        self.conn = None
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
        
    def setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CompanyHeader',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#1f3864'),
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.HexColor('#1f3864'),
            spaceAfter=6,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='ProText',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.darkgreen,
            leftIndent=15,
            bulletIndent=5,
            spaceBefore=2,
            spaceAfter=2
        ))
        
        self.styles.add(ParagraphStyle(
            name='ConText',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.red,
            leftIndent=15,
            bulletIndent=5,
            spaceBefore=2,
            spaceAfter=2
        ))

        
    def connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(self.db_path)
        logger.info(f"Connected to database: {self.db_path}")
        
    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def load_company_data(self, company_id: str) -> Dict:
        """Load all data needed for a company tearsheet"""
        # Get company basic info
        company_query = "SELECT * FROM companies WHERE id = ?"
        company_df = pd.read_sql_query(company_query, self.conn, params=(company_id,))
        
        if len(company_df) == 0:
            logger.warning(f"No data found for company: {company_id}")
            return None
        
        # Get sector
        sector_query = "SELECT broad_sector FROM sectors WHERE company_id = ?"
        sector_df = pd.read_sql_query(sector_query, self.conn, params=(company_id,))
        sector = sector_df.iloc[0]['broad_sector'] if len(sector_df) > 0 else 'Unknown'
        
        # Get latest financial ratios
        ratios_query = """
        SELECT * FROM financial_ratios 
        WHERE company_id = ? 
        ORDER BY year DESC LIMIT 1
        """
        ratios_df = pd.read_sql_query(ratios_query, self.conn, params=(company_id,))
        
        # Get 10-year P&L data
        pl_query = """
        SELECT year, sales, net_profit 
        FROM profitandloss 
        WHERE company_id = ? 
        ORDER BY year DESC LIMIT 10
        """
        pl_df = pd.read_sql_query(pl_query, self.conn, params=(company_id,))
        
        # Get pros/cons
        pros_cons_path = Path('output/pros_cons_generated.csv')
        if pros_cons_path.exists():
            pc_df = pd.read_csv(pros_cons_path)
            pros = pc_df[(pc_df['company_id'] == company_id) & (pc_df['type'] == 'pro')]
            cons = pc_df[(pc_df['company_id'] == company_id) & (pc_df['type'] == 'con')]
        else:
            pros = pd.DataFrame()
            cons = pd.DataFrame()
        
        # Get cash flow intelligence
        cf_intel_path = Path('output/cashflow_intelligence.xlsx')
        if cf_intel_path.exists():
            cf_intel_df = pd.read_excel(cf_intel_path, header=1)
            cf_intel = cf_intel_df[cf_intel_df['company_id'] == company_id]
        else:
            cf_intel = pd.DataFrame()

        return {
            'company': company_df.iloc[0],
            'sector': sector,
            'ratios': ratios_df.iloc[0] if len(ratios_df) > 0 else None,
            'pl_history': pl_df,
            'pros': pros,
            'cons': cons,
            'cf_intelligence': cf_intel.iloc[0] if len(cf_intel) > 0 else None
        }

    def connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(self.db_path)
        
    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def load_company_data(self, company_id: str) -> Dict:
        """Load all data needed for a company tearsheet"""
        # Get company basic info
        company_query = "SELECT * FROM companies WHERE id = ?"
        company_df = pd.read_sql_query(company_query, self.conn, params=(company_id,))
        
        if len(company_df) == 0:
            return None
        
        # Get sector
        sector_query = "SELECT broad_sector FROM sectors WHERE company_id = ?"
        sector_df = pd.read_sql_query(sector_query, self.conn, params=(company_id,))
        sector = sector_df.iloc[0]['broad_sector'] if len(sector_df) > 0 else 'Unknown'
        
        # Get latest financial ratios
        ratios_query = """
        SELECT * FROM financial_ratios 
        WHERE company_id = ? 
        ORDER BY year DESC LIMIT 1
        """
        ratios_df = pd.read_sql_query(ratios_query, self.conn, params=(company_id,))
        
        # Get 5-year P&L data for trend
        pl_query = """
        SELECT year, sales, net_profit 
        FROM profitandloss 
        WHERE company_id = ? 
        ORDER BY year DESC LIMIT 5
        """
        pl_df = pd.read_sql_query(pl_query, self.conn, params=(company_id,))
        
        # Get pros/cons
        pros_cons_path = Path('output/pros_cons_generated.csv')
        if pros_cons_path.exists():
            pc_df = pd.read_csv(pros_cons_path)
            pros = pc_df[(pc_df['company_id'] == company_id) & (pc_df['type'] == 'pro')]
            cons = pc_df[(pc_df['company_id'] == company_id) & (pc_df['type'] == 'con')]
        else:
            pros = pd.DataFrame()
            cons = pd.DataFrame()
        
        # Get cash flow intelligence
        cf_intel_path = Path('output/cashflow_intelligence.xlsx')
        if cf_intel_path.exists():
            cf_intel_df = pd.read_excel(cf_intel_path, header=1)
            cf_intel = cf_intel_df[cf_intel_df['company_id'] == company_id]
        else:
            cf_intel = pd.DataFrame()

        return {
            'company': company_df.iloc[0],
            'sector': sector,
            'ratios': ratios_df.iloc[0] if len(ratios_df) > 0 else None,
            'pl_history': pl_df,
            'pros': pros,
            'cons': cons,
            'cf_intelligence': cf_intel.iloc[0] if len(cf_intel) > 0 else None
        }
    
    def build_page1(self, data: Dict) -> List:
        """Build page 1 content: Header, KPIs, Revenue/Profit Summary"""
        story = []
        company = data['company']
        ratios = data['ratios']
        
        # Header
        header_text = f"<b>{company['company_name']}</b><br/>{company['id']} | {data['sector']}"
        story.append(Paragraph(header_text, self.styles['CompanyHeader']))
        story.append(Spacer(1, 0.2*inch))
        
        # KPI Tiles Table (2 rows x 3 cols)
        if ratios is not None:
            kpi_data = [
                ['ROE', 'ROCE', 'OPM'],
                [
                    f"{ratios['return_on_equity_pct']:.1f}%" if pd.notna(ratios['return_on_equity_pct']) else 'N/A',
                    f"{ratios['return_on_capital_pct']:.1f}%" if pd.notna(ratios['return_on_capital_pct']) else 'N/A',
                    f"{ratios['operating_profit_margin_pct']:.1f}%" if pd.notna(ratios['operating_profit_margin_pct']) else 'N/A'
                ],
                ['D/E Ratio', 'Interest Coverage', 'EPS'],
                [
                    f"{ratios['debt_to_equity']:.2f}" if pd.notna(ratios['debt_to_equity']) else 'N/A',
                    f"{ratios['interest_coverage']:.1f}x" if pd.notna(ratios['interest_coverage']) and ratios['interest_coverage'] != 999 else 'Debt Free',
                    f"₹{ratios['earnings_per_share']:.2f}" if pd.notna(ratios['earnings_per_share']) else 'N/A'
                ]
            ]
            
            kpi_table = Table(kpi_data, colWidths=[2*inch, 2*inch, 2*inch])
            kpi_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f3864')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#1f3864')),
                ('TEXTCOLOR', (0, 2), (-1, 2), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            
            story.append(kpi_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Revenue & Profit Trend (5 years)
        story.append(Paragraph("5-Year Financial Trend", self.styles['SectionHeader']))
        
        if len(data['pl_history']) > 0:
            pl_data = [['Year', 'Revenue (Cr)', 'Net Profit (Cr)']]
            for _, row in data['pl_history'].iterrows():
                pl_data.append([
                    str(row['year'])[:7],  # Truncate year
                    f"₹{row['sales']:,.0f}" if pd.notna(row['sales']) else 'N/A',
                    f"₹{row['net_profit']:,.0f}" if pd.notna(row['net_profit']) else 'N/A'
                ])
            
            pl_table = Table(pl_data, colWidths=[2*inch, 2*inch, 2*inch])
            pl_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e9ecef')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            
            story.append(pl_table)
        
        return story
    
    def build_page2(self, data: Dict) -> List:
        """Build page 2 content: Cash Flow Intelligence, Pros/Cons, Capital Allocation"""
        story = []
        
        story.append(PageBreak())
        
        # Cash Flow Intelligence
        story.append(Paragraph("Cash Flow Intelligence", self.styles['SectionHeader']))
        
        if data['cf_intelligence'] is not None:
            cf = data['cf_intelligence']
            cf_data = [
                ['Metric', 'Value'],
                ['CFO Quality', cf['cfo_quality_label'] if pd.notna(cf.get('cfo_quality_label')) else 'N/A'],
                ['CapEx Intensity', cf['capex_label'] if pd.notna(cf.get('capex_label')) else 'N/A'],
                ['Capital Allocation', cf['capital_allocation_label'] if pd.notna(cf.get('capital_allocation_label')) else 'N/A'],
                ['FCF 5Y CAGR', f"{cf['fcf_cagr_5yr']:.1f}%" if pd.notna(cf.get('fcf_cagr_5yr')) else 'N/A'],
                ['Distress Flag', 'YES ⚠' if cf.get('distress_flag') == 1 else 'No']
            ]
            
            cf_table = Table(cf_data, colWidths=[3*inch, 3*inch])
            cf_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e9ecef')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            
            story.append(cf_table)
            story.append(Spacer(1, 0.2*inch))
        
        # Pros Section
        story.append(Paragraph("✓ Investment Strengths (Pros)", self.styles['SectionHeader']))
        
        if len(data['pros']) > 0:
            for _, pro in data['pros'].head(5).iterrows():  # Limit to top 5
                # Use Paragraph with wordwrap
                text = f"• {pro['text']}"
                story.append(Paragraph(text, self.styles['ProText']))
        else:
            story.append(Paragraph("• No significant pros identified", self.styles['ProText']))
        
        story.append(Spacer(1, 0.2*inch))
        
        # Cons Section
        story.append(Paragraph("⚠ Investment Concerns (Cons)", self.styles['SectionHeader']))
        
        if len(data['cons']) > 0:
            for _, con in data['cons'].head(5).iterrows():  # Limit to top 5
                # Use Paragraph with wordwrap
                text = f"• {con['text']}"
                story.append(Paragraph(text, self.styles['ConText']))
        else:
            story.append(Paragraph("• No significant concerns identified", self.styles['ConText']))
        
        return story
    
    def generate_tearsheet(self, company_id: str, output_path: Path) -> bool:
        """Generate a single company tearsheet"""
        try:
            # Load data
            data = self.load_company_data(company_id)
            
            if data is None:
                logger.warning(f"Skipping {company_id} - insufficient data")
                return False
            
            # Check minimum data requirement (at least 3 years)
            if len(data['pl_history']) < 3:
                logger.warning(f"Skipping {company_id} - fewer than 3 years of data")
                return False
            
            # Create PDF
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=letter,
                rightMargin=0.5*inch,
                leftMargin=0.5*inch,
                topMargin=0.5*inch,
                bottomMargin=0.5*inch
            )
            
            # Build story
            story = []
            story.extend(self.build_page1(data))
            story.extend(self.build_page2(data))
            
            # Generate PDF
            doc.build(story)
            
            return True
            
        except Exception as e:
            logger.error(f"Error generating tearsheet for {company_id}: {str(e)}")
            return False
    
    def generate_batch(self, output_dir: str = 'reports/tearsheets') -> Dict:
        """Generate tearsheets for all companies"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        self.connect()
        
        # Get all companies
        companies_query = "SELECT id FROM companies ORDER BY id"
        companies_df = pd.read_sql_query(companies_query, self.conn)
        
        logger.info(f"Generating tearsheets for {len(companies_df)} companies...")
        
        generated = []
        skipped = []
        
        for _, row in companies_df.iterrows():
            company_id = row['id']
            output_file = output_path / f"{company_id}_tearsheet.pdf"
            
            success = self.generate_tearsheet(company_id, output_file)
            
            if success:
                generated.append(company_id)
                logger.info(f"✓ Generated: {company_id}")
            else:
                skipped.append(company_id)
        
        self.disconnect()
        
        # Save skipped list
        if skipped:
            skipped_df = pd.DataFrame({'ticker': skipped})
            skipped_df.to_csv('output/skipped_tearsheets.csv', index=False)
            logger.info(f"Saved {len(skipped)} skipped tickers to output/skipped_tearsheets.csv")
        
        logger.info(f"\n=== Tearsheet Generation Summary ===")
        logger.info(f"Generated: {len(generated)} tearsheets")
        logger.info(f"Skipped: {len(skipped)} companies")
        
        return {
            'generated': generated,
            'skipped': skipped
        }


def main():
    """Main entry point"""
    generator = TearsheetGenerator()
    generator.generate_batch()
    logger.info("✓ Batch tearsheet generation completed")


if __name__ == '__main__':
    main()
