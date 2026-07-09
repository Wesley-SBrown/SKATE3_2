# Changelog

All notable changes of *SKATE3* will be documented in this file. The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), with the addition of author(s), date of change and optionally the relevant issue.

Add new entries at the top of the current list under the appropriate version subheading. Item format:

- Description. [Name; date; relevant github issue tag(s) and or pull requests]

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

### Added

### Changed

### Fixed

## [Unreleased]

## [1.0.1] - 3-12-2026

### Changed

- Updated deprecated scipy library imports and added missing project `__version__` attribute. [Wesley Brown; 1-17-2026; #3]

## [1.0.0] - 7-2-2025

### Added

- Added full Sphinx documentation pipeline configuration. [ljhwang; 6-17-2025; #1]
- Introduced explicit project metadata placeholder structures. [ljhwang; 6-27-2025]
- Created baseline environment.yaml specification file for project setup. [Brian Kim; 6-27-2025]

## [0.2.0] - 2-26-2025

### Added

- Added an alternative "dev" parameter toggle to `set_seismo_status.sh` to allow manual development database testing. [Benny Lichtner; 2-26-2025]
- Native AWS profile routing configurations added across all primary tool scripts. [Benny Lichtner; 7-22-2022]

### Changed

- Streamlined project environment dependency rules. [Benny Lichtner; 7-16-2022]

### Fixed

- Patched data type handling crash where native `range()` steps expected integers but received floats. [Benny Lichtner; 6-19-2022]

## [0.1.0] - 11-18-2015

### Added

- Initial creation of the seismogram pipeline processing architecture, including automated queue management scripts. [bennlich; 11-18-2015]
- Added complete geographic features framework, exporting region mapping parameters to integer-mapped GeoJSON format. [Marius Nita; 7-1-2015; commit cf01c36]
- Introduced full image filtering matrices including automated Otsu thresholding operations, morphological filters, and Gaussian pyramids. [bennlich; 6-23-2015; commit a40d8f4]
- Added core Hough Lines detection algorithms alongside Region of Interest (ROI) boundaries processors. [bennlich; 4-28-2015]
