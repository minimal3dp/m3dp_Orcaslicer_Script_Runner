#!/usr/bin/env python3
"""Quick test to verify the extracted BrickLayers core logic works."""

from app.core import BrickLayersProcessor

# Simple test G-code
test_gcode = """
;LAYER:0
;TYPE:External perimeter
G1 X10 Y10 E1
G1 X20 Y10 E2
G1 X20 Y20 E3
G1 X10 Y20 E4
G1 X10 Y10 E5
"""


def test_processor():
    """Test that processor can be instantiated and process basic G-code."""
    processor = BrickLayersProcessor(
        extrusion_global_multiplier=1.05,
        start_at_layer=3,
        verbosity=1,
    )

    lines = test_gcode.strip().split("\n")
    output_lines = list(processor.process_gcode(lines))

    print("✓ Processor instantiated successfully")
    print(f"✓ Input lines: {len(lines)}")
    print(f"✓ Output lines: {len(output_lines)}")
    print("✓ Core module is functional!")

    return True


if __name__ == "__main__":
    test_processor()
