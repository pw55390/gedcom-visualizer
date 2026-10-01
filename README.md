<p align="center">
  <img src="assets/logo.png" width="180">
</p>

<h1 align="center">
GEDCOM Visualizer
</h1>

<p align="center">
Modern Desktop Application for Genealogical Data Management
</p>

<p align="center">

![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![PySide6](https://img.shields.io/badge/PySide6-Qt6-41CD52?style=for-the-badge&logo=qt&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-blue?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-success?style=for-the-badge)

</p>

---

## Overview

**GEDCOM Visualizer** is a modern desktop application developed in **Python** for visualization, management and analysis of genealogical data stored in the **GEDCOM** format.

Unlike traditional genealogy software focused solely on data entry, GEDCOM Visualizer combines interactive graph visualization, advanced data exploration, reporting and high-performance desktop technologies into a single application.

The project has been designed with emphasis on:

- performance
- modular architecture
- intuitive user interface
- efficient handling of large genealogy databases
- clean and maintainable code

---

# Screenshots

## Main Window

<p align="center">
<img src="assets/screenshots/main_window.png" width="100%">
</p>

---

## Interactive Tree Visualization

<p align="center">
<img src="assets/screenshots/tree.png" width="100%">
</p>

---

## Statistics

<p align="center">
<img src="assets/screenshots/statistics.png" width="100%">
</p>

---

# Features

## GEDCOM Support

✔ Import GEDCOM

✔ Export GEDCOM

✔ GEDCOM validation

✔ Encoding detection

✔ Fast parser

---

## Genealogy Management

✔ Person management

✔ Family management

✔ Relationship editing

✔ Parent-child linking

✔ Marriage management

✔ Event editing

---

## Visualization

✔ Interactive family tree

✔ Dynamic relationship graph

✔ Zoom & Pan

✔ Layout optimization

✔ Graph navigation

---

## Search

✔ Instant search

✔ Advanced filtering

✔ Multi-field search

✔ Person lookup

---

## Reports

✔ PDF reports

✔ Printable family trees

✔ Statistical summaries

✔ Family reports

---

## Statistics

✔ Population statistics

✔ Gender distribution

✔ Family statistics

✔ Age statistics

✔ Relationship analysis

---

## Database

✔ SQLite backend

✔ Optimized queries

✔ Repository Pattern

✔ Data persistence

---

## User Interface

✔ Modern desktop interface

✔ Dockable panels

✔ Responsive layout

✔ Dark Theme

✔ Light Theme

✔ Status Bar

✔ Toolbar

✔ Keyboard shortcuts

---

# Architecture

The application follows a modular architecture inspired by enterprise desktop applications.

```
                     User Interface
                            │
          ┌─────────────────┴─────────────────┐
          │                                   │
      ViewModels                         Dialogs
          │
     Application Layer
          │
 Services ─────── Repositories
          │
     SQLite Database
          │
 GEDCOM Parser & Engine
          │
 Reports • Statistics • Visualization
```

---

# Technology Stack

## Programming Language

- Python 3.12+

---

## Desktop Framework

- PySide6 (Qt6)

---

## Database

- SQLite

---

## GIS Technologies

- QGIS

---

## Libraries

- ReportLab
- SQLite3
- Graph visualization libraries

---

# Project Structure

```
gedcom-visualizer/

│

├── application/

├── database/

├── gedcom/

├── gui/

├── reports/

├── visualization/

├── resources/

├── tests/

│

├── main.py

├── requirements.txt

└── README.md
```

---

# Installation

Clone repository

```bash
git clone https://github.com/pw55390/gedcom-visualizer.git
```

Open project

```bash
cd gedcom-visualizer
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run

```bash
python main.py
```

---

# Roadmap

## Version 1.1

- Improved graph rendering
- Better performance
- Enhanced search

---

## Version 1.2

- Plugin API
- GEDCOM 7 support
- SVG export

---

## Version 2.0

- Cloud synchronization

- Multi-user support

- Web companion

---

# Why this project?

This project was created as an opportunity to combine software engineering with genealogy and graph visualization.

Its primary goal is to provide a fast, modern and intuitive desktop environment for working with large genealogical databases while demonstrating clean software architecture and modern Python desktop development practices.

---

# Author

## Piotr Wolski

GIS Specialist

Geoinformatics Engineer

Computer Science Student

Python Developer

LinkedIn

https://www.linkedin.com/in/piotr-wolski-gis-wroclaw/

---

# License

MIT License

---

<p align="center">

Made with ❤️ using Python & Qt

</p>