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
    message = "Rango fuera de límites: El PDF tiene 10 páginas."

    assert error_messages.translate(InvalidPageRangeException(message)) == message


def test_unexpected_errors_show_a_generic_message():
    """A traceback on screen helps nobody."""
    translated = error_messages.translate(RuntimeError("segfault en el motor"))

    assert translated == error_messages.UNEXPECTED_ERROR_MESSAGE
    assert "segfault" not in translated


def test_overridden_messages_replace_the_domain_text():
    translated = error_messages.translate(EncryptedPdfException("'x.pdf' está protegido."))

    assert "contraseña" in translated
    assert translated != "'x.pdf' está protegido."


def test_an_expected_error_without_message_still_says_something():
    assert error_messages.translate(InvalidPdfException("")) == error_messages.UNEXPECTED_ERROR_MESSAGE


def test_technical_detail_includes_the_type():
    detail = error_messages.technical_detail(RuntimeError("boom"))

    assert detail == "RuntimeError: boom"


def test_subclasses_are_treated_as_expected():
    """PdfNotFoundException inherits from InvalidPdfException."""
    assert error_messages.is_expected(PdfNotFoundException("no está"))


# =========================
# Dialog contents
# =========================

def test_expected_errors_produce_a_warning_prompt():
    prompt = error_messages.build_error_prompt(
        InvalidOutputPathException("El archivo de salida ya existe: out.pdf")
    )

    assert prompt.is_critical is False
    assert prompt.title == error_messages.EXPECTED_TITLE
    assert prompt.message == "El archivo de salida ya existe: out.pdf"


def test_expected_errors_carry_no_technical_detail():
    """There is nothing technical to report: the user can fix it themselves."""
    prompt = error_messages.build_error_prompt(InvalidPageRangeException("Rango inválido"))

    assert prompt.detail is None


def test_unexpected_errors_produce_a_critical_prompt():
    prompt = error_messages.build_error_prompt(RuntimeError("segfault"))

    assert prompt.is_critical is True
    assert prompt.title == error_messages.UNEXPECTED_TITLE
    assert prompt.message == error_messages.UNEXPECTED_ERROR_MESSAGE


def test_unexpected_errors_keep_the_detail_for_reporting():
    prompt = error_messages.build_error_prompt(RuntimeError("segfault en el motor"))

    assert prompt.detail == "RuntimeError: segfault en el motor"
    assert "segfault" not in prompt.message, "El detail va aparte, no en el mensaje"


def test_the_prompt_respects_message_overrides():
    prompt = error_messages.build_error_prompt(EncryptedPdfException("'x.pdf' está protegido."))

    assert "contraseña" in prompt.message
