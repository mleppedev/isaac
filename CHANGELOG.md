# Changelog

## [1.0.0] - 2025-03-16

### Added
- Web interface for data visualization with multiple views:
  - Raw data view: displays extracted game data in card format
  - Processed data view: shows data tables and visualizations
  - Statistics view: presents key metrics about collected data
- Interactive data processing directly from the web interface
- Ability to process data and train models through the web UI
- Visual graphs for health over time and enemy distribution
- Menu navigation between different visualization sections

### Changed
- Updated requirements.txt to use Python 3.12 compatible dependencies
- Modified go.cmd script to properly install dependencies in virtual environment
- Enhanced server to handle visualization and data processing requests
- Improved documentation with details about the visualization interface

### Fixed
- Dependency installation issues with Python 3.12
- Compatibility problems with numpy, pandas and matplotlib
- Environment setup to ensure dependencies are installed in virtual environment

## [0.1.0] - 2025-03-15

### Added
- Initial project setup
- Basic mod for The Binding of Isaac to extract gameplay data
- Server to receive and store extracted data
- Data processing and model training scripts
- Environment variable handling for sensitive information 