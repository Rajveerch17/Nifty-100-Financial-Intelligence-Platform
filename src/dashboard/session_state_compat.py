"""Compatibility layer for st.session_state across Streamlit versions.

This module provides backward-compatible wrappers for session state operations
that may differ between Streamlit versions.
"""

from __future__ import annotations
import streamlit as st
from typing import Any, Optional


def get_state(key: str, default: Any = None) -> Any:
    """Get a value from session state with backward compatibility."""
    return st.session_state.get(key, default)


def set_state(key: str, value: Any) -> None:
    """Set a value in session state."""
    st.session_state[key] = value


def is_initialized(key: str) -> bool:
    """Check if a session state key has been initialized."""
    return key in st.session_state


def init_state(key: str, default: Any) -> None:
    """Initialize a session state key if it doesn't exist."""
    if key not in st.session_state:
        st.session_state[key] = default
