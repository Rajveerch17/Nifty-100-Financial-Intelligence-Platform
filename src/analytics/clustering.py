"""
KMeans Clustering Module - Day 36
Clusters 92 companies into 5 archetypes using financial metrics
"""

import pandas as pd
import sqlite3
from pathlib import Path
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClusterEngine:
    """KMeans clustering for company archetypes"""
    
    FEATURES = ['return_on_equity_pct', 'debt_to_equity', 'revenue_cagr_5yr', 
                'operating_profit_margin_pct', 'free_cash_flow_cr']
    
    def __init__(self, db_path='data/nifty100.db'):
        self.db_path = db_path
        self.conn = None
        self.df = None
        self.scaled_data = None
        self.kmeans = None
        
    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        
    def disconnect(self):
        if self.conn:
            self.conn.close()
            
    def load_data(self):
        """Load latest year financial ratios for clustering"""
        query = f"""
        SELECT company_id, {', '.join(self.FEATURES)},
               ROW_NUMBER() OVER (PARTITION BY company_id ORDER BY year DESC) as rn
        FROM financial_ratios
        """
        df = pd.read_sql_query(query, self.conn)
        self.df = df[df['rn'] == 1].drop('rn', axis=1)
        logger.info(f"Loaded {len(self.df)} companies for clustering")
        
    def impute_missing(self):
        """Impute missing values with median"""
        for col in self.FEATURES:
            median_val = self.df[col].median()
            self.df[col].fillna(median_val, inplace=True)
        logger.info("Imputed missing values with median")
        
    def scale_features(self):
        """Apply StandardScaler"""
        scaler = StandardScaler()
        self.scaled_data = scaler.fit_transform(self.df[self.FEATURES])
        logger.info("Scaled features using StandardScaler")
        
    def fit_kmeans(self, n_clusters=5):
        """Run KMeans clustering"""
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        self.df['cluster_id'] = self.kmeans.fit_predict(self.scaled_data)
        self.df['distance_from_centroid'] = self.kmeans.transform(self.scaled_data).min(axis=1)
        logger.info(f"KMeans clustering complete with {n_clusters} clusters")
        
    def assign_cluster_names(self):
        """Assign descriptive names to clusters"""
        cluster_names = {
            0: "High-Quality Compounders",
            1: "Defensive Dividend Payers", 
            2: "Value Cyclicals",
            3: "Distressed/Turnaround",
            4: "Emerging Growth"
        }
        self.df['cluster_name'] = self.df['cluster_id'].map(cluster_names)
        
    def generate_elbow_plot(self, output_path='reports/elbow_plot.png'):
        """Generate elbow plot for k=2 to 10"""
        Path(output_path).parent.mkdir(exist_ok=True)
        inertias = []
        k_range = range(2, 11)
        
        for k in k_range:
            km = KMeans(n_clusters=k, random_state=42)
            km.fit(self.scaled_data)
            inertias.append(km.inertia_)
            
        plt.figure(figsize=(8, 5))
        plt.plot(k_range, inertias, 'bo-')
        plt.xlabel('Number of clusters (k)')
        plt.ylabel('Inertia')
        plt.title('Elbow Plot for KMeans Clustering')
        plt.grid(True)
        plt.savefig(output_path)
        plt.close()
        logger.info(f"Saved elbow plot to {output_path}")
        
    def save_labels(self, output_path='output/cluster_labels.csv'):
        """Save cluster labels to CSV"""
        Path(output_path).parent.mkdir(exist_ok=True)
        output = self.df[['company_id', 'cluster_id', 'cluster_name', 'distance_from_centroid']]
        output.to_csv(output_path, index=False)
        logger.info(f"Saved cluster labels to {output_path}")
        
    def run(self):
        """Main execution"""
        try:
            self.connect()
            self.load_data()
            self.impute_missing()
            self.scale_features()
            self.fit_kmeans(n_clusters=5)
            self.assign_cluster_names()
            self.generate_elbow_plot()
            self.save_labels()
            logger.info("✓ Clustering completed successfully")
        finally:
            self.disconnect()


def main():
    engine = ClusterEngine()
    engine.run()


if __name__ == '__main__':
    main()
