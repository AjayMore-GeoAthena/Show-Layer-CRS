"""
CRS Layer Label Plugin — Main Plugin Class (v1.5)
Author: GeoAthena

Strategy
────────
We store the original layer name in a custom node property
("_crs_label_original_name") and then call node.setName() to append the
CRS suffix directly.  QGIS renders the node name exactly as it renders any
other layer name — same font, same colour, same layout engine, same
indicator-button placement.  Nothing is painted on top; no delegate is
replaced; the attribute-table shortcut button is completely unaffected.

On disable / unload we restore every node's original name from the stored
property and clear the property.

Colour: plain default layer-tree text colour (no colouring of the suffix —
that would require a delegate and we are deliberately avoiding that).

Toggle: toolbar button + Plugins ▸ CRS Layer Label menu entry, in sync.
"""

from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui     import QIcon, QPixmap, QPainter
from qgis.PyQt.QtCore    import Qt, QByteArray
from qgis.PyQt.QtSvg     import QSvgRenderer
from qgis.core           import QgsProject, QgsLayerTree, QgsLayerTreeLayer
from qgis.gui            import QgsLayerTreeView

# Custom property key used to remember the original un-suffixed node name
_PROP_ORIG = "crs_label_original_name"


# ─── Inline SVG toolbar icon ─────────────────────────────────────────────────

_ICON_SVG = b"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
  <circle cx="12" cy="12" r="9.5" fill="none" stroke="#555" stroke-width="1.6"/>
  <ellipse cx="12" cy="12" rx="9.5" ry="4"   fill="none" stroke="#555" stroke-width="1"/>
  <ellipse cx="12" cy="12" rx="4"   ry="9.5" fill="none" stroke="#555" stroke-width="1"/>
  <line x1="2.5" y1="12" x2="21.5" y2="12"   stroke="#555" stroke-width="1"/>
  <circle cx="12" cy="12" r="2.4" fill="#555"/>
</svg>
"""


def _make_icon() -> QIcon:
    renderer = QSvgRenderer(QByteArray(_ICON_SVG))
    pixmap   = QPixmap(24, 24)
    pixmap.fill(Qt.transparent)
    p = QPainter(pixmap)
    renderer.render(p)
    p.end()
    return QIcon(pixmap)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _all_layer_nodes(root=None):
    """Yield every QgsLayerTreeLayer node in the tree, recursively."""
    if root is None:
        root = QgsProject.instance().layerTreeRoot()
    for child in root.children():
        if isinstance(child, QgsLayerTreeLayer):
            yield child
        elif QgsLayerTree.isGroup(child):
            yield from _all_layer_nodes(child)


def _crs_suffix(node: QgsLayerTreeLayer) -> str:
    """Return '  [EPSG:xxxx]' for the layer, or '' on any error."""
    try:
        layer = node.layer()
        if layer is None:
            return ""
        crs = layer.crs()
        if not crs.isValid():
            return "  [No CRS]"
        auth = crs.authid() or crs.description()[:16]
        return f"  [{auth}]"
    except Exception:
        return ""


def _apply_suffix(node: QgsLayerTreeLayer):
    """
    Append the CRS suffix to node.name(), storing the original first.
    Safe to call multiple times — checks the stored property to avoid
    double-appending.
    """
    try:
        current = node.name()
        # If we already stored the original, use that as the base
        original = node.customProperty(_PROP_ORIG)
        if original is None:
            # First time: save current name as original
            node.setCustomProperty(_PROP_ORIG, current)
            base = current
        else:
            base = original          # always suffix from the clean name

        suffix = _crs_suffix(node)
        node.setName(base + suffix if suffix else base)
    except Exception:
        pass


def _remove_suffix(node: QgsLayerTreeLayer):
    """Restore the original node name and clear the stored property."""
    try:
        original = node.customProperty(_PROP_ORIG)
        if original is not None:
            node.setName(original)
            node.removeCustomProperty(_PROP_ORIG)
    except Exception:
        pass


# ─── Plugin ──────────────────────────────────────────────────────────────────

class CRSLayerLabelPlugin:

    MENU_ENTRY   = "&CRS Layer Label"
    TOOLBAR_NAME = "CRS Layer Label"

    def __init__(self, iface):
        self.iface           = iface
        self._menu_action    = None
        self._toolbar        = None
        self._toolbar_action = None
        self._enabled        = False

    # ------------------------------------------------------------------
    # QGIS lifecycle
    # ------------------------------------------------------------------

    def initGui(self):
        icon = _make_icon()

        # ── Plugins menu entry ────────────────────────────────────────
        self._menu_action = QAction(icon, "Show CRS next to layer names",
                                    self.iface.mainWindow())
        self._menu_action.setCheckable(True)
        self._menu_action.setStatusTip(
            "Toggle CRS identifier next to each layer name in the Layers panel"
        )
        self._menu_action.triggered.connect(self._on_toggle)
        self.iface.addPluginToMenu(self.MENU_ENTRY, self._menu_action)

        # ── Toolbar ───────────────────────────────────────────────────
        self._toolbar = self.iface.mainWindow().addToolBar(self.TOOLBAR_NAME)
        self._toolbar.setObjectName("CRSLayerLabelToolBar")

        self._toolbar_action = QAction(icon, "Toggle CRS labels", self._toolbar)
        self._toolbar_action.setCheckable(True)
        self._toolbar_action.setToolTip(
            "<b>CRS Layer Label</b> — GeoAthena<br>"
            "Show / hide the CRS identifier next to each layer name."
        )
        self._toolbar_action.triggered.connect(self._on_toggle)
        self._toolbar.addAction(self._toolbar_action)

        # ── Project / layer signals ───────────────────────────────────
        proj = QgsProject.instance()
        proj.layersAdded.connect(self._on_layers_added)
        proj.layersRemoved.connect(self._refresh_all)
        proj.readProject.connect(self._refresh_all)

        self._set_enabled(True)

    def unload(self):
        # Always clean up node names before leaving
        self._set_enabled(False)

        try:
            proj = QgsProject.instance()
            proj.layersAdded.disconnect(self._on_layers_added)
            proj.layersRemoved.disconnect(self._refresh_all)
            proj.readProject.disconnect(self._refresh_all)
        except Exception:
            pass

        self.iface.removePluginMenu(self.MENU_ENTRY, self._menu_action)
        if self._menu_action:
            self._menu_action.deleteLater()
            self._menu_action = None
        if self._toolbar:
            self._toolbar.deleteLater()
            self._toolbar        = None
            self._toolbar_action = None

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _set_enabled(self, enable: bool):
        if enable:
            for node in _all_layer_nodes():
                _apply_suffix(node)
        else:
            for node in _all_layer_nodes():
                _remove_suffix(node)

        self._enabled = enable

        for action in (self._menu_action, self._toolbar_action):
            if action is not None:
                action.setChecked(enable)

    def _on_toggle(self, checked: bool):
        self._set_enabled(checked)
        # Keep both controls in sync without recursion
        for action in (self._menu_action, self._toolbar_action):
            if action is not None and action.isChecked() != checked:
                action.blockSignals(True)
                action.setChecked(checked)
                action.blockSignals(False)

    def _on_layers_added(self, layers):
        """Apply suffix to newly added layers only."""
        if not self._enabled:
            return
        root = QgsProject.instance().layerTreeRoot()
        for layer in layers:
            node = root.findLayer(layer.id())
            if node:
                _apply_suffix(node)

    def _refresh_all(self):
        """Re-apply suffixes to all nodes (e.g. after project load)."""
        if not self._enabled:
            return
        for node in _all_layer_nodes():
            _apply_suffix(node)
