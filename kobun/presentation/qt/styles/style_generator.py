from kobun.shared.theme import AppTheme


class StyleGenerator:
    """
    Transforma un AppTheme en una cadena QSS (Qt Style Sheets).

    Todo el color de la aplicación sale de acá: los widgets no llevan estilos
    propios, así que alternar tema es reemplazar esta hoja y nada más.
    """

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

        return f"""
        QWidget {{
            background-color: {bg};
            color: {text_primary};
            font-size: 13px;
        }}

        QFrame#MainContainer {{
            background-color: {bg};
        }}

        QFrame#Sidebar {{
            background-color: {surface};
            border-right: 1px solid {border};
        }}

        QLabel#Logo {{
            font-size: 22px;
            font-weight: bold;
            color: {primary};
        }}

        QLabel#Title {{
            font-size: 19px;
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

        /* Botón primario */
        QPushButton#PrimaryButton {{
            background-color: {primary};
            color: {text_inverse};
            border: none;
            border-radius: 6px;
            padding: 10px 20px;
            font-weight: bold;
        }}

        QPushButton#PrimaryButton:hover {{
            background-color: {primary_hover};
        }}

        QPushButton#PrimaryButton:disabled {{
            background-color: {surface_alt};
            color: {text_disabled};
        }}

        /* Botones secundarios y de navegación */
        QPushButton {{
            background-color: {surface};
            color: {text_primary};
            border: 1px solid {border};
            border-radius: 6px;
            padding: 8px 14px;
            text-align: left;
        }}

        QPushButton:hover {{
            border-color: {border_strong};
            background-color: {surface_alt};
        }}

        QPushButton:disabled {{
            color: {text_disabled};
        }}

        QPushButton#NavButton:checked {{
            background-color: {surface_alt};
            border-color: {primary};
            font-weight: bold;
        }}

        /* Entradas */
        QLineEdit {{
            background-color: {surface};
            border: 1px solid {border};
            border-radius: 4px;
            padding: 8px;
            color: {text_primary};
            selection-background-color: {primary};
            selection-color: {text_inverse};
        }}

        QLineEdit:focus {{
            border: 1px solid {primary};
        }}

        QLineEdit:disabled {{
            color: {text_disabled};
            background-color: {surface_alt};
        }}

        QComboBox {{
            background-color: {surface};
            border: 1px solid {border};
            border-radius: 4px;
            padding: 7px;
        }}

        QComboBox QAbstractItemView {{
            background-color: {surface};
            selection-background-color: {primary};
            selection-color: {text_inverse};
            border: 1px solid {border};
        }}

        /* Zona de arrastre */
        QFrame#DropArea {{
            background-color: {surface};
            border: 2px dashed {border_strong};
            border-radius: 10px;
        }}

        QFrame#DropArea[dragActive="true"] {{
            border-color: {primary};
            background-color: {surface_alt};
        }}

        /* Historial */
        QListWidget {{
            background-color: {surface};
            border: 1px solid {border};
            border-radius: 6px;
            padding: 4px;
        }}

        QListWidget::item {{
            padding: 8px;
            border-radius: 4px;
        }}

        QListWidget::item:selected {{
            background-color: {primary};
            color: {text_inverse};
        }}

        /* Spinner indeterminado */
        QProgressBar {{
            background-color: {surface_alt};
            border: none;
            border-radius: 3px;
            max-height: 6px;
        }}

        QProgressBar::chunk {{
            background-color: {primary};
            border-radius: 3px;
        }}
        """
