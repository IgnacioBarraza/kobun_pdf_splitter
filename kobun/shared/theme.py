from dataclasses import dataclass
from typing import Any, Dict, Optional

# Umbral de luminancia relativa por debajo del cual un fondo se considera
# oscuro. 0.5 es el punto medio y alcanza para decidir qué ícono usar.
_DARK_LUMINANCE_THRESHOLD = 0.5


@dataclass(frozen=True)
class AppTheme:
    """
    Value Object inmutable que representa un tema visual de Kobun.
    Garantiza que la UI siempre reciba colores válidos.

    Vive en `shared` y no en `domain`: un tema no es un concepto del negocio
    de manipular PDFs, sino un detalle transversal de presentación.
    """
    name: str
    colors: Dict[str, Any]

    label: Optional[str] = None
    """Nombre para mostrar en el selector. El tema se autodescribe para que
    agregar una paleta no obligue a tocar la UI."""

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("El nombre del tema no puede estar vacío.")

        if not self.colors or "background" not in self.colors:
            raise ValueError("El tema debe contener al menos un color de fondo (background).")

    def get_color(self, key: str, default: str = "#000000") -> str:
        return self.colors.get(key, default)

    def get_text_color(self, key: str, default: str = "#000000") -> str:
        text_colors = self.colors.get("text", {})
        if isinstance(text_colors, dict):
            return text_colors.get(key, default)
        return default

    @property
    def display_name(self) -> str:
        """
        Etiqueta declarada, o el nombre técnico presentable si falta.
        """
        if self.label and self.label.strip():
            return self.label

        return self.name.replace("_", " ").title()

    @property
    def is_dark(self) -> bool:
        """
        Se deduce de la luminancia del fondo, no del nombre del tema.

        Con una sola paleta oscura alcanzaba con comparar el nombre, pero al
        haber varias el nombre deja de ser confiable: una paleta oscura que no
        se llame "dark" recibiría el ícono equivocado.
        """
        luminance = self._background_luminance()
        if luminance is None:
            return self.name.lower() == "dark"

        return luminance < _DARK_LUMINANCE_THRESHOLD

    def _background_luminance(self) -> Optional[float]:
        """
        Luminancia relativa aproximada del fondo, entre 0 y 1.
        Devuelve None si el color no es un hexadecimal interpretable.
        """
        raw = str(self.get_color("background", "")).strip().lstrip("#")

        if len(raw) == 3:
            raw = "".join(char * 2 for char in raw)

        if len(raw) != 6:
            return None

        try:
            red, green, blue = (int(raw[i:i + 2], 16) / 255 for i in (0, 2, 4))
        except ValueError:
            return None

        # Coeficientes de percepción del brillo: el ojo ve mucho más el verde
        # que el azul.
        return 0.2126 * red + 0.7152 * green + 0.0722 * blue

    def __str__(self) -> str:
        return f"Theme(name={self.name})"
