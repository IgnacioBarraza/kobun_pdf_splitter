from PySide6.QtGui import QIcon

from kobun.shared.config.app_settings import APP_ICON_SIZES, app_icon_file


def load_app_icon() -> QIcon:
    """
    Icono de la aplicación con todos sus tamaños.

    Se agregan uno por uno en lugar de cargar sólo el más grande: Qt elige el
    más cercano al contexto donde lo dibuja, y a 16 píxeles reducir desde un
    PNG hecho para ese tamaño se ve bastante mejor que reducir desde 256.

    Un tamaño que falte se omite; el icono nunca es motivo para no arrancar.
    """
    icon = QIcon()

    for size in APP_ICON_SIZES:
        ruta = app_icon_file(size)
        if ruta.exists():
            icon.addFile(str(ruta))

    return icon
