# Diseño de pruebas — Planilla

## 0. Base de prueba y alcance

La base de prueba son las **reglas de la planilla del README**: los resultados esperados de
este documento se calcularon a mano a partir de esas tablas, no leyendo el código.

Código bajo prueba:

- `src/planilla/calculo.py`: `valor_hora()`, `pago_horas_extra()`, `salario_ordinario()`,
  `bonificacion_incentivo()`, `descuento_igss()`, `isr_anual()`, `descuento_isr()`,
  `descuento_prestamo()`, `liquidar()` y `resumen()`.
- `src/planilla/cli.py`: `parse_args()` y `main()`.

Salvo que se indique otra cosa, los casos usan **salario base Q4800**: el valor hora queda en
Q20.00 exacto, cada hora extra en Q30.00 y el ISR mensual en Q40.00, lo que permite verificar
los esperados a mano sin arrastrar decimales.

Criterios de comparación:

- Montos: `pytest.approx(esperado, abs=0.005)` (medio centavo), porque son `float`.
- Entradas inválidas: `pytest.raises(ValueError)`.

## 1. Mapa de técnicas

| Técnica | Aplica | Función o clase | Justificación |
|---|---|---|---|
| Equivalence Partitioning | Sí | Todas las reglas de `calculo.py` | Cada entrada tiene rangos válidos e inválidos definidos en el README (salario mayor que cero, 0 a 48 horas, 0 a 30 días, cuota no negativa) y el ISR agrupa la renta imponible en tres tramos con el mismo comportamiento dentro de cada uno. |
| Boundary Value Analysis | Sí | `valor_hora()`, `pago_horas_extra()`, `bonificacion_incentivo()`, `descuento_isr()`, `descuento_prestamo()` | Las reglas cambian en límites exactos: 0 y 48 horas, 0 y 30 días, renta imponible 0 y Q300,000, cuota 0, y el piso del 30% del salario ordinario. Ahí es donde un `<` en lugar de `<=` pasa desapercibido. |
| Decision Table Testing | Sí | `liquidar()` | El líquido depende de la combinación de tres condiciones: si está afiliado al IGSS, si el mes está completo y cómo se compara la cuota del préstamo con el margen disponible. Como el préstamo se descuenta de último, las otras dos condiciones cambian el margen y por lo tanto cuánto se descuenta. |
| State Transition Testing | No | — | El cálculo no tiene estados: son funciones puras y `Planilla` es un `dataclass` inmutable. No hay eventos ni transiciones que modelar. |

La CLI no tiene reglas en el README, pero entra en el gate de coverage. Se prueba con
particiones de sus propias entradas (sección 2.4).

## 2. Productos de trabajo por técnica

### 2.1 Equivalence Partitioning

| ID | Entrada o regla | Partición | Tipo | Representante | Resultado esperado |
|---|---|---|---|---|---|
| EP-01 | `salario_base` | `<= 0` | Inválida | `-1000` | `ValueError` |
| EP-02 | `salario_base` | `> 0` | Válida | `4800` | Valor hora Q20.00 |
| EP-03 | `horas_extra` | `< 0` | Inválida | `-5` | `ValueError` |
| EP-04 | `horas_extra` | `0 a 48` | Válida | `10` | Pago Q300.00 (20 × 1.5 × 10); ordinario Q5100.00 |
| EP-05 | `horas_extra` | `> 48` | Inválida | `60` | `ValueError` |
| EP-06 | `dias_trabajados` | `< 0` | Inválida | `-3` | `ValueError` |
| EP-07 | `dias_trabajados` | Mes incompleto, `0 <= d < 30` | Válida | `15` | Bonificación Q125.00 (250 × 15 / 30) |
| EP-08 | `dias_trabajados` | Mes completo, `30` | Válida | `30` | Bonificación Q250.00 |
| EP-09 | `dias_trabajados` | `> 30` | Inválida | `40` | `ValueError` |
| EP-10 | `afiliado_igss` | Afiliado | Válida | `True`, ordinario Q5100 | IGSS Q246.33 (5100 × 4.83%) |
| EP-11 | `afiliado_igss` | No afiliado | Válida | `False` y `None` (sin dato), ordinario Q5100 | IGSS Q0.00 |
| EP-12 | Renta imponible | `<= 0` (base `<= 4000`) | Válida | base `3000` | ISR mensual Q0.00 |
| EP-13 | Renta imponible | `0 < x <= 300000` (base `4000 < b <= 29000`) | Válida | base `4800` | ISR mensual Q40.00 (9600 × 5% / 12) |
| EP-14 | Renta imponible | `> 300000` (base `> 29000`) | Válida | base `35000` | ISR mensual Q1670.00 ((15000 + 72000 × 7%) / 12) |
| EP-15 | `cuota_prestamo` | `< 0` | Inválida | `-100` | `ValueError` |
| EP-16 | `cuota_prestamo` | Cabe en el margen | Válida | `500` con base 4800 | Préstamo Q500.00; líquido Q4278.16 |
| EP-17 | `cuota_prestamo` | Excede el margen | Válida | `5000` con base 4800 | Préstamo Q3338.16; líquido Q1440.00 (= 30% de 4800) |
| EP-18 | Margen del préstamo | Líquido previo `<=` piso | Válida | `descuento_prestamo(299, 1000, 50)` | Préstamo Q0.00 |

EP-16 y EP-17 usan `liquidar(4800)` con mes completo y afiliado: ordinario Q4800,
bonificación Q250, IGSS Q231.84, ISR Q40, líquido antes del préstamo Q4778.16, piso Q1440 y
margen Q3338.16.

EP-18 se prueba llamando `descuento_prestamo()` directo porque desde `liquidar()` no se
alcanza (ver observación O1).

### 2.2 Boundary Value Analysis

Salario base Q4800 donde aplica.

| ID | Límite | Justo antes | En el límite | Justo después | Resultado esperado |
|---|---|---|---|---|---|
| BV-01 | Salario base mayor que cero | `-0.01` | `0` | `0.01` | `-0.01` y `0` → `ValueError`; `0.01` → valor hora Q0.0000417 (válido) |
| BV-02 | Mínimo de horas extra | `-1` | `0` | `1` | `-1` → `ValueError`; `0` → ordinario Q4800; `1` → Q4830 |
| BV-03 | Máximo de horas extra | `47` | `48` | `49` | `47` → ordinario Q6210; `48` → Q6240; `49` → `ValueError` |
| BV-04 | Mínimo de días | `-1` | `0` | `1` | `-1` → `ValueError`; `0` → bonificación Q0.00; `1` → Q8.33 |
| BV-05 | Máximo de días / mes completo | `29` | `30` | `31` | `29` → Q241.67 (proporcional); `30` → Q250.00; `31` → `ValueError` |
| BV-06 | Renta imponible = 0 | base `3999` | base `4000` | base `4001` | ISR mensual Q0.00, Q0.00 y Q0.05 |
| BV-07 | Renta imponible = Q300,000 | base `28999` | base `29000` | base `29001` | ISR mensual Q1249.95, Q1250.00 y Q1250.07 |
| BV-08 | Cuota no negativa | `-0.01` | `0` | `0.01` | `-0.01` → `ValueError`; `0` → Q0.00; `0.01` → Q0.01 |
| BV-09 | Cuota contra el margen | cuota `699` | cuota `700` | cuota `701` | Préstamo Q699, Q700 y Q700 (se recorta) |
| BV-10 | Líquido previo contra el piso | antes `299` | antes `300` | antes `301` | Préstamo Q0, Q0 y Q1 |

BV-08, BV-09 y BV-10 llaman `descuento_prestamo(liquido_antes, salario_ordinario, cuota)` con
ordinario Q1000, así que el piso es Q300. En BV-08 y BV-09 el líquido previo es Q1000
(margen Q700); en BV-10 la cuota es Q50.

BV-06 y BV-07 salen de despejar la regla: renta imponible = base × 12 − 48000. Es 0 con
base Q4000 y Q300,000 con base Q29,000.

### 2.3 Decision Table Testing

`liquidar(salario_base=4800, horas_extra=0, dias_trabajados=D, afiliado_igss=A, cuota_prestamo=C)`.

Constantes en todas las reglas: ordinario Q4800, ISR Q40.00, piso del préstamo Q1440.

Condiciones:

- **C1**: ¿Está afiliado al IGSS?
- **C2**: ¿Trabajó el mes completo? (30 días sí, 15 días no)
- **C3**: Cuota del préstamo: sin cuota (`0`), cabe en el margen (`500`) o lo excede (`5000`)

| Regla | C1 afiliado | C2 mes completo | C3 cuota | IGSS | Bonificación | Préstamo | Líquido |
|---|---|---|---|---:|---:|---:|---:|
| R1 | Sí | Sí | Sin cuota | 231.84 | 250.00 | 0.00 | 4778.16 |
| R2 | Sí | Sí | Cabe | 231.84 | 250.00 | 500.00 | 4278.16 |
| R3 | Sí | Sí | Excede | 231.84 | 250.00 | 3338.16 | 1440.00 |
| R4 | Sí | No | Sin cuota | 231.84 | 125.00 | 0.00 | 4653.16 |
| R5 | Sí | No | Cabe | 231.84 | 125.00 | 500.00 | 4153.16 |
| R6 | Sí | No | Excede | 231.84 | 125.00 | 3213.16 | 1440.00 |
| R7 | No | Sí | Sin cuota | 0.00 | 250.00 | 0.00 | 5010.00 |
| R8 | No | Sí | Cabe | 0.00 | 250.00 | 500.00 | 4510.00 |
| R9 | No | Sí | Excede | 0.00 | 250.00 | 3570.00 | 1440.00 |
| R10 | No | No | Sin cuota | 0.00 | 125.00 | 0.00 | 4885.00 |
| R11 | No | No | Cabe | 0.00 | 125.00 | 500.00 | 4385.00 |
| R12 | No | No | Excede | 0.00 | 125.00 | 3445.00 | 1440.00 |

Lo que confirma la tabla, además de cada monto:

- **La bonificación queda fuera del IGSS y del ISR.** Entre R1 y R4, que solo cambian los días,
  el IGSS y el ISR no se mueven.
- **El préstamo se descuenta de último.** El préstamo recortado de R3, R6, R9 y R12 cambia
  según el IGSS y la bonificación, pero el líquido siempre termina en el piso de Q1440.

### 2.4 Particiones de la CLI

| ID | Caso | Entrada | Resultado esperado |
|---|---|---|---|
| CLI-01 | Falta `salario_base` | *(sin argumentos)* | Imprime el texto de uso; `main()` retorna `1` |
| CLI-02 | Ejemplo del README | `salario_base=4000 horas_extra=8 dias_trabajados=30 cuota_prestamo=500` | Imprime `Liquido: Q3747.14 \| Descuentos: Q702.86`; retorna `0` |
| CLI-03 | Solo salario, con los valores por defecto | `salario_base=4800` | Afiliado, 30 días, sin horas ni préstamo: `Liquido: Q4778.16 \| Descuentos: Q271.84` |
| CLI-04 | No afiliado | `salario_base=4800 afiliado_igss=no` | No descuenta IGSS: `Liquido: Q5010.0 \| Descuentos: Q40.0` |
| CLI-05 | `parse_args()` | `["salario_base=4800", "suelto", "afiliado_igss=no"]` | `{"salario_base": 4800.0, "afiliado_igss": "no"}`: el número pasa a `float`, el texto se queda como texto y lo que no trae `=` se ignora sin cortar la lectura de lo que sigue |
| CLI-06 | Ejecución como módulo (`python -m planilla.cli`) | Sin argumentos y con `salario_base=4800` | El proceso termina con código `1` y `0`: `sys.exit(main())` propaga lo que retorna `main()` |

Cálculo de CLI-02 a mano: valor hora 4000 / 240 × 1.5 × 8 = Q200 de horas extra; ordinario
Q4200; IGSS Q202.86; ISR Q0 (renta imponible 0); bonificación Q250; líquido antes Q4247.14;
piso Q1260, así que la cuota de Q500 cabe; líquido Q3747.14; descuentos 202.86 + 0 + 500 =
Q702.86.

## 3. Hallazgos

### Defectos contra el README

**Ninguno.** Además del cálculo a mano, se escribió aparte un oráculo que implementa solo las
reglas del README. Se comparó contra `liquidar()` en 7,644 combinaciones de entradas: todas las
fronteras de este documento y valores fuera de rango. Hubo 0 diferencias, lo que coincide con
lo que dice el README ("el código funciona y cumple las reglas").

### Observaciones (no son defectos: el README no las define)

| ID | Observación | Consecuencia para las pruebas |
|---|---|---|
| O1 | En `descuento_prestamo()`, la rama "sin margen" (`margen <= 0`) no se alcanza desde `liquidar()`. El IGSS (4.83%) más el ISR (menos del 7% del salario base) nunca bajan el líquido previo del 30% del ordinario. | EP-18 y BV-10 llaman la función directo. |
| O2 | En la CLI, solo `afiliado_igss=no` quita el IGSS. `afiliado_igss=false` o `afiliado_igss=0` cuentan como afiliado. | Se documenta; CLI-04 usa `no`. |
| O3 | En la CLI, una entrada inválida termina con traceback: `ValueError` con `salario_base=0`, `TypeError` con `salario_base=abc`. No hay mensaje amigable. | Se documenta; el README no pide manejo de errores en la CLI. |
| O4 | `resumen()` redondea con `round()`, así que imprime `Q5010.0` y no `Q5010.00`. | CLI-04 verifica el formato actual. |
| O5 | `ruff check .` reporta 10 findings (8 en `calculo.py`, 2 en `cli.py`). | Se corrigen en la fase 2 sin cambiar el comportamiento. Esta suite sirve como red para confirmarlo. |

## 4. Plan de implementación y trazabilidad

| Archivo de prueba | Casos | Código ejercitado | Defecto que detectaría |
|---|---|---|---|
| `tests/test_particiones.py` | EP-01 a EP-18 | Todas las reglas de `calculo.py` | Aceptar entradas fuera de rango; tasa, recargo o tramo equivocados; incluir la bonificación en el IGSS; no recortar el préstamo |
| `tests/test_fronteras.py` | BV-01 a BV-10 | `valor_hora()`, `pago_horas_extra()`, `bonificacion_incentivo()`, `descuento_isr()`, `descuento_prestamo()` | Comparaciones corridas por uno (`<` contra `<=`) en horas, días, tramos del ISR, cuota y piso |
| `tests/test_tabla_decision.py` | R1 a R12 | `liquidar()` | Descontar en otro orden, aplicar IGSS sin afiliación, calcular el piso sobre otra base |
| `tests/test_cli.py` | CLI-01 a CLI-06 | `parse_args()`, `main()`, `resumen()` | Código de salida incorrecto, argumentos mal interpretados, desglose mal sumado |

## 5. Coverage y efectividad de la suite

Comando (el mismo que corre el pipeline):

```bash
uv run pytest --cov=src/planilla --cov-branch --cov-report=term-missing --cov-report=html --cov-fail-under=95
```

| Suite | Sentencias | Ramas | Coverage total | Gate de 95 |
|---|---:|---:|---:|---|
| Solo reglas de negocio (sin `test_cli.py`) | 73 / 101 | 20 / 28 | 72% | Falla (tampoco llega a 80) |
| Suite completa (68 tests) | 101 / 101 | 28 / 28 | 100% | Pasa |

**Umbral: `--cov-fail-under=95` con coverage de ramas.** Justificación: la suite cubre hoy el
100% de sentencias y ramas, y 95 tolera un par de líneas defensivas sin cubrir, pero falla en
cuanto entra una regla nueva sin su test.

El gate cuenta todo `src/planilla`, incluida la CLI. Sin `tests/test_cli.py` el total baja a
72%, porque `cli.py` queda en 0% y `resumen()` sin ejecutar.

Coverage alto no garantiza que los tests detecten errores. Por eso se hizo además una prueba de
mutantes manual: se inyectaron 24 defectos, uno por uno, en una copia del código. Entre ellos:
cambiar la tasa del IGSS, usar `>=` en lugar de `>` en los límites de horas y días, meter la
bonificación en la base del IGSS, calcular el ISR sobre el ordinario, quitar el tope del
préstamo, invertir `afiliado_igss` en la CLI y no propagar el código de salida.

La primera corrida detectó 23. El que sobrevivió fue cambiar `continue` por `break` en
`parse_args()`, porque en CLI-05 el argumento sin `=` iba de último. Se movió al medio y la suite
quedó en **24/24 detectados**.
