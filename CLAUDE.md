# **CLAUDE.md - IntelligentThermalPacer**

Directivas de ingeniería, estándares de desarrollo y comandos operativos para el proyecto IntelligentThermalPacer.

## **Arquitectura y Flujo de Trabajo**
* **Librería Cliente (`thermal_pacer/client.py`)**: Biblioteca ligera en Python. Expone el gestor de contexto `ThermalGuard` para limitar la concurrencia del cliente basándose en el pautado dinámico del demonio sobre el socket `/var/run/thermal_pacer.sock`.
* **Demonio Central (`thermal_pacer/daemon.py`)**: Demonio de fondo multi-hilo (`thermal_pacerd`). Monitorea la telemetría térmica cada 1 segundo en un hilo separado, almacena un historial deslizante (por defecto 180s) y expone la guía de pautado (`SCALE_UP`, `SCALE_DOWN`, `HOLD`) a los clientes activos. Gestiona estados de hardware de CPU/GPU y restaura automáticamente el estado de gobernadores al desconectarse el último cliente.
* **Calibrador de Hardware (`thermal_pacer/calibration.py`)**: Ejecuta pruebas de estrés en tres fases concurrentes para calibrar el comportamiento térmico óptimo.
* **CLI Operativo (`thermal_pacer/__main__.py`)**: Despachador principal para la instalación (`--install`), desinstalación (`--uninstall`), calibración (`--calibrate`) y restauración fuera de banda (`--restore-governors`).

## **Comandos de Verificación y Construcción**
* **Ejecutar Suite de Pruebas Unitarias**: `python3 -m unittest tests/test_thermal_pacer.py -v`
* **Compilación de Distribución Local**:
  * Wheel: `python3 setup.py bdist_wheel`
  * Tarball fuente: `python3 setup.py sdist`
* **Formateador e Inspección de Estilo (Ruff)**: `ruff check . --fix` y `ruff format .`
* **Análisis de Tipos Estáticos**: `mypy --strict thermal_pacer/`

## **Estándares de Codificación y Reglas Imperativas**
* **Tipado Estático Estricto (PEP 484)**: TODAS las firmas de funciones, métodos e inicializadores de variables DEBEN estar tipados de manera estricta. PROHIBIDO el uso de anotaciones dinámicas o el tipo genérico desestructurado `Any` sin justificación explícita.
* **Estilo de Docstrings (Google Style)**: Escribir docstrings descriptivos detallados para cada módulo, clase y función pública expuesta, especificando de forma clara `Args:`, `Returns:`, `Raises:` y `Example:`.
* **Restauración Absoluta de Estado**: Todo flujo en el demonio que altere el estado físico de la máquina (gobernadores de CPU scaling, boost, NVIDIA gpu) DEBE contar con un snapshot de respaldo persistido en `/var/run/thermal_pacer.governors.bak` y restaurar los valores iniciales de forma segura en caso de señal de interrupción o desconexión del cliente.
* **Precedencia de Estrategia 'eco'**: La estrategia `"eco"` siempre anula cualquier otra bandera de configuración del gobernador, forzando gobernadores `"powersave"` y desactivando el CPU boost.
* **Seguridad de Hilos**: El acceso a colas compartidas, contadores e identificadores de cliente (`client_count`) en el demonio DEBE estar debidamente protegido por un mutex de reentrada (`threading.Lock`).
