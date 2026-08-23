"""Functions for setting themes in the GUI"""
from PyQt5.QtGui import QPalette, QColor, QIcon, QPixmap, QPainter
from PyQt5.QtCore import QByteArray, Qt, QSize
from PyQt5.QtSvg import QSvgRenderer



def light_theme_palette() -> QPalette:
    """Create a light theme palette"""
    theme_dict = {
        'Window': (239, 239, 239), 
        'WindowText': (0, 0, 0), 
        'Base': (255, 255, 255), 
        'Text': (0, 0, 0), 
        'AlternateBase': (247, 247, 247), 
        'Button': (239, 239, 239), 
        'ButtonText':(0, 0, 0), 
        'BrightText': (255, 255, 255),
        'Light': (255, 255, 255), 
        'Midlight': (202, 202, 202), 
        'Dark': (159, 159, 159), 
        'Mid': (184, 184, 184), 
        'Shadow': (118, 118, 118), 
        'Highlight': (48, 140, 198), 
        'HighlightedText': (255, 255, 255), 
        'Link': (0, 0, 255), 
        'LinkVisited': (255, 0, 255), 
        'ToolTipBase': (255, 255, 220), 
        'ToolTipText': (0, 0, 0), 
        'PlaceholderText': (0, 0, 0),
        'NoRole': (0, 0, 0)
    }
    palette = QPalette()
    for key, attr in get_palette_attr().items():
        palette.setColor(attr, QColor(*theme_dict[key]))
    return palette


def dark_theme_palette() -> QPalette:
    """Create a dark theme palette"""
    theme_dict = {
        'Window': (32, 33, 36), 
        'WindowText': (224, 224, 224), 
        'Base': (32, 33, 36), 
        'Text': (224, 224, 224), 
        'AlternateBase': (41, 43, 46), 
        'Button': (32, 33, 36), 
        'ButtonText': (224, 224, 224), 
        'BrightText': (255, 255, 255),
        'Light': (63, 64, 66), 
        'Midlight': (63, 64, 66), 
        'Dark': (224, 224, 224), 
        'Mid': (63, 64, 66), 
        'Shadow': (63, 64, 66), 
        'Highlight': (138, 180, 247), 
        'HighlightedText': (32, 33, 36), 
        'Link': (100, 180, 255), 
        'LinkVisited': (197, 138, 248), 
        'ToolTipBase': (32, 33, 36), 
        'ToolTipText': (224, 224, 224), 
        'PlaceholderText': (150, 150, 150),
        'NoRole': (0, 0, 0)
    }
    palette = QPalette()
    for key, attr in get_palette_attr().items():
        palette.setColor(attr, QColor(*theme_dict[key]))
    return palette
    
    
def get_palette_attr(reversed: bool = False) -> dict:
    """Get a dict of QPalette attributes"""
    palette_dict = {
        'Window': QPalette.Window,
        'WindowText': QPalette.WindowText,
        'Base': QPalette.Base,
        'Text': QPalette.Text,
        'AlternateBase': QPalette.AlternateBase,
        'Button': QPalette.Button,
        'ButtonText': QPalette.ButtonText,
        'BrightText': QPalette.BrightText,
        'Light': QPalette.Light,
        'Midlight': QPalette.Midlight,
        'Dark': QPalette.Dark,
        'Mid': QPalette.Mid,
        'Shadow': QPalette.Shadow,
        'Highlight': QPalette.Highlight,
        'HighlightedText': QPalette.HighlightedText,
        'Link': QPalette.Link,
        'LinkVisited': QPalette.LinkVisited,
        'ToolTipBase': QPalette.ToolTipBase,
        'ToolTipText': QPalette.ToolTipText,
        'NoRole': QPalette.NoRole,
    }
    if hasattr(QPalette, 'PlaceholderText'):  # Only in Qt > 5.12
        palette_dict['PlaceholderText'] = QPalette.PlaceholderText
    if reversed:
        return {val: key for key, val in palette_dict.items()}
    return palette_dict


def get_palette_colors(palette: QPalette) -> dict:
    """Get the palette colors as a dict with RGB values"""
    rgb_dict = {}
    for key, attr in get_palette_attr().items():
        rgb_dict[key] = palette.color(attr).getRgb()[:-1]
    return rgb_dict


def color_icon(svg_path: str, theme: str, size: QSize) -> QIcon:
    """Color the svg icon base on the theme"""
    if theme == 'dark':
        icon_color = '#E0E0E0'
    else: 
        icon_color = '#000000'
    # Changing svg color
    with open(svg_path, 'r', encoding='utf-8') as file:
        svg = file.read()
    if 'fill=' in svg:  # Looking for fill="color"
        i1 = svg.find('fill=') + 6  # Index of first "
        i2 = svg[i1:].find('"') + i1  # Index of second "
        svg = svg[:i1] + icon_color + svg[i2:]  # Replace colors
    if 'stroke=' in svg:
        i1 = svg.find('stroke=') + 8
        i2 = svg[i1:].find('"') + i1  # Index of second "
        svg = svg[:i1] + icon_color + svg[i2:]  # Replace colors
    if 'fill=' not in svg and 'stroke=' not in svg:  # TODO check with different svg's
        svg = svg.replace('<svg', f'<svg stroke="{icon_color}"')
    # Creating icon
    renderer = QSvgRenderer(QByteArray(svg.encode('utf-8')))
    pixmap = QPixmap(size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


def code_editor_colors(theme: str) -> dict:
    """Get the code editor colors"""
    if theme == 'light':
        colors = {
            'line_numbers': {
                'background': '#e8e8e8',
                'text': '#717171',
                'bold_text': '#000000'
            },
            'syntax_highlight': {
                'keyword': 'blue',
                'algorithm_functions': 'darkBlue',
                'operator': 'red',
                'brace': 'blue',
                'defclass': 'black',
                'string': 'magenta',
                'string2': 'darkMagenta',
                'comment': 'darkGreen',
                'self': 'black',
                'numbers': 'brown'
            }
        }
    elif theme == 'dark':
        colors = {
            'line_numbers': {
                'background': '#292B2E',
                'text': '#717171',
                'bold_text': '#E0E0E0'
            },
            'syntax_highlight': {
                'keyword': '#C586C0',
                'algorithm_functions': "#C0C077FF",
                'operator': '#D4D4D4',
                'brace': '#D4D4D4',
                'defclass': '#DCDCAA',
                'string': '#CE9178',
                'string2': '#CE9178',
                'comment': '#6A9955',
                'self': '#9CDCFE',
                'numbers': '#B5CEA8',
            }
        }
    return colors
    