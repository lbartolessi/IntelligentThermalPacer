# IntelligentThermalPacer

Librería cliente y demonio de fondo en Python para la monitorización de temperatura, pautado dinámico de concurrencia y prevención proactiva de degradación térmica (*thermal throttling*) en Linux.

---

## Características Principales
* **Pautado Térmico Dinámico**: Pauta las cargas de trabajo hilos/procesos concurrentes añadiendo pausas proporcionales (*sleeps*) cuando la temperatura supera el límite de seguridad.
* **Control de Concurrencia de la Aplicación**: Los hilos clientes pueden consultar si deben reducir la concurrencia (`SCALE_DOWN`), expandirse (`SCALE_UP`), o mantenerse estables (`HOLD`) basándose en análisis estadísticos deslizantes de 180 segundos en el demonio.
* **Restauración Absoluta de Estado**: El demonio guarda un backup de la configuración física de hardware del procesador (gobernadores de CPU scaling y CPU boost de AMD/Intel) y los restaura de manera segura en cuanto el último cliente se desconecta o si ocurre un apagado catastrófico del servicio (OOB).
* **Instalación Systemd Nativa**: Script CLI de instalación automatizada con soporte para socket activation de systemd (el socket de UNIX `/var/run/thermal_pacer.sock` gestiona el arranque a demanda del servicio).

---

## Estructura del Repositorio
* `thermal_pacer/client.py`: Implementación del cliente y gestor de contexto `ThermalGuard`.
* `thermal_pacer/daemon.py`: Motor del demonio, hilos de telemetría, lectura de sensores CPU/GPU (a través de `psutil` y `pynvml`), y sockets de comunicación.
* `thermal_pacer/calibration.py`: Calibrador de estrés de tres fases con POSIX file-locks.
* `thermal_pacer/__main__.py`: CLI de administración del paquete.
* `tests/test_thermal_pacer.py`: Suite completa de pruebas unitarias y de integración determinista de rampa térmica.

---

## 1. Compilación y Construcción del Paquete
Para compilar localmente las distribuciones fuente y binaria (wheel) del paquete desde la raíz del proyecto, ejecuta:

```bash
# Compilar wheel (binario de distribución)
python3 setup.py bdist_wheel

# Compilar sdist (paquete de distribución fuente)
python3 setup.py sdist
```

Esto generará los entregables listos en la carpeta `dist/`:
* `dist/intelligent_thermal_pacer-1.0.0-py3-none-any.whl`
* `dist/intelligent_thermal_pacer-1.0.0.tar.gz`

---

## 2. Instalación

### Instalación Local
Para instalar el paquete wheel compilado de manera local en tu entorno de desarrollo o sistema de producción:

```bash
pip install dist/intelligent_thermal_pacer-1.0.0-py3-none-any.whl
```

### Instalación Directa desde GitHub (Ideal para dependencias en otras aplicaciones)
Puedes añadir este proyecto directamente como dependencia en el archivo `requirements.txt` o `pyproject.toml` de otra aplicación de software o instalarlo en línea desde consola:

```bash
# Instalación directa desde la rama principal (main/master) de GitHub
pip install git+https://github.com/tu-usuario/IntelligentThermalPacer.git
```

Si usas un archivo `requirements.txt` en tu otro repositorio, añade la siguiente línea:
```text
intelligent-thermal-pacer @ git+https://github.com/tu-usuario/IntelligentThermalPacer.git
```

---

## 3. Preparación e Instalación en el Sistema

### Paso 1: Ejecutar la Calibración de Hardware
Para detectar los parámetros térmicos idóneos en tu hardware (matrices de cómputo puro, escrituras concurridas de I/O y estrés mixto), ejecuta la herramienta de calibración con permisos de administrador:

```bash
sudo python3 -m thermal_pacer --calibrate
```
La herramienta generará un archivo de configuración recomendado en `/etc/thermal_pacer/thermal_config.json`.

### Paso 2: Instalar y Activar el Demonio de Systemd
Para instalar las plantillas de servicios del sistema, configurar los sockets UNIX y habilitar el demonio con persistencia, ejecuta:

```bash
sudo python3 -m thermal_pacer --install
```

Esto copiará las plantillas correspondientes a `/etc/systemd/system/` y habilitará el socket `/var/run/thermal_pacer.sock` controlado por systemd.

Para desinstalar de forma limpia el demonio y eliminar los archivos del sistema:
```bash
sudo python3 -m thermal_pacer --uninstall
```

---

## 4. Ejemplos de Uso e Integración

### Integración en la Aplicación Cliente
En tu aplicación intensiva de procesamiento de datos u otros flujos concurrentes, importa `ThermalGuard` para rodear el procesamiento pesado de tareas:

```python
import time
from thermal_pacer.client import ThermalGuard

def procesar_lote_de_datos(lote):
    # Simula carga intensiva
    pass

# Inicializa el cliente apuntando al socket del demonio
with ThermalGuard(socket_path="/var/run/thermal_pacer.sock") as guard:
    for lote in lista_de_lotes:
        # 1. Invocación de control de paso
        # Si el demonio detecta sobrecalentamiento crítico, guard.pace()
        # detendrá la ejecución del hilo durante unos milisegundos de forma transparente.
        guard.pace()
        
        # 2. Procesamiento de la tarea pesada
        procesar_lote_de_datos(lote)
```

### Escalabilidad Dinámica de Hilos (Guidance)
Si tu aplicación utiliza un pool de hilos dinámicos para procesar tareas en paralelo, puedes ajustar el número de hilos consultando la guía del demonio de fondo:

```python
with ThermalGuard() as guard:
    while procesando_tareas:
        # Obtiene la directiva del demonio
        guidance = guard.get_concurrency_guidance()
        
        if guidance == "SCALE_DOWN":
            # Reduce la concurrencia del pool de hilos (por ejemplo, apagar un hilo de trabajo)
            ajustar_pool_trabajadores(decremento=1)
        elif guidance == "SCALE_UP":
            # El procesador está frío y estable: añade un hilo para acelerar el procesamiento
            ajustar_pool_trabajadores(incremento=1)
        elif guidance == "HOLD":
            # Temperatura adecuada y estable; mantiene el pool sin cambios
            pass
        
        # Procesar lote de trabajo
        ejecutar_siguiente_tarea()
```
