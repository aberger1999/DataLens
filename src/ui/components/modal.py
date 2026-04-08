"""
Custom in-app modal dialogs that replace QMessageBox.
These render inside the application window with dark-themed styling,
avoiding the Windows system alert sound and OS-native appearance.
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QLineEdit
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QCursor


def _colors():
    from ui.theme import get_colors, current_theme
    return get_colors(current_theme())


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
            background-color: {c['bg_input']};
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
            color: {c['text_secondary']};
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
            background-color: {c['bg_input']};
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
            color: {c['text_secondary']};
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


def show_import_duplicate(parent, filename):
    """
    Show a 3-option modal when a duplicate file is being imported.
    Returns "import_again", "create_copy", or "cancel".
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
            background-color: {c['bg_input']};
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 10px;
            border-left: 3px solid {c['warning']};
        }}
    """)

    box_layout = QVBoxLayout(box)
    box_layout.setContentsMargins(24, 24, 24, 24)
    box_layout.setSpacing(12)

    title_label = QLabel("Duplicate File")
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

    body_label = QLabel(
        f"'{filename}' has already been imported. Import again as a "
        "new original, or create a new working copy of the existing import?"
    )
    body_label.setWordWrap(True)
    body_label.setStyleSheet(f"""
        QLabel {{
            color: {c['text_secondary']};
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

    _result = {"value": "cancel"}

    # Cancel
    cancel_btn = QPushButton("Cancel")
    cancel_btn.setCursor(QCursor(Qt.PointingHandCursor))
    cancel_btn.setMinimumWidth(80)
    cancel_btn.setStyleSheet(f"""
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
    cancel_btn.clicked.connect(dialog.reject)
    btn_layout.addWidget(cancel_btn)

    # Create Copy
    copy_btn = QPushButton("Create Copy")
    copy_btn.setCursor(QCursor(Qt.PointingHandCursor))
    copy_btn.setMinimumWidth(80)
    copy_btn.setStyleSheet(f"""
        QPushButton {{
            background-color: transparent;
            color: {c['text_primary']};
            border: 1px solid {c['border_medium']};
            border-radius: 6px;
            padding: 8px 20px;
            font-size: 12px;
            font-weight: 600;
            min-height: 0px;
        }}
        QPushButton:hover {{
            background-color: {c['bg_hover']};
        }}
    """)
    def _on_copy():
        _result["value"] = "create_copy"
        dialog.accept()
    copy_btn.clicked.connect(_on_copy)
    btn_layout.addWidget(copy_btn)

    # Import Again
    import_btn = QPushButton("Import Again")
    import_btn.setCursor(QCursor(Qt.PointingHandCursor))
    import_btn.setMinimumWidth(80)
    import_btn.setStyleSheet(f"""
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
    def _on_import():
        _result["value"] = "import_again"
        dialog.accept()
    import_btn.clicked.connect(_on_import)
    btn_layout.addWidget(import_btn)

    box_layout.addLayout(btn_layout)

    def _resize():
        dialog.resize(parent.size() if parent else dialog.size())
        overlay.setGeometry(0, 0, dialog.width(), dialog.height())
        box_w = min(420, dialog.width() - 60)
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
    dialog.exec()
    return _result["value"]


def show_load_original_warning(parent):
    """
    Show a warning when user tries to load an original dataset directly.
    Returns "load_original", "create_copy", or "cancel".
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
            background-color: {c['bg_input']};
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 10px;
            border-left: 3px solid {c['warning']};
        }}
    """)

    box_layout = QVBoxLayout(box)
    box_layout.setContentsMargins(24, 24, 24, 24)
    box_layout.setSpacing(12)

    title_label = QLabel("Load Original Dataset")
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

    body_label = QLabel(
        "Loading the original dataset means any changes will modify "
        "the source file. We recommend working on a copy instead."
    )
    body_label.setWordWrap(True)
    body_label.setStyleSheet(f"""
        QLabel {{
            color: {c['text_secondary']};
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

    _result = {"value": "cancel"}

    cancel_btn = QPushButton("Cancel")
    cancel_btn.setCursor(QCursor(Qt.PointingHandCursor))
    cancel_btn.setMinimumWidth(80)
    cancel_btn.setStyleSheet(f"""
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
    cancel_btn.clicked.connect(dialog.reject)
    btn_layout.addWidget(cancel_btn)

    copy_btn = QPushButton("Create Copy Instead")
    copy_btn.setCursor(QCursor(Qt.PointingHandCursor))
    copy_btn.setMinimumWidth(80)
    copy_btn.setStyleSheet(f"""
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
    def _on_copy():
        _result["value"] = "create_copy"
        dialog.accept()
    copy_btn.clicked.connect(_on_copy)
    btn_layout.addWidget(copy_btn)

    load_btn = QPushButton("Load Original Anyway")
    load_btn.setCursor(QCursor(Qt.PointingHandCursor))
    load_btn.setMinimumWidth(80)
    load_btn.setStyleSheet(f"""
        QPushButton {{
            background-color: transparent;
            color: {c['warning']};
            border: 1px solid {c['warning']};
            border-radius: 6px;
            padding: 8px 20px;
            font-size: 12px;
            font-weight: 600;
            min-height: 0px;
        }}
        QPushButton:hover {{
            background-color: rgba(245,158,11,0.15);
        }}
    """)
    def _on_load():
        _result["value"] = "load_original"
        dialog.accept()
    load_btn.clicked.connect(_on_load)
    btn_layout.addWidget(load_btn)

    box_layout.addLayout(btn_layout)

    def _resize():
        dialog.resize(parent.size() if parent else dialog.size())
        overlay.setGeometry(0, 0, dialog.width(), dialog.height())
        box_w = min(420, dialog.width() - 60)
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
    dialog.exec()
    return _result["value"]


def show_delete_original_confirm(parent, filename, copy_count):
    """
    Show a confirmation modal for deleting an original + all its copies.
    Returns True if user confirmed, False otherwise.
    """
    msg = (
        f"Are you sure you want to delete '{filename}'? "
        f"This will also delete all {copy_count} working "
        f"cop{'y' if copy_count == 1 else 'ies'} associated with it. "
        "This cannot be undone."
    )
    c = _colors()
    dlg = _build_modal(
        parent, "Delete Original Dataset", msg,
        [("Cancel", "reject"), ("Delete Everything", "accept")],
        accent_type="error",
    )
    # Re-style the accept button to red
    for child in dlg.findChildren(QPushButton):
        if child.text() == "Delete Everything":
            child.setStyleSheet(f"""
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
    return dlg.exec() == QDialog.Accepted


def show_reset_workspace(parent):
    """
    Two-step confirmation for resetting a workspace.
    Returns True only if user completes both steps.
    """
    c = _colors()

    # ── Step 1 ────────────────────────────────────────────────────────
    step1 = _build_modal(
        parent, "Reset Workspace",
        "This will permanently delete ALL datasets (originals and copies) "
        "from this workspace and clear all dataset history. The workspace "
        "itself and your saved graphs/reports will not be deleted.",
        [("Cancel", "reject"), ("Continue", "accept")],
        accent_type="error",
    )
    if step1.exec() != QDialog.Accepted:
        return False

    # ── Step 2 (custom — has a text input) ────────────────────────────
    dialog = QDialog(parent, Qt.FramelessWindowHint)
    dialog.setModal(True)
    dialog.setAttribute(Qt.WA_TranslucentBackground)

    overlay = QWidget(dialog)
    overlay.setStyleSheet("background: rgba(0, 0, 0, 0.6);")

    box = QWidget(overlay)
    box.setStyleSheet(f"""
        QWidget {{
            background-color: {c['bg_input']};
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 10px;
            border-left: 3px solid {c['danger']};
        }}
    """)

    box_layout = QVBoxLayout(box)
    box_layout.setContentsMargins(24, 24, 24, 24)
    box_layout.setSpacing(12)

    title_label = QLabel("Are you absolutely sure?")
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

    body_label = QLabel('Type RESET to confirm. This cannot be undone.')
    body_label.setWordWrap(True)
    body_label.setStyleSheet("""
        QLabel {
            color: {c['text_secondary']};
            font-size: 13px;
            background: transparent;
            border: none;
            padding-right: 8px;
        }
    """)
    box_layout.addWidget(body_label)

    text_input = QLineEdit()
    text_input.setPlaceholderText("Type RESET here")
    text_input.setStyleSheet(f"""
        QLineEdit {{
            background-color: {c['bg_primary']};
            color: {c['text_primary']};
            border: 1px solid {c['border_medium']};
            border-radius: 6px;
            padding: 8px 12px;
            font-size: 13px;
        }}
        QLineEdit:focus {{
            border-color: {c['danger']};
        }}
    """)
    box_layout.addWidget(text_input)

    btn_layout = QHBoxLayout()
    btn_layout.setSpacing(8)
    btn_layout.addStretch()

    cancel_btn = QPushButton("Cancel")
    cancel_btn.setCursor(QCursor(Qt.PointingHandCursor))
    cancel_btn.setMinimumWidth(80)
    cancel_btn.setStyleSheet(f"""
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
    cancel_btn.clicked.connect(dialog.reject)
    btn_layout.addWidget(cancel_btn)

    confirm_btn = QPushButton("Confirm Reset")
    confirm_btn.setCursor(QCursor(Qt.PointingHandCursor))
    confirm_btn.setMinimumWidth(80)
    confirm_btn.setEnabled(False)
    confirm_btn.setStyleSheet(f"""
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
        QPushButton:disabled {{
            color: {c['text_disabled']};
            border-color: {c['border_subtle']};
        }}
    """)
    confirm_btn.clicked.connect(dialog.accept)
    btn_layout.addWidget(confirm_btn)

    def _on_text_changed(text):
        confirm_btn.setEnabled(text.strip() == "RESET")
    text_input.textChanged.connect(_on_text_changed)

    box_layout.addLayout(btn_layout)

    def _resize():
        dialog.resize(parent.size() if parent else dialog.size())
        overlay.setGeometry(0, 0, dialog.width(), dialog.height())
        box_w = min(400, dialog.width() - 60)
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
        dialog.resize(400, 300)

    _resize()
    return dialog.exec() == QDialog.Accepted
