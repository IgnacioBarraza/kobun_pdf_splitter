from kobun.shared.theme import AppTheme


class StyleGenerator:
    """
    Transforma un AppTheme en una cadena QSS (Qt Style Sheets).
    Usa los tokens del JSON para inyectar colores en los widgets de Qt.
    """

    @staticmethod
    def generate(theme: AppTheme) -> str:
        # Extraemos los colores del Value Object de forma segura
        bg = theme.get_color("background")
        surface = theme.get_color("surface")
        primary = theme.get_color("primary")
        border = theme.get_color("border")

        # Colores de texto
        text_primary = theme.get_text_color("primary")
        text_secondary = theme.get_text_color("secondary")
        text_inverse = theme.get_text_color("inverse")

        return f"""
        /* Ventana Principal */
        QMainWindow {{
            background-color: {bg};
        }}

        /* Contenedores y Paneles */
        QFrame#MainContainer {{
            background-color: {bg};
        }}

        QFrame#Sidebar {{
            background-color: {surface};
            border-right: 1px solid {border};
        }}

        /* Botón Primario (Basado en tu diseño) */
        QPushButton#PrimaryButton {{
            background-color: {primary};
            color: {text_inverse};
            border: none;
            border-radius: 6px;
            padding: 10px 20px;
            font-weight: bold;
            font-size: 13px;
        }}

        QPushButton#PrimaryButton:hover {{
            background-color: {primary}dd; /* Un poco de transparencia al pasar el mouse */
        }}

        /* Campos de Entrada (Inputs) */
        QLineEdit {{
            background-color: {surface};
            border: 1px solid {border};
            border-radius: 4px;
            padding: 8px;
            color: {text_primary};
        }}

        QLineEdit:focus {{
            border: 1px solid {primary};
        }}

        /* Etiquetas (Labels) */
        QLabel {{
            color: {text_primary};
            font-size: 13px;
        }}

        QLabel#SecondaryText {{
            color: {text_secondary};
            font-size: 11px;
        }}

        /* Tablas e Historial */
        QTableWidget {{
            background-color: {bg};
            alternate-background-color: {surface};
            gridline-color: {border};
            color: {text_primary};
            border: none;
        }}
        """