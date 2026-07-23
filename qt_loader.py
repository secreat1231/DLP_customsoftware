from PySide6.QtUiTools import loadUiType


def load_ui(ui_path, widget):
    form_class, _ = loadUiType(ui_path)
    form = form_class()
    form.setupUi(widget)

    for name, value in form.__dict__.items():
        if not name.startswith("_"):
            setattr(widget, name, value)

    return widget
