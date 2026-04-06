"""
Custom in-app modal dialogs that replace QMessageBox.
These render inside the application window with dark-themed styling,
avoiding the Windows system alert sound and OS-native appearance.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QCursor


def _colors():
    from ui.theme import get_colors
    return get_colors("dark")


def _build_modal(parent, title, message, buttons, accent_type="info"):
    """
    Build and return a custom styled modal dialog.

    buttons: list of (label, role) where role is "accept", "reject", or "cancel"
    accent_type: "info", "warning", "error", "success", "question"
    Returns the QDialog instance (caller should exec or get result).
    """
    c = _colors()

    dialog = QDialog(parent, Qt.FramelessWindowHint)
    dialog.setModal(True)
    dialog.setAttribute(Qt.WA_TranslucentBackground)

    # Full overlay
    overlay = QWidget(dialog)
    overlay.setStyleSheet("background: rgba(0, 0, 0, 0.6);")

    # Modal box
    box = QWidget(overlay)

    # Accent color for left border
    if accent_type == "error":
        accent = c['danger']
    elif accent_type == "warning":
        accent = c['warning']
    elif accent_type == "success":
        accent = c['success']
    else:
        accent = c['accent']

    box.setStyleSheet(f"""
        QWidget {{
            background-color: #1e2433;
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 10px;
            border-left: 3px solid {accent};
        }}
    """)

    box_layout = QVBoxLayout(box)
    box_layout.setContentsMargins(24, 24, 24, 24)
    box_layout.setSpacing(12)

    # Header
    title_label = QLabel(title)
    title_label.setStyleSheet(f"""
        QLabel {{
            color: {c['text_primary']};
            font-size: 15px;
            font-weight: 700;
            background: transparent;
            border: none;
        }}
    """)
    box_layout.addWidget(title_label)

    # Body
    body_label = QLabel(message)
    body_label.setWordWrap(True)
    body_label.setStyleSheet(f"""
        QLabel {{
            color: #9ca3af;
            font-size: 13px;
            background: transparent;
            border: none;
            padding-right: 8px;
        }}
    """)
    box_layout.addWidget(body_label)

    # Buttons row
    btn_layout = QHBoxLayout()
    btn_layout.setSpacing(8)
    btn_layout.addStretch()

    dialog._result_role = None

    for label, role in buttons:
        btn = QPushButton(label)
        btn.setCursor(QCursor(Qt.PointingHandCursor))
        btn.setMinimumWidth(80)

        if role == "accept":
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {accent};
                    color: {c['text_inverse']};
                    border: none;
                    border-radius: 6px;
                    padding: 8px 20px;
                    font-size: 12px;
                    font-weight: 600;
                    min-height: 0px;
                }}
                QPushButton:hover {{
                    background-color: {c['accent_hover']};
                }}
            """)
            btn.clicked.connect(dialog.accept)
        elif role == "reject":
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {c['text_secondary']};
                    border: 1px solid {c['border']};
                    border-radius: 6px;
                    padding: 8px 20px;
                    font-size: 12px;
                    font-weight: 600;
                    min-height: 0px;
                }}
                QPushButton:hover {{
                    background-color: {c['bg_hover']};
                    color: {c['text_primary']};
                }}
            """)
            btn.clicked.connect(dialog.reject)
        elif role == "cancel":
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {c['text_secondary']};
                    border: 1px solid {c['border']};
                    border-radius: 6px;
                    padding: 8px 20px;
                    font-size: 12px;
                    font-weight: 600;
                    min-height: 0px;
                }}
                QPushButton:hover {{
                    background-color: {c['bg_hover']};
                    color: {c['text_primary']};
                }}
            """)
            # Use done(2) for cancel to distinguish from reject
            btn.clicked.connect(lambda: dialog.done(2))

        btn_layout.addWidget(btn)

    box_layout.addLayout(btn_layout)

    # Layout: overlay fills dialog, box centered in overlay
    def _resize():
        dialog.resize(parent.size() if parent else dialog.size())
        overlay.setGeometry(0, 0, dialog.width(), dialog.height())
        box_w = min(360, dialog.width() - 60)
        box.setFixedWidth(box_w)
        box.adjustSize()
        bx = (dialog.width() - box_w) // 2
        by = (dialog.height() - box.height()) // 2
        box.move(bx, by)

    dialog.resizeEvent = lambda e: _resize()

    # Position dialog over parent
    if parent:
        dialog.resize(parent.size())
        dialog.move(parent.mapToGlobal(parent.rect().topLeft()))
    else:
        dialog.resize(400, 200)

    _resize()
    return dialog


# ── Public API ─────────────────────────────────────────────────────────────

def show_info(parent, title, message):
    """Show an information modal (single OK button)."""
    dlg = _build_modal(parent, title, message,
                        [("OK", "accept")], accent_type="info")
    dlg.exec()


def show_success(parent, title, message):
    """Show a success modal (single OK button)."""
    dlg = _build_modal(parent, title, message,
                        [("OK", "accept")], accent_type="success")
    dlg.exec()


def show_warning(parent, title, message):
    """Show a warning modal (single OK button)."""
    dlg = _build_modal(parent, title, message,
                        [("OK", "accept")], accent_type="warning")
    dlg.exec()


def show_error(parent, title, message):
    """Show an error modal (single OK button)."""
    dlg = _build_modal(parent, title, message,
                        [("OK", "accept")], accent_type="error")
    dlg.exec()


def show_question(parent, title, message):
    """
    Show a Yes/No question modal.
    Returns True if user clicked Yes, False if No.
    """
    dlg = _build_modal(parent, title, message,
                        [("No", "reject"), ("Yes", "accept")],
                        accent_type="info")
    return dlg.exec() == QDialog.Accepted


def show_discard_confirm(parent, title, message):
    """
    Show a Discard/Cancel confirmation modal.
    Returns True if user clicked Discard, False if Cancel.
    Discard button has a warm/red tint; Cancel is accent filled.
    """
    c = _colors()

    dialog = QDialog(parent, Qt.FramelessWindowHint)
    dialog.setModal(True)
    dialog.setAttribute(Qt.WA_TranslucentBackground)

    overlay = QWidget(dialog)
    overlay.setStyleSheet("background: rgba(0, 0, 0, 0.6);")

    box = QWidget(overlay)
    box.setStyleSheet(f"""
        QWidget {{
            background-color: #1e2433;
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 10px;
            border-left: 3px solid {c['danger']};
        }}
    """)

    box_layout = QVBoxLayout(box)
    box_layout.setContentsMargins(24, 24, 24, 24)
    box_layout.setSpacing(12)

    title_label = QLabel(title)
    title_label.setStyleSheet(f"""
        QLabel {{
            color: {c['text_primary']};
            font-size: 15px;
            font-weight: 700;
            background: transparent;
            border: none;
        }}
    """)
    box_layout.addWidget(title_label)

    body_label = QLabel(message)
    body_label.setWordWrap(True)
    body_label.setStyleSheet(f"""
        QLabel {{
            color: #9ca3af;
            font-size: 13px;
            background: transparent;
            border: none;
            padding-right: 8px;
        }}
    """)
    box_layout.addWidget(body_label)

    btn_layout = QHBoxLayout()
    btn_layout.setSpacing(8)
    btn_layout.addStretch()

    # Discard button (outlined, warm/red tint)
    discard_btn = QPushButton("Discard")
    discard_btn.setCursor(QCursor(Qt.PointingHandCursor))
    discard_btn.setMinimumWidth(80)
    discard_btn.setStyleSheet(f"""
        QPushButton {{
            background-color: transparent;
            color: {c['danger']};
            border: 1px solid {c['danger']};
            border-radius: 6px;
            padding: 8px 20px;
            font-size: 12px;
            font-weight: 600;
            min-height: 0px;
        }}
        QPushButton:hover {{
            background-color: rgba(239,68,68,0.15);
        }}
    """)
    discard_btn.clicked.connect(dialog.accept)
    btn_layout.addWidget(discard_btn)

    # Cancel button (accent filled)
    cancel_btn = QPushButton("Cancel")
    cancel_btn.setCursor(QCursor(Qt.PointingHandCursor))
    cancel_btn.setMinimumWidth(80)
    cancel_btn.setStyleSheet(f"""
        QPushButton {{
            background-color: {c['accent']};
            color: {c['text_inverse']};
            border: none;
            border-radius: 6px;
            padding: 8px 20px;
            font-size: 12px;
            font-weight: 600;
            min-height: 0px;
        }}
        QPushButton:hover {{
            background-color: {c['accent_hover']};
        }}
    """)
    cancel_btn.clicked.connect(dialog.reject)
    btn_layout.addWidget(cancel_btn)

    box_layout.addLayout(btn_layout)

    def _resize():
        dialog.resize(parent.size() if parent else dialog.size())
        overlay.setGeometry(0, 0, dialog.width(), dialog.height())
        box_w = min(360, dialog.width() - 60)
        box.setFixedWidth(box_w)
        box.adjustSize()
        bx = (dialog.width() - box_w) // 2
        by = (dialog.height() - box.height()) // 2
        box.move(bx, by)

    dialog.resizeEvent = lambda e: _resize()

    if parent:
        dialog.resize(parent.size())
        dialog.move(parent.mapToGlobal(parent.rect().topLeft()))
    else:
        dialog.resize(400, 200)

    _resize()
    return dialog.exec() == QDialog.Accepted


def show_question_3way(parent, title, message):
    """
    Show a Yes/No/Cancel question modal.
    Returns "yes", "no", or "cancel".
    """
    dlg = _build_modal(parent, title, message,
                        [("Cancel", "cancel"), ("No", "reject"), ("Yes", "accept")],
                        accent_type="info")
    result = dlg.exec()
    if result == QDialog.Accepted:
        return "yes"
    elif result == 2:
        return "cancel"
    else:
        return "no"
