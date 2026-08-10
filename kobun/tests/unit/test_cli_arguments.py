from pathlib import Path

from kobun.presentation.qt.cli_arguments import first_pdf_argument


def test_no_arguments_means_no_document():
    assert first_pdf_argument(["main.py"]) is None
    assert first_pdf_argument([]) is None
    assert first_pdf_argument(None) is None


def test_a_pdf_argument_is_recognized():
    assert first_pdf_argument(["main.py", "/libros/book.pdf"]) == Path("/libros/book.pdf")


def test_the_program_name_is_never_taken_as_a_document():
    """argv[0] puede terminar en .pdf si alguien renombra el script."""
    assert first_pdf_argument(["raro.pdf"]) is None


def test_uppercase_extension_is_accepted():
    assert first_pdf_argument(["main.py", "LIBRO.PDF"]) == Path("LIBRO.PDF")


def test_non_pdf_arguments_are_ignored():
    assert first_pdf_argument(["main.py", "notas.txt", "imagen.png"]) is None


def test_the_first_pdf_wins_when_several_are_passed():
    """Igual que en el drag & drop: la pantalla trabaja sobre un documento."""
    resultado = first_pdf_argument(["main.py", "uno.pdf", "dos.pdf"])

    assert resultado == Path("uno.pdf")


def test_a_pdf_after_other_files_is_still_found():
    resultado = first_pdf_argument(["main.py", "notas.txt", "libro.pdf"])

    assert resultado == Path("libro.pdf")


def test_qt_flags_are_not_mistaken_for_files():
    """Qt acepta opciones propias como -style o --platform."""
    assert first_pdf_argument(["main.py", "-style", "Fusion"]) is None
    assert first_pdf_argument(["main.py", "--platform", "offscreen"]) is None


def test_a_pdf_alongside_qt_flags_is_still_found():
    resultado = first_pdf_argument(["main.py", "--platform", "offscreen", "libro.pdf"])

    assert resultado == Path("libro.pdf")


def test_blank_arguments_are_ignored():
    assert first_pdf_argument(["main.py", "", "   "]) is None


def test_paths_with_spaces_survive():
    resultado = first_pdf_argument(["main.py", "/home/x/manual de prueba.pdf"])

    assert resultado == Path("/home/x/manual de prueba.pdf")


def test_existence_is_not_checked_here():
    """
    Validar que sea legible es tarea de LoadPdfUseCase; acá sólo se decide si
    el argumento parece un documento.
    """
    assert first_pdf_argument(["main.py", "/no/existe.pdf"]) == Path("/no/existe.pdf")
