import pytest

from kobun.domain.pdf.exceptions.invalid_page_range_exception import InvalidPageRangeException
from kobun.domain.pdf.value_objects.page_range import PageRange


def test_page_range_creation_success():
    p_range = PageRange(start=1, end=10)
    assert p_range.start == 1
    assert p_range.end == 10


def test_page_range_to_range_conversion():
    p_range = PageRange(start=1, end=3)
    assert list(p_range.to_range()) == [1, 2, 3]  #


def test_page_range_error_when_start_is_greater_than_end():
    with pytest.raises(InvalidPageRangeException, match="cannot be greater than"):
        PageRange(start=10, end=5)


def test_page_range_error_with_negative_values():
    with pytest.raises(InvalidPageRangeException):
        PageRange(start=0, end=10)


def test_page_range_string_representation():
    p_range = PageRange(start=5, end=15)
    assert str(p_range) == "5-15"