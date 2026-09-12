"""Particiones de la CLI (seccion 2.4 de diseno-de-pruebas.md)."""

import runpy
import sys

import pytest

from planilla import cli


def ejecutar(monkeypatch, capsys, *argumentos):
    """Corre main() con los argumentos dados y devuelve (codigo, salida)."""
    monkeypatch.setattr(sys, "argv", ["planilla", *argumentos])
    codigo = cli.main()
    return codigo, capsys.readouterr().out


def test_cli01_sin_salario_base_muestra_uso_y_falla(monkeypatch, capsys):
    codigo, salida = ejecutar(monkeypatch, capsys)

    assert codigo == 1
    assert salida == cli.USO + "\n"


@pytest.mark.parametrize(
    ("argumentos", "esperado"),
    [
        pytest.param(
            [
                "salario_base=4000",
                "horas_extra=8",
                "dias_trabajados=30",
                "cuota_prestamo=500",
            ],
            "Liquido: Q3747.14 | Descuentos: Q702.86",
            id="CLI-02 ejemplo del README",
        ),
        pytest.param(
            ["salario_base=4800"],
            "Liquido: Q4778.16 | Descuentos: Q271.84",
            id="CLI-03 valores por defecto",
        ),
        pytest.param(
            ["salario_base=4800", "afiliado_igss=no"],
            "Liquido: Q5010.0 | Descuentos: Q40.0",
            id="CLI-04 no afiliado",
        ),
    ],
)
def test_cli_imprime_resumen_y_termina_bien(monkeypatch, capsys, argumentos, esperado):
    codigo, salida = ejecutar(monkeypatch, capsys, *argumentos)

    assert codigo == 0
    assert salida == esperado + "\n"


def test_cli05_parse_args_convierte_numeros_y_ignora_lo_que_no_es_clave_valor():
    # "suelto" va en medio: lo que sigue despues tambien debe leerse.
    datos = cli.parse_args(["salario_base=4800", "suelto", "afiliado_igss=no"])

    assert datos == {"salario_base": 4800.0, "afiliado_igss": "no"}


@pytest.mark.parametrize(
    ("argumentos", "codigo_salida"),
    [
        pytest.param([], 1, id="CLI-06 sin salario"),
        pytest.param(["salario_base=4800"], 0, id="CLI-06 con salario"),
    ],
)
def test_cli06_ejecutado_como_modulo_propaga_el_codigo_de_salida(
    monkeypatch, capsys, argumentos, codigo_salida
):
    # Equivale a `python -m planilla.cli`. Se saca el modulo de sys.modules para
    # que runpy lo ejecute desde cero como __main__.
    monkeypatch.setattr(sys, "argv", ["planilla", *argumentos])
    monkeypatch.delitem(sys.modules, "planilla.cli", raising=False)

    with pytest.raises(SystemExit) as salida:
        runpy.run_module("planilla.cli", run_name="__main__")

    assert salida.value.code == codigo_salida
    capsys.readouterr()
