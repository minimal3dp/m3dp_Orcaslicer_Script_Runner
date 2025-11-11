"""
BrickLayers Core Processing Engine - Public API

This module provides a clean, web-friendly API for the BrickLayers G-code
post-processing algorithm. It can be used independently of the CLI interface.

Example usage:
    ```python
    from app.core import BrickLayersProcessor

    # Create processor with desired settings
    processor = BrickLayersProcessor(
        extrusion_global_multiplier=1.05,
        start_at_layer=3,
        verbosity=0
    )

    # Process G-code from a file or stream
    with open('input.gcode', 'r') as infile:
        gcode_stream = (line for line in infile)
        processed_gcode = processor.process_gcode(gcode_stream)

        # Write output
        with open('output.gcode', 'w') as outfile:
            for line in processed_gcode:
                outfile.write(line)
    ```

Classes exported:
    - BrickLayersProcessor: Main processing engine
    - GCodeFeature: Feature detection and tracking
    - GCodeSimulator: G-code state simulation
    - GCodeLine: G-code line wrapper with state
    - GCodeState: Immutable state snapshot
    - GCodeFeatureState: Immutable feature state snapshot
    - Point: 2D point for geometric calculations
    - ObjectEntry: Object tracking for multi-object prints

Version: v0.2.1-10-g6409588 (from original BrickLayers script)
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
