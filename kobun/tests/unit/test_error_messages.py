from kobun.domain.pdf.exceptions.encrypted_pdf_exception import EncryptedPdfException
from kobun.domain.pdf.exceptions.file_open_exception import FileOpenException
from kobun.domain.pdf.exceptions.invalid_output_path_exception import InvalidOutputPathException
from kobun.domain.pdf.exceptions.invalid_page_range_exception import InvalidPageRangeException
from kobun.domain.pdf.exceptions.invalid_pdf_exception import InvalidPdfException
from kobun.domain.pdf.exceptions.pdf_not_found_exception import PdfNotFoundException
from kobun.presentation import error_messages


def test_domain_errors_are_expected():
    esperados = [
        InvalidPdfException("x"),
        PdfNotFoundException("x"),
        EncryptedPdfException("x"),
        InvalidPageRangeException("x"),
        InvalidOutputPathException("x"),
        FileOpenException("x"),
    ]

    assert all(error_messages.is_expected(e) for e in esperados)


def test_programming_errors_are_not_expected():
    assert not error_messages.is_expected(RuntimeError("boom"))
    assert not error_messages.is_expected(AttributeError("None no tiene 'x'"))
    assert not error_messages.is_expected(KeyError("title"))


def test_expected_errors_show_their_own_message():
    mensaje = "Rango fuera de límites: El PDF tiene 10 páginas."

    assert error_messages.translate(InvalidPageRangeException(mensaje)) == mensaje


def test_unexpected_errors_show_a_generic_message():
    """Un traceback en pantalla no le sirve a nadie."""
    traducido = error_messages.translate(RuntimeError("segfault en el motor"))

    assert traducido == error_messages.UNEXPECTED_ERROR_MESSAGE
    assert "segfault" not in traducido


def test_overridden_messages_replace_the_domain_text():
    traducido = error_messages.translate(EncryptedPdfException("'x.pdf' está protegido."))

    assert "contraseña" in traducido
    assert traducido != "'x.pdf' está protegido."


def test_an_expected_error_without_message_still_says_something():
    assert error_messages.translate(InvalidPdfException("")) == error_messages.UNEXPECTED_ERROR_MESSAGE


def test_technical_detail_includes_the_type():
    detalle = error_messages.technical_detail(RuntimeError("boom"))

    assert detalle == "RuntimeError: boom"


def test_subclasses_are_treated_as_expected():
    """PdfNotFoundException hereda de InvalidPdfException."""
    assert error_messages.is_expected(PdfNotFoundException("no está"))
