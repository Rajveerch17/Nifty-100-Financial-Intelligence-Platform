"""
Screener Module
===============
Multi-criteria stock screener with configurable filters and preset templates.

Features:
- 15 filterable metrics with operator support
- 6 pre-built screening templates
- Custom filter builder via YAML configuration
- Composite quality score (0-100) with sector-relative normalization
- Intelligent handling of sector carve-outs (banks/NBFCs)
- Debt-free company handling for ICR filter

Usage:
    from src.screener.engine import ScreenerEngine
    
    engine = ScreenerEngine(config_path="config/screener_config.yaml")
    results = engine.apply_preset("quality_compounder")
    results.to_excel("output/screener_output.xlsx")
"""

__version__ = "1.0.0"
__all__ = ["ScreenerEngine"]
