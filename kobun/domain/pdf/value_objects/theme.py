from dataclasses import dataclass
from typing import Dict, Any


@dataclass(frozen=True)
class AppTheme:
    """
    Value Object inmutable que representa un tema visual de Kobun.
    Garantiza que la UI siempre reciba colores válidos.
    """
    name: str
    colors: Dict[str, Any]

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
    def is_dark(self) -> bool:
        return self.name.lower() == "dark"

    def __str__(self) -> str:
        return f"Theme(name={self.name})"