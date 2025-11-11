

# **An Expert Compendium of OrcaSlicer Pre- and Post-Processing Scripts**

## **A Technical Primer on OrcaSlicer Scripting Mechanisms**

OrcaSlicer, a fork of Bambu Studio, inherits a powerful yet nuanced scripting capability from its Slic3r and PrusaSlicer lineage.1 Understanding the precise mechanism of this feature is critical for its successful implementation. This system allows for the execution of external programs to modify G-code *after* slicing, enabling a vast range of custom optimizations, integrations, and automated tasks.

### **Dissection of the Post-Processing Mechanism**

The core principle of OrcaSlicer's post-processing is the execution of an external program *after* the slicer has generated the G-code file.2 The primary technical constraint is that the script must modify the G-code file *in-place*.

When a script is triggered, OrcaSlicer passes the absolute path of the newly created G-code file as the final argument to the script.3 The external program is then responsible for reading this file, performing its modifications, and saving the changes back to the original file.3 An alternative method is for the script to output a new G-code to a temporary file and then use that file to overwrite the original.3

This mechanism is language-agnostic. The operating system simply needs to be able to execute the specified command. This allows for scripts written in any language, with common examples being Python (.py) 2, Perl (.pl) 5, and pre-compiled executables (.exe).7

### **Configuration Syntax and Execution**

Post-processing scripts are configured within OrcaSlicer in the print settings profile:  
Print Settings $\\rightarrow$ Others $\\rightarrow$ Post-processing Scripts.1  
The syntax is a standard command-line call.

* **For interpreted scripts (e.g., Python):** The path to the interpreter must be provided, followed by the path to the script.  
  * "C:\\Your\\Path\\To\\Python\\python.exe" "C:\\Your\\Path\\To\\Script\\pythonScript.py" 2  
* **For compiled executables (e.g.,.exe):** Only the path to the executable is required.  
  * "C:\\Path\\Where\\You\\Put\\thumbnail.exe"; 7

A common user-reported pitfall is failing to handle paths that contain spaces. The correct syntax requires enclosing any path with spaces in double-quotes (").10 Some user examples omit these 11, which can lead to execution failures.

It is also important to note that these scripts are executed upon G-code *export*. Some user reports indicate that relying on the script to run during the "Preview" stage may not function as expected or, in some cases, may cause the slicer to crash.12

### **Harnessing Slicer Data: The SLIC3R\_ Environment Variables**

The primary "API" for post-processing scripts is a set of environment variables. OrcaSlicer, following the Slic3r convention, passes all of its configuration options to the script's execution environment.3

Every variable is prefixed with SLIC3R\_. For example, the configured layer height is made available to the script as the SLIC3R\_LAYER\_HEIGHT environment variable.3 A script can read these variables to make its modifications conditional. For instance, a script could apply a function only if SLIC3R\_LAYER\_HEIGHT is less than a certain value.

A simple shell script can be used as an essential debugging tool to dump all available variables from any given OrcaSlicer version 3:

Bash

\#\!/bin/sh  
env | grep ^SLIC3R\_

By temporarily adding this as a post-processing script and exporting a G-code file, a user can inspect the console output to see all available variables and their exact names. This is critical because, while the *mechanism* is similar to PrusaSlicer, the *variable names themselves* may have diverged.13 A script written for PrusaSlicer may fail in OrcaSlicer simply because it is calling a variable that OrcaSlicer has renamed.

### **Critical Distinction: The Three "Scripting" Modalities**

Analysis of the user query and community discussions reveals that the term "scripting" is used to describe three distinct modalities of automation. Clarifying these is essential to finding the correct solution.

1. **Modality 1: Post-Processing Scripts (Host-Side):** This is the official "Post-processing Scripts" feature detailed above. The script is an external program (e.g., ArcWelder.exe, Fuzzyficator.py) that runs on the *computer* after slicing to modify the G-code *before* it is sent to the printer.  
2. **Modality 2: Start G-Code Macros (Firmware-Side):** This is the most common method for "pre-print" automation and directly addresses the "pre-processing" part of the query. These are not external scripts, but rather G-code macros (e.g., CLEAN\_NOZZLE for Klipper) stored *on the printer's firmware*.14 OrcaSlicer's role is to *call* these macros from its "Machine start G-code" field, using placeholders (e.g., \[nozzle\_temperature\_initial\_layer\]) 14 to pass settings from the slicer to the firmware.  
3. **Modality 3: G-Code Triggers (Host-Intercept):** This is a hybrid method where the slicer injects a special G-code command (e.g., @OCTOLAPSE TAKE-SNAPSHOT 16 or G4 P1 17) into the G-code file. This command is then *intercepted* by a connected host service, such as OctoPrint, which pauses the print and performs an action (like taking a photo) before resuming.

## **Category 1: Pre-Slicing Environment Scripts (Utility)**

While the user's query for "pre-processing" largely refers to pre-print automation (Modality 2), one true pre-slicing (Modality 1\) utility was identified.

### **Profile Conversion: Migrating from PrusaSlicer & SuperSlicer**

The PrusaSlicer ecosystem has historically been built on .ini configuration files. OrcaSlicer, via Bambu Studio, uses a .json format, creating a significant barrier to entry for users who have invested years in tuning their .ini profiles. This "ecosystem friction" is a major pain point for migration.

A Perl-based utility script has been developed to solve this specific problem.

* **Script:** SuperSlicer\_to\_Orca\_scripts 5  
* **Function:** This is a command-line utility designed to read PrusaSlicer and SuperSlicer .ini profile files (for printer, print, and filament settings) and convert them into the .json format required by OrcaSlicer.5  
* **Implementation:** This script is run from a terminal, not from within the slicer. The user provides an input pattern for the .ini files and an output directory for the converted .json files.5  
* **Link:** https://github.com/theophile/SuperSlicer\_to\_Orca\_scripts 5

## **Category 2: G-Code Optimization & Print Quality Scripts (Post-Processing)**

This category represents the most common use of the post-processing feature: modifying G-code toolpaths to improve print quality, speed, or strength.

### **Toolpath Optimization: ArcWelder**

ArcWelder is an executable (.exe) that parses a G-code file and converts sequences of small, co-planar linear G1 movements into G2 (clockwise arc) and G3 (counter-clockwise arc) commands.18

* **Benefits:**  
  1. **Print Quality:** Drastically improves quality on curved surfaces by reducing the command density. This prevents "stuttering," which can occur when a printer's controller (especially 8-bit or overwhelmed 32-bit boards) cannot process the high volume of tiny G1 commands quickly enough.18  
  2. **File Size:** User reports indicate file size reductions of \~60%.19  
  3. **Print Time:** The reduction in command overhead can lead to significant print time savings. One user reported a reduction of "an hour off of a 12.45 hour print".19  
* Implementation:  
  OrcaSlicer includes a native "Arc Fitting" feature.19 However, direct user comparisons indicate this native implementation is critically flawed. Users report that native "Arc Fitting" produces worse quality (e.g., "look more like octagons") and fails to provide the time or file size reductions of the external script.19 In contrast, the external ArcWelder.exe script provides "significant improvements" in all three categories.19  
  Therefore, it is strongly recommended to *disable* OrcaSlicer's native "Arc Fitting" feature and *exclusively* use the external ArcWelder.exe post-processing script.  
  1. **Download:** The correct download is the standalone console application, *not* the OctoPrint or Cura plugins. This is available from the ArcWelderLib repository releases page.11  
  2. **Syntax:** Add the path to the executable in the post-processing field, for example: "C:\\Path\\To\\ArcWelder.exe" \-g ;.8  
* **Link:** https://github.com/FormerLurker/ArcWelderLib/releases 11

### **Advanced Print Modification: The TengerTechnologies (TenTech) Suite**

A suite of innovative Python scripts from developer TengerTechnologies (TenTech) enables advanced features not yet available in core slicers. These scripts function as a form of rapid prototyping for the open-source community, allowing users to access experimental features long before they can be integrated into the slicer's core C++ engine.22

All scripts are Python-based and use the standard interpreter syntax: "C:\\Path\\To\\Python.exe" "C:\\Path\\To\\Script.py".4

* **Smoothificator (Python Script)**  
  * **Function:** Enables differential layer heights. The script modifies the G-code to print *outer walls* at a low layer height (e.g., 0.1mm for high quality) while printing *infill and inner walls* at a much larger layer height (e.g., 0.3mm for high speed).25 This provides the quality of a fine print in a fraction of the time. It has also been updated to work with OrcaSlicer's native adaptive layer height feature.28  
  * **Link:** https://github.com/TengerTechnologies/Smoothificator 26  
* **Fuzzyficator (Python Script)**  
  * **Function:** Extends the slicer's "Fuzzy Skin" feature (which is normally limited to vertical walls) to *non-planar* (3D) top and bottom surfaces.4 The script automatically reads the slicer's existing fuzzy skin settings and applies them by algorithmically adding small Z-axis deviations to the top-most and bottom-most toolpaths.4  
  * **Link:** https://github.com/TengerTechnologies/Fuzzyficator 4  
* **Bricklayers (Python Script)**  
  * **Function:** A script designed to improve the strength of 3D prints by algorithmically staggering the layer start/end points and toolpaths, simulating the interlocking pattern of a brick wall.25  
  * **Link:** https://github.com/TengerTechnologies/Bricklayers 31  
* **Other Scripts:** The same developer also provides NonPlanarInfill, NonPlanarIroning, and SupportInterfaceIroning in their repository.29

### **Multi-Material & Infill Management (Perl)**

This represents one of the most advanced forms of scripting, creating a "handshake" between the slicer and the printer's firmware.

* **Script:** purge\_to\_infill.pl 6  
* **Function:** A highly advanced Perl script for Klipper-based multi-material printers. It analyzes the G-code to find filament changes and re-sequences the print order. It moves "invisible" features (like infill or supports) to be printed *immediately after* the filament change.6  
* **Benefit:** The script calculates the exact filament volume of these invisible sections and passes this value as a parameter (e.g., MODEL\_PURGE) to a custom Klipper FILAMENT\_CHANGE macro. This allows the printer to purge the old color *into the model's infill* rather than onto a purge tower or into a waste bucket, drastically reducing filament waste.6  
* **Companion Script:** A gcode\_fixups.pl script is also provided to solve common Klipper compatibility issues, such as removing the \# from filament color codes (which Klipper interprets as a comment).6  
* **Link:** https://github.com/theophile/gcode-postprocessing-scripts 6

## **Category 3: Host, Firmware & Service Integration Scripts (Post-Processing)**

This category of scripts modifies G-code to improve compatibility with third-party hardware and software, such as Klipper, OctoPrint, and proprietary printer screens.

### **Thumbnail Management for Hosts (Klipper, OctoPrint)**

* **Script:** gcode\_thumbnail\_move 32  
* **Function:** This is a "quality of life" Python script that addresses a common annoyance for Klipper users. OrcaSlicer, by default, places the large, base64-encoded thumbnail data block at the *beginning* of the G-code file. This script moves that entire block to the *end* of the file.32  
* **Benefit:** This allows users to immediately inspect the starting G-code (e.g., START\_PRINT macros) in Klipper web interfaces like Mainsail or Fluidd without having to scroll past thousands of lines of thumbnail data.33 This may also resolve some conflicts with OctoPrint timelapse generation.33  
* **Link:** https://github.com/cron410/gcode\_thumbnail\_move 32

### **Thumbnail Generation for Specific Printers**

* **Script:** ElegooNeptuneThumbnailPrusaMod 7  
* **Function:** This is a post-processing executable that acts as a "translator" for thumbnails. OrcaSlicer generates standard PNG or JPG thumbnails.7 This script finds that data and *converts* it into the proprietary thumbnail format required by the touchscreens on Elegoo Neptune printers.7  
* **Implementation:** This script *requires* native G-code thumbnails to be enabled first within OrcaSlicer's settings (e.g., Printer Settings $\\rightarrow$ Basic information $\\rightarrow$ G-code thumbnails set to 300x300 and Format set to PNG).7 The script then runs, finds this data, and overwrites it.  
* **Link:** https://github.com/fifonik/ElegooNeptuneThumbnailPrusaMod 7

### **Automated Print Logging**

* **Script:** Slic3rPostProcessingUploader 34  
* **Function:** An executable script that integrates with the 3DPrintLog.com service. After slicing, it parses the G-code to extract metadata (filament usage, print time, settings). It then opens the user's default web browser with a pre-filled submission form to automatically log the details of the print.34  
* **Compatibility:** The script is explicitly compatible with OrcaSlicer, Bambu Studio, PrusaSlicer, and others.34  
* **Link:** https://github.com/ChristopherHoffman/Slic3rPostProcessingUploader 34

## **Category 4: Pre-Print Automation (Start G-Code Macros)**

This section directly addresses the user's "pre-processing" query by focusing on Modality 2 scripting. The solutions below are not post-processing scripts, but rather G-code macros and logic snippets inserted into the "Machine start G-code" section of OrcaSlicer's printer settings. They fulfill the "pre-print" automation goal.

### **Purge Line Customization**

By default, many slicer profiles include a generic purge line. This can be customized by directly editing the G-code in the Machine start G-code field.35 When migrating G-code from PrusaSlicer, it is essential to update Prusa's placeholders to OrcaSlicer's variable syntax.36

A more advanced, dynamic method is available:

* **Macro:** Adaptive Purge for any 3D printer 37  
* **Function:** This is a snippet of "firmware agnostic" G-code that is pasted directly into the slicer's start G-code.38 It is a recreation of Klipper's KAMP LINE\_PURGE macro but runs entirely on slicer variables. It uses placeholders (e.g., \[first\_layer\_print\_min\_x\]) to dynamically calculate a purge line location *immediately adjacent to the printed object*, saving time and bed space.37  
* **Link:** https://www.printables.com/model/1035759-adaptive-purge-for-any-3d-printer-using-slicer-var 37

### **Nozzle Cleaning Routines (Klipper)**

This implements a call to a physical nozzle-wiping brush or station before probing or printing. This is a Klipper-based solution that perfectly illustrates the Modality 2 "placeholder-to-macro" pipeline.14

* **Implementation:**  
  1. **Firmware-Side:** First, a macro (e.g., \[gcode\_macro CLEAN\_NOZZLE\]) must be added to the Klipper printer.cfg file. This macro contains the G-code to move the toolhead to the brush and perform the wipe.14  
  2. **Slicer-Side:** In OrcaSlicer's Machine start G-code field, the user *calls* this macro. The key is to use an OrcaSlicer placeholder to pass the correct temperature, making the macro filament-agnostic.  
* Example Call:  
  CLEAN\_NOZZLE EXTRUDER\_TEMP=\[nozzle\_temperature\_initial\_layer\] WIPES={10} 14  
  In this example, \[nozzle\_temperature\_initial\_layer\] is *not* G-code; it is an OrcaSlicer variable. When slicing, OrcaSlicer replaces this placeholder with the numerical value from the filament profile (e.g., "240"). The final G-code file sent to the printer contains the static line CLEAN\_NOZZLE EXTRUDER\_TEMP=240 WIPES={10}, which Klipper can then execute.

### **Timelapse Integration (Octolapse G-Code Triggers)**

This "Modality 3" scripting is used to configure stabilized timelapses with the OctoPrint plugin Octolapse.16 Octolapse *does not* use a post-processing script.16 Instead, it works by either automatically detecting slicer settings from G-code comments or by responding to a G-code trigger.

User reports indicate that OrcaSlicer's comment style can cause "Slicer Settings Missing" errors with Octolapse's automatic detection.40 Therefore, the G-Code Trigger method is more reliable.

* **Implementation:** In OrcaSlicer, navigate to Printer Settings $\\rightarrow$ Machine G-code $\\rightarrow$ After layer change G-code. In this box, insert a G-code command that Octolapse is configured to intercept.17  
* **Recommended Trigger Code:** G4 P1 (a 1ms pause) 17 or the custom @OCTOLAPSE TAKE-SNAPSHOT.16

## **Comprehensive Script Repository and Reference Table**

The following table summarizes the scripts and macros identified, their function, and their source.

**Table 1: OrcaSlicer Script & Macro Repository**

| Script / Macro Name | Primary Function | Type / Implementation | Language | Source / Link |
| :---- | :---- | :---- | :---- | :---- |
| **Pre-Slicing Utilities** |  |  |  |  |
| SuperSlicer\_to\_Orca\_scripts | Converts Prusa/SuperSlicer .ini profiles to OrcaSlicer .json | Pre-Slicing Utility (CLI) | Perl | github.com/theophile/SuperSlicer\_to\_Orca\_scripts 5 |
| **G-Code Optimization (Post-Process)** |  |  |  |  |
| ArcWelder | Converts linear G1 moves to G2/G3 arc commands. | Post-Processing Script | Executable | github.com/FormerLurker/ArcWelderLib/releases 11 |
| Smoothificator | Sets different layer heights for inner/outer walls. | Post-Processing Script | Python | github.com/TengerTechnologies/Smoothificator 26 |
| Fuzzyficator | Adds non-planar (3D) fuzzy skin to top/bottom surfaces. | Post-Processing Script | Python | github.com/TengerTechnologies/Fuzzyficator 4 |
| Bricklayers | Staggers layer lines to increase part strength. | Post-Processing Script | Python | github.com/TengerTechnologies/Bricklayers 31 |
| purge\_to\_infill.pl | Re-sequences G-code to purge multi-material prints into infill. | Post-Processing Script | Perl | github.com/theophile/gcode-postprocessing-scripts 6 |
| **Host/Firmware Integration (Post-Process)** |  |  |  |  |
| gcode\_thumbnail\_move | Moves G-code thumbnail data block to the end of the file. | Post-Processing Script | Python | github.com/cron410/gcode\_thumbnail\_move 32 |
| ElegooNeptuneThumbnailPrusaMod | Converts slicer thumbnails to Elegoo Neptune-compatible format. | Post-Processing Script | Executable | github.com/fifonik/ElegooNeptuneThumbnailPrusaMod 7 |
| Slic3rPostProcessingUploader | Uploads print metadata to 3DPrintLog.com. | Post-Processing Script | Executable | github.com/ChristopherHoffman/Slic3rPostProcessingUploader 34 |
| **Pre-Print Automation (Start G-Code)** |  |  |  |  |
| Adaptive Purge | Dynamically purges near the object based on slicer variables. | Start G-Code Macro | G-code | printables.com/model/1035759-adaptive-purge... 37 |
| CLEAN\_NOZZLE | Klipper macro call to run a nozzle-wiping routine. | Start G-Code Macro (Call) | G-code | (User printer.cfg \+ Slicer G-code) 14 |
| Octolapse Trigger | In-G-code command intercepted by OctoPrint for snapshots. | Layer-Change G-Code | G-code | @OCTOLAPSE TAKE-SNAPSHOT 16 |

## **Actionable Recommendations and Implementation Checklists**

Based on the analysis of available scripts and common implementation issues, the following recommendations are provided.

### **Expert Recommendations**

* **For ALL Users:**  
  * **Use the external ArcWelder script.** The analysis is definitive that the external executable 20 is superior in quality, speed, and file size reduction to OrcaSlicer's native "Arc Fitting" feature, which should be disabled.19  
* **For Klipper Users:**  
  * Implement the gcode\_thumbnail\_move script 32 as a standard "quality of life" improvement for inspecting G-code files.33  
  * Replace standard purge lines with the "Adaptive Purge" G-code macro 37 for greater efficiency.  
  * For nozzle-wiping routines, use the "placeholder-to-macro" (Modality 2\) method by calling a printer.cfg macro from the slicer's start G-code.14  
* **For Print Quality Enthusiasts:**  
  * The TenTech suite of Python scripts represents the cutting edge of slicer features. Smoothificator 26 is ideal for balancing speed and quality, while Fuzzyficator 4 enables unique, non-planar aesthetic finishes.  
* **For Multi-Material Klipper Users:**  
  * The purge\_to\_infill.pl script 6 is an essential tool for drastically reducing filament waste, though it requires advanced setup of both the Perl script and Klipper macros.

### **Implementation Checklist & Common Pitfalls**

Failure to correctly configure the scripting environment is the most common source of errors.

* **\[ \] 1\. Install the Interpreter:** Post-processing scripts are not run by OrcaSlicer, but by the operating system. Python (.py) scripts require a system-wide Python installation.4 Perl (.pl) scripts require a Perl installation.5  
* **\[ \] 2\. Use Absolute, Quoted Paths:** In the post-processing command box, use full, absolute paths for both the interpreter and the script. If *either* path contains spaces, enclose it in double-quotes.10  
  * **Correct:** "C:\\Program Files\\Python311\\python.exe" "D:\\My Scripts\\Fuzzyficator.py"  
  * **Incorrect:** C:\\Program Files\\Python311\\python.exe D:\\My Scripts\\Fuzzyficator.py  
* **\[ \] 3\. Set Permissions (Linux/macOS):** On non-Windows systems, scripts must be marked as executable. Run chmod \+x your\_script.py in a terminal.32  
* **\[ \] 4\. Verify Environment Variables:** If a script fails silently or behaves incorrectly, it is often due to a mismatch in environment variable names (e.g., a PrusaSlicer script used in OrcaSlicer).13 Use the env | grep ^SLIC3R\_ debug script 3 to dump all variables available in your version of OrcaSlicer and verify the names the script is trying to access.  
* **\[ \] 5\. Export, Don't Just Preview:** Post-processing scripts are designed to run during the final G-code *export* or "Save" operation. Do not rely on them to execute when only clicking "Slice" or viewing the "Preview" tab, as this may fail or cause instability.12

#### **Works cited**

1. Is there an easier way to have a post process script for orca slicer? : r/OrcaSlicer \- Reddit, accessed November 4, 2025, [https://www.reddit.com/r/OrcaSlicer/comments/1b0rkib/is\_there\_an\_easier\_way\_to\_have\_a\_post\_process/](https://www.reddit.com/r/OrcaSlicer/comments/1b0rkib/is_there_an_easier_way_to_have_a_post_process/)  
2. Post-Processing Scripts \- SoftFever/OrcaSlicer Wiki \- GitHub, accessed November 4, 2025, [https://github.com/SoftFever/OrcaSlicer/wiki/others\_settings\_post\_processing\_scripts](https://github.com/SoftFever/OrcaSlicer/wiki/others_settings_post_processing_scripts)  
3. Post-Processing Scripts \- Slic3r Manual, accessed November 4, 2025, [https://manual.slic3r.org/advanced/post-processing](https://manual.slic3r.org/advanced/post-processing)  
4. TengerTechnologies/Fuzzyficator: (Work In Progress) A Gcode postprocessing script to add non-planar "Fuzzyskin" to top flat surfaces. \- GitHub, accessed November 4, 2025, [https://github.com/TengerTechnologies/Fuzzyficator](https://github.com/TengerTechnologies/Fuzzyficator)  
5. theophile/SuperSlicer\_to\_Orca\_scripts: Script(s) to convert SuperSlicer data for use in Orca Slicer \- GitHub, accessed November 4, 2025, [https://github.com/theophile/SuperSlicer\_to\_Orca\_scripts](https://github.com/theophile/SuperSlicer_to_Orca_scripts)  
6. theophile/gcode-postprocessing-scripts: My personal ... \- GitHub, accessed November 4, 2025, [https://github.com/theophile/gcode-postprocessing-scripts](https://github.com/theophile/gcode-postprocessing-scripts)  
7. fifonik/ElegooNeptuneThumbnailPrusaMod: PrusaSlicer ... \- GitHub, accessed November 4, 2025, [https://github.com/fifonik/ElegooNeptuneThumbnailPrusaMod](https://github.com/fifonik/ElegooNeptuneThumbnailPrusaMod)  
8. ArcWelder PostProcess · supermerill SuperSlicer · Discussion \#946 \- GitHub, accessed November 4, 2025, [https://github.com/supermerill/SuperSlicer/discussions/946](https://github.com/supermerill/SuperSlicer/discussions/946)  
9. Home · SoftFever/OrcaSlicer Wiki \- GitHub, accessed November 4, 2025, [https://github.com/SoftFever/OrcaSlicer/wiki](https://github.com/SoftFever/OrcaSlicer/wiki)  
10. Post-processing scripts \- Bambu Lab Software, accessed November 4, 2025, [https://forum.bambulab.com/t/post-processing-scripts/25517](https://forum.bambulab.com/t/post-processing-scripts/25517)  
11. arc welder x orca slicer : r/OrcaSlicer \- Reddit, accessed November 4, 2025, [https://www.reddit.com/r/OrcaSlicer/comments/197aipc/arc\_welder\_x\_orca\_slicer/](https://www.reddit.com/r/OrcaSlicer/comments/197aipc/arc_welder_x_orca_slicer/)  
12. Post processing script results in corrupted gcode / crash when previewing model · Issue \#7433 · SoftFever/OrcaSlicer \- GitHub, accessed November 4, 2025, [https://github.com/SoftFever/OrcaSlicer/issues/7433](https://github.com/SoftFever/OrcaSlicer/issues/7433)  
13. Orca slicer can't properly use python post proccesing scripts · Issue \#2333 · SoftFever/OrcaSlicer \- GitHub, accessed November 4, 2025, [https://github.com/SoftFever/OrcaSlicer/issues/2333](https://github.com/SoftFever/OrcaSlicer/issues/2333)  
14. Installing nozzle whipper micro in klipper. \- Reddit, accessed November 4, 2025, [https://www.reddit.com/r/klippers/comments/1hx1987/installing\_nozzle\_whipper\_micro\_in\_klipper/](https://www.reddit.com/r/klippers/comments/1hx1987/installing_nozzle_whipper_micro_in_klipper/)  
15. Installing nozzle whipper micro in klipper. : r/ElegooNeptune4 \- Reddit, accessed November 4, 2025, [https://www.reddit.com/r/ElegooNeptune4/comments/1hwwpqr/installing\_nozzle\_whipper\_micro\_in\_klipper/](https://www.reddit.com/r/ElegooNeptune4/comments/1hwwpqr/installing_nozzle_whipper_micro_in_klipper/)  
16. Octolapse | Stabilized timelapses for Octoprint \- GitHub Pages, accessed November 4, 2025, [https://formerlurker.github.io/Octolapse/](https://formerlurker.github.io/Octolapse/)  
17. Complete Octolapse Guide \- Tips, tricks and troubleshooting for 3D printing timelapses, accessed November 4, 2025, [https://www.youtube.com/watch?v=CjOIxKxb3h8](https://www.youtube.com/watch?v=CjOIxKxb3h8)  
18. Arc Welder \- Ultimaker Cura Marketplace, accessed November 4, 2025, [https://marketplace.ultimaker.com/app/cura/plugins/fieldofview/ArcWelderPlugin](https://marketplace.ultimaker.com/app/cura/plugins/fieldofview/ArcWelderPlugin)  
19. Arc Fitting does not work as well as Arc Welder · Issue \#3521 ..., accessed November 4, 2025, [https://github.com/SoftFever/OrcaSlicer/issues/3521](https://github.com/SoftFever/OrcaSlicer/issues/3521)  
20. Releases · FormerLurker/ArcWelderLib \- GitHub, accessed November 4, 2025, [https://github.com/FormerLurker/ArcWelderLib/releases](https://github.com/FormerLurker/ArcWelderLib/releases)  
21. FormerLurker/ArcWelderLib: A collection of projects used to convert G0/G1 commands to G2/G3 commands. \- GitHub, accessed November 4, 2025, [https://github.com/FormerLurker/ArcWelderLib](https://github.com/FormerLurker/ArcWelderLib)  
22. Maker improves “fuzzy skin” function for the top layer with open source script \- 3Printr.com, accessed November 4, 2025, [https://www.3printr.com/maker-improves-fuzzy-skin-function-for-the-top-layer-with-open-source-script-3075068/](https://www.3printr.com/maker-improves-fuzzy-skin-function-for-the-top-layer-with-open-source-script-3075068/)  
23. Fuzzyficator is awesome : r/TenTech \- Reddit, accessed November 4, 2025, [https://www.reddit.com/r/TenTech/comments/1gagpvz/fuzzyficator\_is\_awesome/](https://www.reddit.com/r/TenTech/comments/1gagpvz/fuzzyficator_is_awesome/)  
24. How to install post processing script on Bambu slicer? : r/TenTech, accessed November 4, 2025, [https://www.reddit.com/r/TenTech/comments/1iosill/how\_to\_install\_post\_processing\_script\_on\_bambu/](https://www.reddit.com/r/TenTech/comments/1iosill/how_to_install_post_processing_script_on_bambu/)  
25. Tentech Gcode Post-processing scripts \- Bambu Lab Community Forum, accessed November 4, 2025, [https://forum.bambulab.com/t/tentech-gcode-post-processing-scripts/145131](https://forum.bambulab.com/t/tentech-gcode-post-processing-scripts/145131)  
26. TengerTechnologies/Smoothificator: A script that enables you to 3D print with different Layerheights on the inside and outside of your print \- GitHub, accessed November 4, 2025, [https://github.com/TengerTechnologies/Smoothificator](https://github.com/TengerTechnologies/Smoothificator)  
27. Different Layerheight for Walls in Prusaslicer and Orcaslicer now Opensource\! \- Reddit, accessed November 4, 2025, [https://www.reddit.com/r/3Dprinting/comments/1i9qbbw/different\_layerheight\_for\_walls\_in\_prusaslicer/](https://www.reddit.com/r/3Dprinting/comments/1i9qbbw/different_layerheight_for_walls_in_prusaslicer/)  
28. Adaptive Layerheight with constant surface finish\! Smoothificator update \- Reddit, accessed November 4, 2025, [https://www.reddit.com/r/3Dprinting/comments/1ilkvcb/adaptive\_layerheight\_with\_constant\_surface\_finish/](https://www.reddit.com/r/3Dprinting/comments/1ilkvcb/adaptive_layerheight_with_constant_surface_finish/)  
29. TengerTechnologies (TenTech) · GitHub, accessed November 4, 2025, [https://github.com/TengerTechnologies](https://github.com/TengerTechnologies)  
30. UPDATE\! \- Non-Planar Top Fuzzyskin \- 3D Printing Guide\! \- YouTube, accessed November 4, 2025, [https://www.youtube.com/watch?v=85FJl5P0AoU](https://www.youtube.com/watch?v=85FJl5P0AoU)  
31. Tinx: "TenTech implemented a post pro…" \- jit.social, accessed November 4, 2025, [https://jit.social/@tinx/113893549181878117](https://jit.social/@tinx/113893549181878117)  
32. cron410/gcode\_thumbnail\_move: This Orca Slicer post ... \- GitHub, accessed November 4, 2025, [https://github.com/cron410/gcode\_thumbnail\_move](https://github.com/cron410/gcode_thumbnail_move)  
33. Annoyed that Orca Slicer inserts Thumbnail data at the beginning of GCODE, so I wrote a post-processing script to move it to the end like SuperSlicer does. : r/klippers \- Reddit, accessed November 4, 2025, [https://www.reddit.com/r/klippers/comments/1afpbgz/annoyed\_that\_orca\_slicer\_inserts\_thumbnail\_data/](https://www.reddit.com/r/klippers/comments/1afpbgz/annoyed_that_orca_slicer_inserts_thumbnail_data/)  
34. ChristopherHoffman/Slic3rPostProcessingUploader: A ... \- GitHub, accessed November 4, 2025, [https://github.com/ChristopherHoffman/Slic3rPostProcessingUploader](https://github.com/ChristopherHoffman/Slic3rPostProcessingUploader)  
35. Changing purge line : r/OrcaSlicer \- Reddit, accessed November 4, 2025, [https://www.reddit.com/r/OrcaSlicer/comments/1jgt0pf/changing\_purge\_line/](https://www.reddit.com/r/OrcaSlicer/comments/1jgt0pf/changing_purge_line/)  
36. How to set purge line & preheat nozzle height in Elegoo or Orca Slicer \- Reddit, accessed November 4, 2025, [https://www.reddit.com/r/elegoo/comments/1jx4b3z/how\_to\_set\_purge\_line\_preheat\_nozzle\_height\_in/](https://www.reddit.com/r/elegoo/comments/1jx4b3z/how_to_set_purge_line_preheat_nozzle_height_in/)  
37. Klipper Adaptive Purge Tutorial: A Guide for Orcaslicer \- YouTube, accessed November 4, 2025, [https://www.youtube.com/watch?v=P3ztK\_15In0](https://www.youtube.com/watch?v=P3ztK_15In0)  
38. Adaptive purge for any 3D printer using slicer variables by ..., accessed November 4, 2025, [https://www.printables.com/model/1035759-adaptive-purge-for-any-3d-printer-using-slicer-var](https://www.printables.com/model/1035759-adaptive-purge-for-any-3d-printer-using-slicer-var)  
39. Octolapse \- Setup And Configuration for the Best Timelapses \- Obico, accessed November 4, 2025, [https://www.obico.io/blog/octolapse-setup-and-configuration/](https://www.obico.io/blog/octolapse-setup-and-configuration/)  
40. \[Request\] Allow compatability with Orcaslicer for automatic slicer configuration · Issue \#928 · FormerLurker/Octolapse \- GitHub, accessed November 4, 2025, [https://github.com/FormerLurker/Octolapse/issues/928](https://github.com/FormerLurker/Octolapse/issues/928)  
41. Unable to Print using Octolapse and OrcaSlicer : r/3Dprinting \- Reddit, accessed November 4, 2025, [https://www.reddit.com/r/3Dprinting/comments/1cg7ipu/unable\_to\_print\_using\_octolapse\_and\_orcaslicer/](https://www.reddit.com/r/3Dprinting/comments/1cg7ipu/unable_to_print_using_octolapse_and_orcaslicer/)
