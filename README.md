# DLP Custom Software

PyQt6 desktop controller for DLP projection workflows using the Total Phase Cheetah SPI adapter.

## Project Layout

- `main_ui.py` - main GUI entry point.
- `main.py` - DLP command layer and SPI command helpers.
- `engineering.py` - engineering-mode window and parameter table tools.
- `cheetah_py.py`, `cheetah.dll` - Total Phase Cheetah Python binding and Windows DLL.
- `test (2).ui`, `EngineeringWindow (3).ui` - active Qt Designer UI files.
- `ShortAxisFlip.png`, `LongAxisFlip.png` - UI image assets.
- `customers/` - customer-specific visual style files.
- `docs/` - manuals and reference documents.
- `data/` - sample or exported data files.

## Setup

```powershell
pip install -r requirements.txt
```

Run the app:

```powershell
python main_ui.py
```

Run with a customer style:

```powershell
python main_ui.py --customer sample_customer
```

Or use an environment variable:

```powershell
$env:DLP_CUSTOMER="sample_customer"
python main_ui.py
```

## Customer Styles

Each customer style lives in:

```text
customers/<customer_name>/style.qss
```

To create a new customer version, copy `customers/default/` to a new folder and edit `style.qss`.

## Build

```powershell
pyinstaller DLP_Controller.spec
```

Build outputs are generated in `build/` and `dist/`. These folders are ignored by Git and should be uploaded as release assets only when needed.
