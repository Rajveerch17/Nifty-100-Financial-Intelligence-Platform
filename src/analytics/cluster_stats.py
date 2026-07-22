"""
Cluster Statistics Module - Day 37
Profile clusters, generate correlation heatmap, outlier detection
"""

import pandas as pd
import sqlite3
from pathlib import Path
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClusterStats:
    """Generate cluster statistics and visualizations"""
    
    KPI_COLS = ['return_on_equity_pct', 'debt_to_equity', 'revenue_cagr_5yr',
                'operating_profit_margin_pct', 'free_cash_flow_cr',
                'return_on_capital_pct', 'net_profit_margin_pct', 
                'asset_turnover', 'dividend_payout_ratio_pct', 'interest_coverage']
    
    def __init__(self, db_path='data/nifty100.db'):
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        
    def disconnect(self):
        if self.conn:
            self.conn.close()
            
    def load_latest_data(self):
        """Load latest year data for all companies"""
        query = f"""
        SELECT company_id, {', '.join(self.KPI_COLS)},
               ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY year DESC) as rn
        FROM financial_ratios
        """
        df = pd.read_sql_query(query, self.conn)
        return df[df['rn'] == 1].drop('rn', axis=1)
        
    def profile_clusters(self, cluster_labels_path='output/cluster_labels.csv'):
        """Profile each cluster with mean/median stats"""
        labels_df = pd.read_csv(cluster_labels_path)
        df = self.load_latest_data()
        merged = df.merge(labels_df[['company_id', 'cluster_id', 'cluster_name']], on='company_id')
        
        profile = merged.groupby('cluster_name')[['return_on_equity_pct', 'debt_to_equity', 
                                                   'revenue_cagr_5yr', 'operating_profit_margin_pct',
                                                   'free_cash_flow_cr']].agg(['mean', 'median'])
        
        output_path = 'output/cluster_profile.csv'
        Path(output_path).parent.mkdir(exist_ok=True)
        profile.to_csv(output_path)
        logger.info(f"Saved cluster profile to {output_path}")
        return profile
        
    def generate_correlation_heatmap(self, output_path='reports/correlation_heatmap.png'):
        """Generate Pearson correlation heatmap"""
        df = self.load_latest_data()
        corr_matrix = df[self.KPI_COLS].corr()
        
        Path(output_path).parent.mkdir(exist_ok=True)
        plt.figure(figsize=(12, 10))
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, fmt='.2f')
        plt.title('Pearson Correlation of 10 KPIs')
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        logger.info(f"Saved correlation heatmap to {output_path}")
        
    def detect_outliers(self, output_path='output/outlier_report.csv'):
        """Detect outliers using Z-score > 3"""
        df = self.load_latest_data()
        outliers = []
        
        for col in self.KPI_COLS:
            if col in df.columns:
                z_scores = stats.zscore(df[col].dropna())
                outlier_mask = abs(z_scores) > 3
                outlier_companies = df.loc[df[col].dropna().index[outlier_mask], 'company_id']
                
                for company_id in outlier_companies:
                    outliers.append({
                        'company_id': company_id,
                        'metric': col,
                        'z_score': z_scores[outlier_mask].tolist()[0] if len(z_scores[outlier_mask]) > 0 else 0
                    })
        
        if outliers:
            outlier_df = pd.DataFrame(outliers)
            Path(output_path).parent.mkdir(exist_ok=True)
            outlier_df.to_csv(output_path, index=False)
            logger.info(f"Saved {len(outliers)} outliers to {output_path}")
        else:
            logger.info("No outliers detected")
            
    def generate_portfolio_stats(self, output_path='output/portfolio_stats.csv'):
        """Generate P10-P90 statistics for all KPIs"""
        df = self.load_latest_data()
        stats_df = df[self.KPI_COLS].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9])
        
        Path(output_path).parent.mkdir(exist_ok=True)
        stats_df.to_csv(output_path)
        logger.info(f"Saved portfolio stats to {output_path}")
        
    def run(self):
        """Main execution"""
        try:
            self.connect()
            self.profile_clusters()
            self.generate_correlation_heatmap()
            self.detect_outliers()
            self.generate_portfolio_stats()
            logger.info("✓ Cluster statistics completed successfully")
        finally:
            self.disconnect()


def main():
    stats = ClusterStats()
    stats.run()


if __name__ == '__main__':
    main()
