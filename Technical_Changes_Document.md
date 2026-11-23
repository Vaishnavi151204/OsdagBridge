# OsdagBridge – Technical Changes Document

## Project Overview
The OsdagBridge report generator was enhanced to improve PDF formatting, table readability, layout consistency and design visualizations using Python and PyLaTeX.

## 1. Repeated Table Headers
- Improved multi-page table formatting using PyLaTeX LongTable.
- Added repeated header handling using `\endfirsthead` and `\endhead`.
- Improved readability when tables continue across pages.

## 2. Layout and Footer Improvements
- Improved table spacing and page layout.
- Adjusted vertical spacing and table formatting to reduce footer overlap.
- Improved page-break handling.

## 3. Load and Geometry Tables
- Separated vehicle live-load and footpath live-load information.
- Improved presentation of load parameters and their units.
- Vehicle selection is linked to the application's loading inputs.

## 4. Utilization Ratio Charts
- Added an overall design-check visualization for:
  - Steel Plate Girders
  - Concrete Deck Slab
  - Cross Bracing
  - End Diaphragms
- Included a red dashed reference line at UR = 1.0.
- Values above 1.0 indicate checks exceeding the utilization limit.

## 5. Material Quantity Charts
- Added structural steel quantity visualization.
- Added concrete volume versus reinforcement steel weight visualization.
- Generated chart images for embedding into the PDF report.

## 6. Centralized Formatting System
- Introduced `styles.py` as a centralized formatting configuration module.
- Consolidated shared formatting and visual styling.
- Reduced duplicated formatting definitions across report-generation modules.

## Architectural Rationale
The refactoring improves maintainability by centralizing styling, using appropriate multi-page table structures and separating report content into clearer sections. Charts make important structural design results and material quantities easier to interpret.

## Testing
The enhanced report was generated through the OsdagBridge desktop application after bridge design analysis. The resulting PDF should be compared with the original report to verify table formatting, page layout, load sections and visualizations.

## Submission
- GitHub: https://github.com/Vaishnavi151204/OsdagBridge
- Branch: feature/report-refactor
- Original report: Report_Before.pdf
- Enhanced report: Report_After.pdf
- Source code and chart assets: GitHub repository
