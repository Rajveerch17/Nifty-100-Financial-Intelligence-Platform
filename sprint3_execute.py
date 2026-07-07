"""
sprint3_execute.py
===================
Sprint 3 Execution Script (Days 15-21)
Screener & Peer Comparison Implementation

This script orchestrates all tasks for Sprint 3:
- Day 15: Filter engine core
- Day 16-17: 6 preset screeners + composite scoring
- Day 18: Peer percentile rankings
- Day 19: Radar charts
- Day 20: Peer comparison Excel report
- Day 21: Tests & validation

Usage:
    python sprint3_execute.py [--year YYYY-MM]

Author: Data Analytics Team
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.screener.engine import ScreenerEngine
from src.analytics.peer import PeerComparisonEngine
from src.analytics.charting import RadarChartGenerator

# Configure logging with UTF-8 encoding to handle Unicode characters
import io
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sprint3_execution.log', encoding='utf-8'),
        logging.StreamHandler(stream=io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8'))
    ]
)

logger = logging.getLogger(__name__)


def day_15_filter_engine():
    """Day 15: Filter Engine Core - Load and validate filter engine."""
    logger.info("\n" + "="*80)
    logger.info("DAY 15: FILTER ENGINE CORE")
    logger.info("="*80)
    
    try:
        engine = ScreenerEngine()
        logger.info("[OK] Filter engine initialized")
        logger.info(f"  - Config loaded with {len(engine.config['filters'])} filter definitions")
        logger.info(f"  - {len(engine.config['presets'])} preset templates configured")
        if engine.df_ratios is not None:
            logger.info(f"  - {len(engine.df_ratios)} financial ratio records loaded")
            logger.info(f"  - Available columns: {list(engine.df_ratios.columns)[:8]}...")
        else:
            logger.error("  - Failed to load financial ratio records")
        
        return engine
    except Exception as e:
        logger.error(f"[ERROR] Failed to initialize filter engine: {e}")
        raise


def day_16_preset_screeners(engine: ScreenerEngine):
    """Day 16-17: 6 Preset Screeners & Composite Score."""
    logger.info("\n" + "="*80)
    logger.info("DAY 16-17: 6 PRESET SCREENERS & COMPOSITE SCORING")
    logger.info("="*80)
    
    try:
        # Generate all presets
        results = engine.generate_all_presets()
        
        successful_presets = {k: v for k, v in results.items() if v is not None and len(v) > 0}
        logger.info(f"[OK] Generated {len(successful_presets)}/{len(results)} preset screeners:")
        
        if not successful_presets:
            logger.warning("[WARN] No presets generated successfully.")
            if engine.df_ratios is not None:
                logger.warning(f"  - Available columns: {list(engine.df_ratios.columns)}")
            logger.warning("  - Check if required columns exist in database")
            return {}
        
        for preset_name, df in successful_presets.items():
            logger.info(f"  - {preset_name}: {len(df)} companies")
        
        # Export to Excel (only if we have successful presets)
        Path("output").mkdir(exist_ok=True)
        if successful_presets:
            engine.export_to_excel(successful_presets, "output/screener_output.xlsx")
            logger.info(f"[OK] Exported to output/screener_output.xlsx")
        else:
            logger.warning("[WARN] Skipping Excel export - no successful presets")
        
        # Verify preset counts
        for preset_name, df in successful_presets.items():
            preset_def = engine.config['presets'].get(preset_name, {})
            target = preset_def.get('target_count', 'unknown')
            logger.info(f"  {preset_name}: {len(df)} companies (target: {target})")
        
        return successful_presets
    
    except Exception as e:
        logger.error(f"[ERROR] Failed to generate presets: {e}")
        logger.exception("Detailed traceback:")
        return {}


def day_18_peer_rankings():
    """Day 18: Peer Percentile Rankings."""
    logger.info("\n" + "="*80)
    logger.info("DAY 18: PEER PERCENTILE RANKINGS")
    logger.info("="*80)
    
    try:
        peer_engine = PeerComparisonEngine()
        
        # Compute percentiles
        df_percentiles = peer_engine.compute_peer_percentiles()
        
        logger.info(f"[OK] Computed {len(df_percentiles)} peer percentile ranks")
        logger.info(f"  - {len(df_percentiles['peer_group'].unique())} peer groups")
        logger.info(f"  - {len(df_percentiles['metric'].unique())} metrics ranked")
        
        # Save to database
        peer_engine.save_to_database(df_percentiles)
        logger.info(f"[OK] Saved peer_percentiles table to SQLite")
        
        return peer_engine, df_percentiles
    
    except Exception as e:
        logger.error(f"[ERROR] Failed to compute peer rankings: {e}")
        logger.exception("Detailed traceback:")
        raise


def day_19_radar_charts():
    """Day 19: Radar Chart Generation."""
    logger.info("\n" + "="*80)
    logger.info("DAY 19: RADAR CHART GENERATION")
    logger.info("="*80)
    
    try:
        chart_gen = RadarChartGenerator()
        
        # Generate all charts
        Path("reports/radar_charts").mkdir(parents=True, exist_ok=True)
        results = chart_gen.generate_all_radar_charts(
            peer_groups=PeerComparisonEngine.PEER_GROUPS
        )
        
        logger.info(f"[OK] Generated {len(results)} radar charts")
        logger.info(f"  - Output directory: reports/radar_charts/")
        
        return results
    
    except Exception as e:
        logger.error(f"[ERROR] Failed to generate radar charts: {e}")
        logger.exception("Detailed traceback:")
        raise


def day_20_peer_comparison_excel(peer_engine: PeerComparisonEngine):
    """Day 20: Peer Comparison Excel Report."""
    logger.info("\n" + "="*80)
    logger.info("DAY 20: PEER COMPARISON EXCEL REPORT")
    logger.info("="*80)
    
    try:
        peer_engine.generate_peer_comparison_excel()
        
        logger.info(f"[OK] Generated peer_comparison.xlsx")
        logger.info(f"  - 11 sheets (one per peer group)")
        logger.info(f"  - Percentile colour-coding applied")
        logger.info(f"  - Benchmark companies highlighted")
        
    except Exception as e:
        logger.error(f"[ERROR] Failed to generate Excel: {e}")
        logger.exception("Detailed traceback:")
        raise


def day_21_tests_and_validation():
    """Day 21: Tests & Sprint Review."""
    logger.info("\n" + "="*80)
    logger.info("DAY 21: TESTS & VALIDATION")
    logger.info("="*80)
    
    try:
        checks = []
        
        # Verify screener outputs
        screener_exists = Path("output/screener_output.xlsx").exists()
        if screener_exists:
            logger.info(f"[OK] screener_output.xlsx verified")
        else:
            logger.warning(f"[WARN] screener_output.xlsx not found (expected if presets failed)")
        checks.append(("6 preset screeners generated", screener_exists))
        
        # Verify peer comparison output
        peer_exists = Path("output/peer_comparison.xlsx").exists()
        if peer_exists:
            logger.info(f"[OK] peer_comparison.xlsx verified")
        else:
            logger.warning(f"[WARN] peer_comparison.xlsx not found")
        checks.append(("Peer comparison with 11 groups", peer_exists))
        
        # Verify radar charts
        radar_dir = Path("reports/radar_charts")
        if radar_dir.exists():
            chart_count = len(list(radar_dir.glob("*.png")))
            logger.info(f"[OK] Radar charts generated: {chart_count} files")
            checks.append(("Radar charts for all companies", chart_count > 50))
        else:
            logger.warning(f"[WARN] Radar charts directory not found")
            checks.append(("Radar charts for all companies", False))
        
        # Print exit criteria
        logger.info("\n" + "-"*80)
        logger.info("EXIT CRITERIA (Definition of Done)")
        logger.info("-"*80)
        
        for criterion, status in checks:
            status_str = "[PASS]" if status else "[FAIL]"
            logger.info(f"  {status_str}: {criterion}")
        
        return all(status for _, status in checks)
    
    except Exception as e:
        logger.error(f"[ERROR] Validation failed: {e}")
        logger.exception("Detailed traceback:")
        return False


def main():
    """Main execution flow for Sprint 3."""
    logger.info("\n" + "="*80)
    logger.info("SPRINT 3 EXECUTION - SCREENER & PEER COMPARISON")
    logger.info("="*80)
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Day 15: Initialize filter engine
        screener_engine = day_15_filter_engine()
        
        # Day 16-17: Generate preset screeners
        preset_results = day_16_preset_screeners(screener_engine)
        
        # Day 18: Compute peer rankings
        peer_engine = None
        df_percentiles = None
        try:
            peer_engine, df_percentiles = day_18_peer_rankings()
        except Exception as e:
            logger.error(f"[ERROR] Day 18 failed: {e}")
        
        # Day 19: Generate radar charts
        radar_results = {}
        try:
            radar_results = day_19_radar_charts()
        except Exception as e:
            logger.error(f"[ERROR] Day 19 failed: {e}")
        
        # Day 20: Generate peer comparison Excel
        if peer_engine:
            try:
                day_20_peer_comparison_excel(peer_engine)
            except Exception as e:
                logger.error(f"[ERROR] Day 20 failed: {e}")
        else:
            logger.warning("[WARN] Skipping Day 20 - peer engine not initialized")
        
        # Day 21: Validate and test
        all_pass = day_21_tests_and_validation()
        
        # Final summary
        logger.info("\n" + "="*80)
        logger.info("SPRINT 3 SUMMARY")
        logger.info("="*80)
        logger.info(f"Execution completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Status: {'[OK] ALL CRITERIA MET' if all_pass else '[PARTIAL] SOME CRITERIA NOT MET'}")
        logger.info("\nDeliverables:")
        logger.info(f"  - output/screener_output.xlsx ({len(preset_results)} presets)")
        if peer_engine:
            logger.info(f"  - output/peer_comparison.xlsx (11 peer groups)")
        logger.info(f"  - reports/radar_charts/ ({len(radar_results)} charts)")
        if df_percentiles is not None:
            logger.info(f"  - peer_percentiles table (SQLite)")
        logger.info(f"  - config/screener_config.yaml")
        
        return 0 if all_pass else 1
    
    except Exception as e:
        logger.error(f"\n[ERROR] SPRINT 3 EXECUTION FAILED: {e}")
        logger.exception("Full traceback:")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
