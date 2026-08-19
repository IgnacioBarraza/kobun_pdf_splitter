from kobun.shared.config.app_settings import THEME_ICONS_DIRECTORY
from kobun.shared.theme import AppTheme

# Radios en píxeles. Se nombran en vez de repetirse para que ajustar la
# redondez de toda la app sea cambiar un número.
RADIO_CHICO = 6
RADIO_MEDIO = 9
RADIO_GRANDE = 12
RADIO_ZONA = 14


class StyleGenerator:
    """
    Transforma un AppTheme en una cadena QSS (Qt Style Sheets).

    Todo el color de la aplicación sale de acá: los widgets no llevan estilos
    propios, así que alternar tema es reemplazar esta hoja y nada más.

    La forma también: se prefieren superficies y espacio a marcos. Sólo llevan
    borde los elementos donde el borde comunica algo —la zona de arrastre, que
    invita a soltar, y los campos editables— en lugar de encajonar cada bloque.
    """

    @staticmethod
    def chevron_url(theme: AppTheme) -> str:
        """
        Ruta del ícono de flecha para los desplegables.

        Qt no permite dibujar la flecha con estilos: `QComboBox::down-arrow`
        sólo acepta una imagen. Se usa un gris neutro por variante clara u
        oscura, que funciona con cualquier color de acento.

        Se emite en formato posix porque QSS espera barras normales incluso
        en Windows.
        """
        variant = "dark" if theme.is_dark else "light"

        return (THEME_ICONS_DIRECTORY / f"chevron_{variant}.svg").as_posix()

    @staticmethod
    def generate(theme: AppTheme) -> str:
        bg = theme.get_color("background")
        surface = theme.get_color("surface")
        surface_alt = theme.get_color("surface_alt", surface)
        primary = theme.get_color("primary")
        primary_hover = theme.get_color("primary_hover", primary)
        border = theme.get_color("border")
        border_strong = theme.get_color("border_strong", border)
        danger = theme.get_color("danger", "#b3261e")
        success = theme.get_color("success", "#3f7d58")

        text_primary = theme.get_text_color("primary")
        text_secondary = theme.get_text_color("secondary")
        text_inverse = theme.get_text_color("inverse")
        text_disabled = theme.get_text_color("disabled", text_secondary)
        chevron = StyleGenerator.chevron_url(theme)

        return f"""
        QWidget {{
            background-color: {bg};
            color: {text_primary};
            font-size: 13px;
        }}

        /* Sin esto los QLabel pintan el fondo general encima del panel que
           los contiene, y se ve un recuadro alrededor de cada texto. */
        QLabel {{
            background: transparent;
        }}

        QFrame#MainContainer {{
            background-color: {bg};
        }}

        QFrame#Sidebar {{
            background-color: {surface};
            border: none;
        }}

        QLabel#Logo {{
            font-size: 23px;
            font-weight: bold;
            color: {primary};
        }}

        QLabel#Title {{
            font-size: 20px;
            font-weight: bold;
        }}

        QLabel#SectionLabel {{
            color: {text_secondary};
            font-size: 11px;
            font-weight: bold;
        }}

        QLabel#SecondaryText {{
            color: {text_secondary};
            font-size: 11px;
        }}

        QLabel#ErrorText {{
            color: {danger};
        }}

        QLabel#SuccessText {{
            color: {success};
        }}

        /* Separador de un píxel: divide sin encajonar. */
        QFrame#Hairline {{
            background-color: {border};
            border: none;
            max-height: 1px;
        }}

        /* Botón primario */
        QPushButton#PrimaryButton {{
            background-color: {primary};
            color: {text_inverse};
            border: none;
            border-radius: {RADIO_GRANDE}px;
            padding: 12px 22px;
            font-weight: bold;
            font-size: 14px;
        }}

        QPushButton#PrimaryButton:hover {{
            background-color: {primary_hover};
        }}

        QPushButton#PrimaryButton:disabled {{
            background-color: {surface_alt};
            color: {text_disabled};
        }}

        /* Botones secundarios */
        QPushButton {{
            background-color: {surface};
            color: {text_primary};
            border: 1px solid {border};
            border-radius: {RADIO_MEDIO}px;
            padding: 9px 15px;
        }}

        QPushButton:hover {{
            border-color: {border_strong};
            background-color: {surface_alt};
        }}

        QPushButton:disabled {{
            color: {text_disabled};
            border-color: {border};
        }}

        /* Navegación: texto con barra de acento, no un botón encajonado. */
        QPushButton#NavButton {{
            background: transparent;
            border: none;
            border-left: 3px solid transparent;
            border-radius: 0;
            padding: 11px 12px;
            text-align: left;
            color: {text_secondary};
        }}

        QPushButton#NavButton:hover {{
            background-color: {surface_alt};
            color: {text_primary};
        }}

        QPushButton#NavButton:checked {{
            border-left-color: {primary};
            background-color: {surface_alt};
            color: {text_primary};
            font-weight: bold;
        }}

        /* Entradas */
        QLineEdit {{
            background-color: {surface_alt};
            border: 1px solid transparent;
            border-radius: {RADIO_MEDIO}px;
            padding: 10px 12px;
            color: {text_primary};
            selection-background-color: {primary};
            selection-color: {text_inverse};
        }}

        QLineEdit:hover {{
            border-color: {border};
        }}

        QLineEdit:focus {{
            border-color: {primary};
            background-color: {surface};
        }}

        QLineEdit:disabled {{
            color: {text_disabled};
            background-color: {surface};
        }}

        QComboBox {{
            background-color: {surface_alt};
            border: 1px solid transparent;
            border-radius: {RADIO_MEDIO}px;
            padding: 9px 12px;
            /* Fuerza la lista estilable en vez del popup nativo del sistema. */
            combobox-popup: 0;
        }}

        QComboBox:hover {{
            border-color: {border};
        }}

        QComboBox:focus, QComboBox:on {{
            border-color: {primary};
        }}

        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: center right;
            width: 30px;
            border: none;
            background: transparent;
        }}

        QComboBox::down-arrow {{
            image: url("{chevron}");
            width: 12px;
            height: 12px;
        }}

        QComboBox QAbstractItemView {{
            background-color: {surface};
            border: 1px solid {border};
            border-radius: {RADIO_MEDIO}px;
            padding: 5px;
            outline: none;
        }}

        /* Sin ::item las filas quedan apretadas y sin realce al pasar el mouse. */
        QComboBox QAbstractItemView::item {{
            min-height: 28px;
            padding: 5px 9px;
            border-radius: {RADIO_CHICO}px;
            color: {text_primary};
        }}

        QComboBox QAbstractItemView::item:hover {{
            background-color: {surface_alt};
        }}

        QComboBox QAbstractItemView::item:selected {{
            background-color: {primary};
            color: {text_inverse};
        }}

        /* Zona de arrastre: acá el borde sí comunica —invita a soltar—, así
           que se conserva punteado, sólo más suave y más redondeado. */
        QFrame#DropArea {{
            background-color: {surface};
            border: 2px dashed {border};
            border-radius: {RADIO_ZONA}px;
        }}

        QFrame#DropArea:hover {{
            border-color: {border_strong};
        }}

        QFrame#DropArea[dragActive="true"] {{
            border-color: {primary};
            background-color: {surface_alt};
        }}

        /* Historial: sin marco. La superficie ya lo separa del fondo. */
        QListWidget {{
            background-color: {surface};
            border: none;
            border-radius: {RADIO_GRANDE}px;
            padding: 8px;
            outline: none;
        }}

        QListWidget::item {{
            padding: 11px 12px;
            border-radius: {RADIO_MEDIO}px;
            color: {text_primary};
        }}

        QListWidget::item:hover {{
            background-color: {surface_alt};
        }}

        QListWidget::item:selected {{
            background-color: {primary};
            color: {text_inverse};
        }}

        QScrollBar:vertical {{
            background: transparent;
            width: 10px;
            margin: 4px 2px;
        }}

        QScrollBar::handle:vertical {{
            background-color: {border_strong};
            border-radius: 4px;
            min-height: 28px;
        }}

        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}

        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: transparent;
        }}

        /* Spinner indeterminado */
        QProgressBar {{
            background-color: {surface_alt};
            border: none;
            border-radius: 3px;
            max-height: 5px;
        }}

        QProgressBar::chunk {{
            background-color: {primary};
            border-radius: 3px;
        }}

        /* Los tooltips del historial son largos; sin estilo propio heredan el
           del sistema y en tema oscuro quedan ilegibles. */
        QToolTip {{
            background-color: {surface};
            color: {text_primary};
            border: 1px solid {border_strong};
            border-radius: {RADIO_CHICO}px;
            padding: 7px 9px;
        }}
        """
