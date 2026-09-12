# Entrega — Hoja de Trabajo 3

**Estudiante:** Juan Pablo Madriz — carné 20240841

**Fork:** https://github.com/Panito115/planilla-cd

## Evidencia del pipeline

| Run | Resultado | Commit (SHA) | URL del run |
|---|---|---|---|
| Rojo | ❌ failure | `2e5b241ebe5b39ebbd748394ac5bf8afccdebd11` | https://github.com/Panito115/planilla-cd/actions/runs/34718349855 |
| Verde | ✅ success | `4b4e6d5d32e4bb75f8f2ab22dc628ff5318e0325` | https://github.com/Panito115/planilla-cd/actions/runs/34718391229 |

**Qué se rompió en el run rojo.** En `pago_horas_extra()` la validación
`horas_extra > MAX_HORAS_EXTRA` se cambió a `>=`. Así se rechazan 48 horas extra, que el README
permite ("de 0 a 48 al mes"). Es el típico error de frontera por uno.

- `ruff check .` pasó.
- La suite detectó el defecto con el test de frontera BV-03:
  `FAILED tests/test_fronteras.py::test_horas_extra_dentro_del_rango[BV-03 48] - ValueError: horas extra fuera del rango permitido`.
- Resultado: 1 failed, 67 passed. El job terminó con código 1.

**Arreglo en el run verde.** Se revirtió la comparación a `>`. Pasaron `ruff` y los 68 tests,
con coverage de 100% sobre el gate de 95.

El pipeline se incorporó en el commit `dc318a42fcc026c3bafbad71a3cce5d7f55317d9`, que también
quedó en verde: https://github.com/Panito115/planilla-cd/actions/runs/34718282046

## Coverage gate

`--cov-fail-under=95`, con coverage de ramas sobre todo `src/planilla`.

> 95: la suite cubre hoy el 100% de sentencias y ramas; 95 tolera un par de líneas defensivas
> sin cubrir pero falla si entra una regla sin test.

Sin los tests de la CLI el total baja a 72%, así que el gate no se alcanza probando solo las
reglas de negocio. El detalle está en la sección 5 de `diseno-de-pruebas.md`.

## Cómo cumple el pipeline (`.github/workflows/ci.yml`)

| Requisito | Implementación |
|---|---|
| Dispara en `push` y `pull_request` contra `main` | `on.push.branches: [main]` y `on.pull_request.branches: [main]` |
| Corre `ruff check .` y la suite con coverage | Pasos `Ruff` y `Tests con coverage` (`pytest --cov=src/planilla --cov-branch --cov-fail-under=95`) |
| Cachea dependencias entre runs | `astral-sh/setup-uv` con `enable-cache: true`, llave sobre `uv.lock` y `cache-python: true`. Los runs rojo y verde muestran `Cache restored successfully` |
| Actions de terceros fijadas por hash | `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1` (v7.0.1), `astral-sh/setup-uv@bec219d24cd3e171d82865faccec33120bb574f4` (v10.1.0), `actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a` (v7.0.1) |

## Contenido del zip

- `ENTREGA.md`: este archivo, con la URL del fork y las URLs de los runs con su SHA.
- `htmlcov/`: reporte HTML de coverage. Es el artifact `coverage-html` descargado del run verde.
- `.git/`: historial completo del repositorio.
- Código, tests (`tests/`), workflow y `diseno-de-pruebas.md` (diseño de pruebas con particiones,
  fronteras y tabla de decisión).
