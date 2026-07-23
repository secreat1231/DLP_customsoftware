import argparse
import os
import sys


DEFAULT_CUSTOMER = "default"


def get_customer_name(argv=None):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--customer", default=os.getenv("DLP_CUSTOMER", DEFAULT_CUSTOMER))
    args, remaining = parser.parse_known_args(argv if argv is not None else sys.argv[1:])

    sys.argv = [sys.argv[0], *remaining]
    return args.customer


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def apply_customer_style(app, customer_name):
    style_path = resource_path(os.path.join("customers", customer_name, "style.qss"))

    if not os.path.exists(style_path):
        style_path = resource_path(os.path.join("customers", DEFAULT_CUSTOMER, "style.qss"))

    if os.path.exists(style_path):
        with open(style_path, "r", encoding="utf-8") as style_file:
            app.setStyleSheet(style_file.read())
