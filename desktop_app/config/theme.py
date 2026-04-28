from __future__ import annotations


LIGHT_THEME = """
QWidget { background: #eef3f8; color: #172033; font-family: "Segoe UI"; font-size: 10pt; }
QMainWindow { background: #eef3f8; }
QLabel { background: transparent; }
QLabel#brandLogo { padding: 0; margin: 0; }
QFrame[card="true"] { background: #ffffff; border: 1px solid #d9e3f0; border-radius: 20px; }
QWidget[sidebar="true"] { background: #10233b; border: none; }
QLabel[muted="true"] { color: #60738c; }
QLabel[title="true"] { font-size: 22pt; font-weight: 700; color: #11284a; }
QLabel[sectionTitle="true"] { font-size: 13pt; font-weight: 600; }
QLabel[badge="true"] { border-radius: 12px; padding: 8px 14px; font-weight: 600; }
QLabel[badgeKind="success"] { background: #e8f7ec; color: #1f7a44; }
QLabel[badgeKind="warning"] { background: #fff4de; color: #8c5c00; }
QLabel[badgeKind="danger"] { background: #fdeaea; color: #a53d2d; }
QLabel[alert="true"] { border-radius: 14px; padding: 14px 16px; border: 1px solid transparent; }
QLabel[alertKind="info"] { background: #eaf2ff; color: #2957aa; }
QLabel[alertKind="error"] { background: #fdeaea; color: #a53d2d; border-color: #f3c9c2; }
QLabel[alertKind="success"] { background: #e8f7ec; color: #1f7a44; }
QPushButton { background: #f5f8fc; color: #172033; border: 1px solid #cfdae8; border-radius: 14px; padding: 12px 18px; font-weight: 600; }
QPushButton:hover { background: #eaf0f8; border-color: #bfd0e6; }
QPushButton[primary="true"] { background: #255dff; color: white; border: 1px solid #255dff; }
QPushButton[primary="true"]:hover { background: #1d4fdd; border-color: #1d4fdd; }
QPushButton:disabled { background: #eef2f7; color: #9aa8b8; border-color: #e0e7ef; }
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox { background: white; border: 1px solid #cfdae8; border-radius: 14px; padding: 12px; selection-background-color: #255dff; }
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QSpinBox:focus { border-color: #7ba3ff; }
QListWidget { background: transparent; border: none; outline: 0; }
QListWidget::item { border-radius: 14px; padding: 12px 14px; color: #d7e2f0; margin: 4px 0; }
QListWidget::item:selected { background: #29476f; color: white; border: none; outline: 0; }
QListWidget::item:focus { outline: 0; border: none; }
QProgressBar { border: 1px solid #d3dcea; border-radius: 10px; background: #edf2f9; text-align: center; min-height: 12px; }
QProgressBar::chunk { border-radius: 7px; background: #2f6bff; }
QTableWidget { background: white; border: 1px solid #d9e3f0; border-radius: 16px; gridline-color: #e7eef6; selection-background-color: #e8f0ff; alternate-background-color: #f8fbff; }
QHeaderView::section { background: #f4f8fd; color: #4e647d; border: none; border-bottom: 1px solid #d9e3f0; padding: 12px; font-weight: 600; }
QTableCornerButton::section { background: #f4f8fd; border: none; }
QCheckBox { background: transparent; spacing: 10px; }
QCheckBox::indicator { width: 18px; height: 18px; border-radius: 6px; border: 1px solid #b9c8d9; background: white; }
QCheckBox::indicator:checked { background: #2f6bff; border-color: #2f6bff; }
QScrollArea { border: none; background: transparent; }
"""
