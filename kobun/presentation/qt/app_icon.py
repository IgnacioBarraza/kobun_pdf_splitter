from PySide6.QtGui import QIcon

from kobun.shared.config.app_settings import APP_ICON_SIZES, app_icon_file


def load_app_icon() -> QIcon:
    """
    The application icon with all of its sizes.

    They are added one by one instead of loading only the largest: Qt picks the
    one closest to the context it draws in, and at 16 pixels shrinking a PNG
    made for that size looks considerably better than shrinking from 256.

    A missing size is skipped; the icon is never a reason not to start.
    """
    icon = QIcon()

    for size in APP_ICON_SIZES:
        path = app_icon_file(size)
        if path.exists():
            icon.addFile(str(path))

    return icon
