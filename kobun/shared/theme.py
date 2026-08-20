from dataclasses import dataclass
from typing import Any, Dict, Optional

# Relative luminance below which a background counts as dark. 0.5 is the
# midpoint and is enough to decide which icon to use.
_DARK_LUMINANCE_THRESHOLD = 0.5


@dataclass(frozen=True)
class AppTheme:
    """
    Immutable Value Object representing one of Kobun's visual themes.
    It guarantees the UI always receives valid colours.

    It lives in `shared` and not in `domain`: a theme is not a concept of the
    business of manipulating PDFs, but a cross-cutting presentation detail.
    """
    name: str
    colors: Dict[str, Any]

    label: Optional[str] = None
    """Display name for the selector. A theme describes itself so adding a
    palette does not force a change to the UI."""

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("A theme name cannot be empty.")

        if not self.colors or "background" not in self.colors:
            raise ValueError("A theme must contain at least a background colour.")

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
        The declared label, or the technical name made presentable if absent.
        """
        if self.label and self.label.strip():
            return self.label

        return self.name.replace("_", " ").title()

    @property
    def is_dark(self) -> bool:
        """
        Derived from the background's luminance, not from the theme's name.

        With a single dark palette comparing the name was enough, but with
        several the name stops being reliable: a dark palette not called "dark"
        would get the wrong icon.
        """
        luminance = self._background_luminance()
        if luminance is None:
            return self.name.lower() == "dark"

        return luminance < _DARK_LUMINANCE_THRESHOLD

    def _background_luminance(self) -> Optional[float]:
        """
        Approximate relative luminance of the background, between 0 and 1.
        Returns None if the colour is not an interpretable hexadecimal.
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

        # Brightness perception coefficients: the eye sees green far more than
        # blue.
        return 0.2126 * red + 0.7152 * green + 0.0722 * blue

    def __str__(self) -> str:
        return f"Theme(name={self.name})"
