"""Particiones de equivalencia (seccion 2.1 de diseno-de-pruebas.md)."""

import pytest

from planilla.calculo import (
    bonificacion_incentivo,
    descuento_igss,
    descuento_isr,
    descuento_prestamo,
    liquidar,
    pago_horas_extra,
    salario_ordinario,
    valor_hora,
)


def monto(valor):
    """Compara montos en quetzales con tolerancia de medio centavo."""
    return pytest.approx(valor, abs=0.005)


@pytest.mark.parametrize(
    ("salario_base", "entradas", "mensaje"),
    [
        pytest.param(-1000, {}, "salario base", id="EP-01"),
        pytest.param(4800, {"horas_extra": -5}, "horas extra", id="EP-03"),
        pytest.param(4800, {"horas_extra": 60}, "horas extra", id="EP-05"),
        pytest.param(4800, {"dias_trabajados": -3}, "dias trabajados", id="EP-06"),
        pytest.param(4800, {"dias_trabajados": 40}, "dias trabajados", id="EP-09"),
        pytest.param(4800, {"cuota_prestamo": -100}, "cuota", id="EP-15"),
    ],
)
def test_liquidar_rechaza_particiones_invalidas(salario_base, entradas, mensaje):
    with pytest.raises(ValueError, match=mensaje):
        liquidar(salario_base, **entradas)


def test_ep02_salario_valido_da_valor_hora():
    assert valor_hora(4800) == monto(20.00)


def test_ep04_horas_extra_validas_se_pagan_con_recargo():
    assert pago_horas_extra(4800, 10) == monto(300.00)
    assert salario_ordinario(4800, 10) == monto(5100.00)


@pytest.mark.parametrize(
    ("dias", "esperado"),
    [
        pytest.param(15, 125.00, id="EP-07 mes incompleto"),
        pytest.param(30, 250.00, id="EP-08 mes completo"),
    ],
)
def test_bonificacion_por_particion_de_dias(dias, esperado):
    assert bonificacion_incentivo(dias) == monto(esperado)


@pytest.mark.parametrize(
    ("afiliado", "esperado"),
    [
        pytest.param(True, 246.33, id="EP-10 afiliado"),
        pytest.param(False, 0.00, id="EP-11 no afiliado"),
        pytest.param(None, 0.00, id="EP-11 sin dato de afiliacion"),
    ],
)
def test_igss_segun_afiliacion(afiliado, esperado):
    assert descuento_igss(5100, afiliado) == monto(esperado)


@pytest.mark.parametrize(
    ("salario_base", "esperado"),
    [
        pytest.param(3000, 0.00, id="EP-12 renta imponible no positiva"),
        pytest.param(4800, 40.00, id="EP-13 tramo del 5%"),
        pytest.param(35000, 1670.00, id="EP-14 tramo del 7%"),
    ],
)
def test_isr_mensual_por_tramo(salario_base, esperado):
    assert descuento_isr(salario_base) == monto(esperado)


def test_ep16_cuota_que_cabe_se_descuenta_completa():
    planilla = liquidar(4800, cuota_prestamo=500)

    assert planilla.prestamo == monto(500.00)
    assert planilla.liquido == monto(4278.16)


def test_ep17_cuota_que_excede_se_recorta_al_piso_del_30_por_ciento():
    planilla = liquidar(4800, cuota_prestamo=5000)

    assert planilla.prestamo == monto(3338.16)
    assert planilla.liquido == monto(1440.00)


def test_ep18_sin_margen_sobre_el_piso_no_se_descuenta_prestamo():
    assert descuento_prestamo(299, 1000, 50) == monto(0.00)
