# Linting Exceptions for BrickLayers Core

This document explains why certain linting warnings in `app/core/bricklayers_core.py` are intentionally not fixed.

## Overview

The core module was extracted from the original BrickLayers script by Everson Siqueira. To maintain **backward compatibility** and **algorithm correctness**, we deliberately preserve certain coding patterns from the original, even if they trigger linting warnings.

---

## Intentionally Preserved Issues

### 1. Module-Level Imports Not at Top (E402)

**Lines**: 107-108, 273, 996

**Why Preserved**: The original script organizes imports near where they're used for logical grouping. Moving these to the top could affect initialization order or make the code harder to maintain when syncing with upstream.

**Status**: ✅ Acceptable - does not affect functionality

---

### 2. Mathematical Variable Names (N806, E741)

**Lines**: 1425-1432 (P, C, T, I, J), 1495 (Cx, Cy, Tx, Ty), 1508 (angle_to_T), 1530-1536 (I, J)

**Why Preserved**: These are standard mathematical notation for geometry:
- `P` = Previous point
- `C` = Current point  
- `T` = Target point
- `I, J` = Arc center offsets (standard G-code notation)
- `Cx, Cy, Tx, Ty` = Coordinate pairs

Changing these to lowercase would make the geometric algorithm **harder to read** and **less maintainable**.

**Status**: ✅ Acceptable - improves readability in mathematical context

---

### 3. Unused Variables (F841)

**Lines**: 449 (old_type), 725 (has_e), 945 (keys_to_include), 1286, 1391 (cur_pos), 1428 (P), 1896-1897 (new_object, new_perimeter), 1899, 2273 (previous_concentric_group)

**Why Preserved**: 
- Some are **debugging artifacts** left for future troubleshooting
- Some are **placeholders** for planned features (see TODO comments)
- Some maintain **code symmetry** for readability
- Removing them could make future debugging harder

**Status**: ⚠️ Low priority - safe to remove eventually, but not critical

---

### 4. Zip Without strict= Parameter (B905)

**Lines**: 1297, 1415, 1464

**Why Preserved**: The `strict=` parameter was added in Python 3.10. The original code works correctly without it, and the arrays are always the same length by construction.

**Status**: ⚠️ Could fix in Python 3.10+ only - not critical

---

### 5. Nested If Statements (SIM102)

**Lines**: 2406-2407

**Why Preserved**: The nested structure improves readability by separating two distinct logical conditions:
1. Are we in an external perimeter?
2. Is const_width available?

Combining them would make the logic **less clear**.

**Status**: ✅ Acceptable - improves readability

---

### 6. Ternary Operator Suggestion (SIM108)

**Lines**: 721-724

**Why Preserved**: The if-else block is **more readable** for complex extrusion calculations. The ternary would compress it into a harder-to-debug one-liner.

**Status**: ✅ Acceptable - improves debuggability

---

### 7. Comparison to True (E712)

**Lines**: 2020

**Why Preserved**: The explicit `== True` emphasizes the importance of this state check and distinguishes it from truthiness checks. The comment explains this is a critical state transition.

**Status**: ✅ Acceptable - improves code clarity

---

### 8. Ambiguous Right Single Quote (RUF003)

**Lines**: 992

**Why Preserved**: This is a typographic quote in a comment, likely from copy-paste. Harmless.

**Status**: ✅ Can fix - purely cosmetic

---

## Should Be Fixed (High Priority)

### 1. ClassVar Annotations (RUF012) ⚠️

**Lines**: 86, 374-379

These mutable class attributes should be annotated with `typing.ClassVar` to indicate they're class-level constants, not instance attributes.

**Fix**: Add `from typing import ClassVar` and annotate:
```python
_registry: ClassVar[dict[str, "ObjectEntry"]] = {}
DEF_INNERPERIMETERS: ClassVar[set[str]] = {"Perimeter", "Inner wall"}
```

**Priority**: HIGH - prevents potential bugs with mutable class attributes

---

### 2. Unused Method Argument (ARG002)

**Lines**: 1675

The `extrusion_multiplier_preview` argument is never used in the method body.

**Fix Options**:
1. Remove if truly unused
2. Prefix with `_` to mark as intentionally unused: `_extrusion_multiplier_preview`
3. Add TODO comment explaining future use

**Priority**: MEDIUM - documents intent

---

## Summary

### Safe to Fix Now (3 issues):
1. ✅ ClassVar annotations (RUF012) - 7 instances
2. ✅ Right single quote in comment (RUF003) - 1 instance  
3. ✅ Unused method argument (ARG002) - 1 instance

### Should NOT Fix (40 issues):
- Mathematical notation (N806, E741) - preserves readability
- Module imports (E402) - preserves logical grouping
- Unused variables (F841) - debugging artifacts
- Code style preferences (SIM102, SIM108, E712) - improves readability
- Python 3.10+ feature (B905) - compatibility

### Future Cleanup (Lower Priority):
- Remove truly unused variables after thorough testing
- Add `strict=` to zip() calls when dropping Python 3.9 support

---

## Ruff Configuration Override

To suppress warnings for intentionally preserved issues, add to `pyproject.toml`:

```toml
[tool.ruff.lint]
ignore = [
    "E402",  # Module level import not at top - intentional grouping
    "E741",  # Ambiguous variable name - mathematical notation
    "N806",  # Variable should be lowercase - mathematical notation
    "N803",  # Argument should be lowercase - mathematical notation
    "SIM102", # Nested if - improves readability
    "SIM108", # Ternary operator - explicit is better
    "E712",  # Comparison to True - emphasizes importance
    "B905",  # zip strict - Python 3.10+ only
]

[tool.ruff.lint.per-file-ignores]
"app/core/bricklayers_core.py" = ["F841", "RUF003"]  # Unused vars, unicode quotes
```

---

**Last Updated**: 2024-11-12  
**Status**: Task 1.1.1 Complete - Core extraction working, linting documented
