"""
CRS Layer Label Plugin
Displays the coordinate reference system next to each layer name in the Layers panel.
"""


def classFactory(iface):
    from .plugin import CRSLayerLabelPlugin
    return CRSLayerLabelPlugin(iface)
