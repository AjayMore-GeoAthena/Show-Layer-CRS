# CRS Layer Label — QGIS Plugin

Displays the **coordinate reference system** (e.g. `EPSG:4326`) as a coloured
badge next to every layer name in the **Layers panel**.

---

## Features

| What you get | Detail |
|---|---|
| **Instant CRS visibility** | See the projection of every layer at a glance |
| **Colour-coded badges** | 🔵 Blue = projected CRS · 🟢 Green = geographic CRS · ⚫ Grey = no CRS |
| **Toggle on/off** | Plugins ▸ CRS Layer Label ▸ Show CRS next to layer names |
| **Zero config** | Auto-enables on load; restores original delegate on unload |
| **QGIS 3.x compatible** | Uses only stable PyQGIS / PyQt5 APIs |

---

## Installation

### Option A — Manual (recommended for development)

1. Copy the `crs_layer_plugin/` folder to your QGIS plugins directory:

   | Platform | Path |
   |---|---|
   | **Windows** | `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\` |
   | **macOS** | `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/` |
   | **Linux** | `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/` |

2. Open QGIS → **Plugins ▸ Manage and Install Plugins…**
3. Switch to the **Installed** tab, find **CRS Layer Label**, and tick it.

### Option B — Install from ZIP

1. Zip the `crs_layer_plugin/` folder → `crs_layer_plugin.zip`
2. QGIS → **Plugins ▸ Manage and Install Plugins… ▸ Install from ZIP**
3. Browse to the zip and click **Install Plugin**.

---

## Usage

- The badge appears automatically when the plugin is enabled.
- **Toggle**: Plugins ▸ CRS Layer Label ▸ Show CRS next to layer names ✓
- The badge refreshes whenever layers are added/removed or a project is loaded.
- To change a layer's CRS: right-click the layer → **Layer CRS** or **Properties ▸ Source**.

---

## How It Works

The plugin installs a custom `QStyledItemDelegate` on QGIS's internal
`QgsLayerTreeView`. The delegate calls the base `paint()` first (so the
normal layer icon, name, and action buttons are unchanged), then overlays a
rounded-rectangle badge with the `authid()` of the layer's CRS.

On unload the original delegate is restored — no permanent changes to QGIS.

---

## File Structure

```
crs_layer_plugin/
├── __init__.py      # QGIS plugin factory
├── plugin.py        # CRSDelegate + CRSLayerLabelPlugin
├── metadata.txt     # Plugin metadata (name, version, author…)
├── icon.png         # (optional) 32×32 plugin icon
└── README.md        # This file
```

---

## Requirements

- QGIS **3.0** or newer
- Python **3.6+** (bundled with QGIS)
- No additional pip packages required

---

## Customisation

Open `plugin.py` and adjust the constants at the top of `CRSDelegate`:

```python
BADGE_BG     = QColor("#1a73e8")   # projected CRS badge colour
BADGE_BG_ALT = QColor("#34a853")   # geographic CRS badge colour
BADGE_RADIUS = 3                   # corner rounding (pixels)
BADGE_PADDING_H = 6                # horizontal padding inside badge
```

---

## License

MIT — do whatever you like, attribution appreciated.
