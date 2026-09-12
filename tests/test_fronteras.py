"""Valores frontera (seccion 2.2 de diseno-de-pruebas.md)."""

import pytest

from planilla.calculo import (
    bonificacion_incentivo,
    descuento_isr,
    descuento_prestamo,
    salario_ordinario,
    valor_hora,
)


def monto(valor):
    """Compara montos en quetzales con tolerancia de medio centavo."""
    return pytest.approx(valor, abs=0.005)


@pytest.mark.parametrize("salario_base", [-0.01, 0], ids=["BV-01 -0.01", "BV-01 0"])
def test_bv01_salario_no_positivo_se_rechaza(salario_base):
    with pytest.raises(ValueError, match="salario base"):
        valor_hora(salario_base)


def test_bv01_salario_minimo_positivo_se_acepta():
    assert valor_hora(0.01) == pytest.approx(0.01 / 240)


@pytest.mark.parametrize(
    ("horas_extra", "ordinario"),
    [
        pytest.param(0, 4800.00, id="BV-02 0"),
        pytest.param(1, 4830.00, id="BV-02 1"),
        pytest.param(47, 6210.00, id="BV-03 47"),
        pytest.param(48, 6240.00, id="BV-03 48"),
    ],
)
def test_horas_extra_dentro_del_rango(horas_extra, ordinario):
    assert salario_ordinario(4800, horas_extra) == monto(ordinario)


@pytest.mark.parametrize("horas_extra", [-1, 49], ids=["BV-02 -1", "BV-03 49"])
def test_horas_extra_fuera_del_rango(horas_extra):
    with pytest.raises(ValueError, match="horas extra"):
        salario_ordinario(4800, horas_extra)


@pytest.mark.parametrize(
    ("dias", "bonificacion"),
    [
        pytest.param(0, 0.00, id="BV-04 0"),
        pytest.param(1, 8.33, id="BV-04 1"),
        pytest.param(29, 241.67, id="BV-05 29"),
        pytest.param(30, 250.00, id="BV-05 30"),
    ],
)
def test_dias_dentro_del_rango(dias, bonificacion):
    assert bonificacion_incentivo(dias) == monto(bonificacion)


@pytest.mark.parametrize("dias", [-1, 31], ids=["BV-04 -1", "BV-05 31"])
def test_dias_fuera_del_rango(dias):
    with pytest.raises(ValueError, match="dias trabajados"):
        bonificacion_incentivo(dias)


@pytest.mark.parametrize(
    ("salario_base", "isr"),
    [
        pytest.param(3999, 0.00, id="BV-06 3999"),
        pytest.param(4000, 0.00, id="BV-06 4000"),
        pytest.param(4001, 0.05, id="BV-06 4001"),
        pytest.param(28999, 1249.95, id="BV-07 28999"),
        pytest.param(29000, 1250.00, id="BV-07 29000"),
        pytest.param(29001, 1250.07, id="BV-07 29001"),
    ],
)
def test_isr_en_los_limites_de_tramo(salario_base, isr):
    assert descuento_isr(salario_base) == monto(isr)


def test_bv08_cuota_negativa_se_rechaza():
    with pytest.raises(ValueError, match="cuota"):
        descuento_prestamo(1000, 1000, -0.01)


@pytest.mark.parametrize(
    ("cuota", "descontado"),
    [
        pytest.param(0, 0.00, id="BV-08 0"),
        pytest.param(0.01, 0.01, id="BV-08 0.01"),
        pytest.param(699, 699.00, id="BV-09 699"),
        pytest.param(700, 700.00, id="BV-09 700"),
        pytest.param(701, 700.00, id="BV-09 701"),
    ],
)
def test_cuota_contra_el_margen_disponible(cuota, descontado):
    # Ordinario Q1000 y liquido previo Q1000: piso Q300, margen Q700.
    assert descuento_prestamo(1000, 1000, cuota) == monto(descontado)


@pytest.mark.parametrize(
    ("liquido_antes", "descontado"),
    [
        pytest.param(299, 0.00, id="BV-10 299"),
        pytest.param(300, 0.00, id="BV-10 300"),
        pytest.param(301, 1.00, id="BV-10 301"),
    ],
)
def test_liquido_previo_contra_el_piso(liquido_antes, descontado):
    # Ordinario Q1000: piso Q300. Cuota de Q50.
    assert descuento_prestamo(liquido_antes, 1000, 50) == monto(descontado)
