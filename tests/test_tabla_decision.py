"""Tabla de decision de liquidar() (seccion 2.3 de diseno-de-pruebas.md)."""

import pytest

from planilla.calculo import liquidar

SIN_CUOTA = 0
CUOTA_CABE = 500
CUOTA_EXCEDE = 5000


def monto(valor):
    """Compara montos en quetzales con tolerancia de medio centavo."""
    return pytest.approx(valor, abs=0.005)


@pytest.mark.parametrize(
    ("afiliado", "dias", "cuota", "igss", "bonificacion", "prestamo", "liquido"),
    [
        pytest.param(True, 30, SIN_CUOTA, 231.84, 250.00, 0.00, 4778.16, id="R1"),
        pytest.param(True, 30, CUOTA_CABE, 231.84, 250.00, 500.00, 4278.16, id="R2"),
        pytest.param(True, 30, CUOTA_EXCEDE, 231.84, 250.00, 3338.16, 1440.00, id="R3"),
        pytest.param(True, 15, SIN_CUOTA, 231.84, 125.00, 0.00, 4653.16, id="R4"),
        pytest.param(True, 15, CUOTA_CABE, 231.84, 125.00, 500.00, 4153.16, id="R5"),
        pytest.param(True, 15, CUOTA_EXCEDE, 231.84, 125.00, 3213.16, 1440.00, id="R6"),
        pytest.param(False, 30, SIN_CUOTA, 0.00, 250.00, 0.00, 5010.00, id="R7"),
        pytest.param(False, 30, CUOTA_CABE, 0.00, 250.00, 500.00, 4510.00, id="R8"),
        pytest.param(False, 30, CUOTA_EXCEDE, 0.00, 250.00, 3570.00, 1440.00, id="R9"),
        pytest.param(False, 15, SIN_CUOTA, 0.00, 125.00, 0.00, 4885.00, id="R10"),
        pytest.param(False, 15, CUOTA_CABE, 0.00, 125.00, 500.00, 4385.00, id="R11"),
        pytest.param(False, 15, CUOTA_EXCEDE, 0.00, 125.00, 3445.00, 1440.00, id="R12"),
    ],
)
def test_liquidar_segun_tabla_de_decision(
    afiliado, dias, cuota, igss, bonificacion, prestamo, liquido
):
    planilla = liquidar(
        salario_base=4800,
        horas_extra=0,
        dias_trabajados=dias,
        afiliado_igss=afiliado,
        cuota_prestamo=cuota,
    )

    # Constantes de la tabla: la bonificacion no entra al IGSS ni al ISR.
    assert planilla.salario_ordinario == monto(4800.00)
    assert planilla.isr == monto(40.00)
    assert planilla.igss == monto(igss)
    assert planilla.bonificacion == monto(bonificacion)
    assert planilla.prestamo == monto(prestamo)
    assert planilla.liquido == monto(liquido)
