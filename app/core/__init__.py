"""
BrickLayers Core Module

This module contains the core processing logic extracted from the original
BrickLayers script, providing a clean API for web integration while maintaining
backward compatibility with the CLI interface.

The core classes and functions can be used independently of the CLI,
making them suitable for web applications, APIs, and other integrations.
"""

from app.core.bricklayers_core import (
    BrickLayersProcessor,
    GCodeFeature,
    GCodeFeatureState,
    GCodeLine,
    GCodeSimulator,
    GCodeState,
    ObjectEntry,
    Point,
    __version__,
)

__all__ = [
    "BrickLayersProcessor",
    "GCodeFeature",
    "GCodeFeatureState",
    "GCodeLine",
    "GCodeSimulator",
    "GCodeState",
    "ObjectEntry",
    "Point",
    "__version__",
]
