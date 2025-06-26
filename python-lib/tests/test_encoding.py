import pytest
from line_protocol.network.request import NoneEncoder, FormulaEncoder, MappingEncoder, TwosComplementEncoder


class TestNoneEncoder:

    @pytest.mark.parametrize("value", [42, 0, -1, 1000])
    def test_NoneEncode_Valid(self, value):
        encoder = NoneEncoder("test")

        assert encoder.encode(value) == value

    @pytest.mark.parametrize("value", ["A", "Abc", "-1", "100"])
    def test_NoneEncode_Invalid(self, value):
        encoder = NoneEncoder("test")

        with pytest.raises(ValueError):
            encoder.encode(value)

    @pytest.mark.parametrize("value", [42, 0, -1, 1000])
    def test_NoneDecode_Valid(self, value):
        encoder = NoneEncoder("test")

        assert encoder.decode(value) == value

class TestFormulaEncoder:

    @pytest.mark.parametrize("value,expected", [
        (42.0, 42),
        (0.0, 0),
        (-1.0, -1),
        (100.0, 100)
    ])
    def test_FormulaEncode_Valid(self, value, expected):
        encoder = FormulaEncoder("test", scale=1.0, offset=0.0, unit="unit")

        assert encoder.encode(value) == expected

    @pytest.mark.parametrize("value", ["A", "Abc"])
    def test_FormulaEncode_Invalid(self, value):
        encoder = FormulaEncoder("test", scale=1.0, offset=0.0, unit="unit")

        with pytest.raises(ValueError):
            encoder.encode(value)

    @pytest.mark.parametrize("value,expected", [
        (42, 42.0),
        (0, 0.0),
        (-1, -1.0),
        (100, 100.0)
    ])
    def test_FormulaDecode_Valid(self, value, expected):
        encoder = FormulaEncoder("test", scale=1.0, offset=0.0, unit="unit")

        assert encoder.decode(value) == expected

class TestMappingEncoder:

    @pytest.mark.parametrize("value,expected", [
        ("A", 1),
        ("B", 2),
        ("C", 3)
    ])
    def test_MappingEncode_Valid(self, value, expected):
        mapping = {1: "A", 2: "B", 3: "C"}
        encoder = MappingEncoder("test", mapping)

        assert encoder.encode(value) == expected

    @pytest.mark.parametrize("value", ["D", "E", "F"])
    def test_MappingEncode_Invalid(self, value):
        mapping = {1: "A", 2: "B", 3: "C"}
        encoder = MappingEncoder("test", mapping)

        with pytest.raises(ValueError):
            encoder.encode(value)

    @pytest.mark.parametrize("value,expected", [
        (1, "A"),
        (2, "B"),
        (3, "C")
    ])
    def test_MappingDecode_Valid(self, value, expected):
        mapping = {1: "A", 2: "B", 3: "C"}
        encoder = MappingEncoder("test", mapping)

        assert encoder.decode(value) == expected

    @pytest.mark.parametrize("value", [4, 5, 6])
    def test_MappingDecode_Invalid(self, value):
        mapping = {1: "A", 2: "B", 3: "C"}
        encoder = MappingEncoder("test", mapping)

        with pytest.raises(ValueError):
            encoder.decode(value)
