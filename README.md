# Laboratorio de transformaciones lineales

Aplicación de escritorio para analizar transformaciones entre espacios reales, evaluar vectores y visualizar figuras en el plano. Utiliza Tkinter, SymPy y Matplotlib.

## Ejecución

Se necesita Python 3 con Tkinter disponible y un entorno gráfico. Desde la carpeta del proyecto:

```sh
python -m venv .venv
```

Esto crea un entorno virtual local. Instala allí las dependencias:

```sh
.venv/bin/python -m pip install -r requirements.txt
```

Ejecuta la aplicación:

```sh
.venv/bin/python transformaciones_lineales.py
```

En Arch Linux, Tkinter se proporciona mediante el paquete `tk`; si no está disponible, revisa la instalación de Python y Tk antes de ejecutar la aplicación. El entorno virtual se puede eliminar borrando `.venv`.

## Uso

Selecciona la dimensión de entrada y escribe las componentes separadas por comas, por ejemplo `2*x + y, 3*y`. Usa `x`, `y` y, en dimensión 3, `z`. Se admiten potencias como `x^2` y funciones como `sqrt`, `sin`, `cos`, `Abs`, `exp` y `log`.

Introduce el vector separado por comas y, para una figura en el plano, los vértices separados por punto y coma; por ejemplo `0,0; 2,3; 4,0`. La figura es opcional. Los ejemplos de la lista permiten probar transformaciones lineales y no lineales.

La gráfica es una aproximación del contorno transformado, no una representación de todos los puntos interiores. Las expresiones con singularidades o dominios difíciles pueden requerir análisis adicional; no interpretes una simplificación simbólica como prueba de que una fórmula está definida en todos los puntos.

## Pruebas

```sh
.venv/bin/python -m unittest discover -s tests
```

Este comando ejecuta las pruebas automatizadas; no modifica el código del proyecto. No sustituye una comprobación manual de la interfaz gráfica.

## Crear la aplicación distribuible

PyInstaller debe ejecutarse en el sistema de destino: genera la versión Linux en Linux y la versión Windows en Windows. Usa Python de la misma arquitectura que los equipos de destino. Se distribuye **toda la carpeta** generada, no únicamente el ejecutable.

### Arch Linux

Con el entorno virtual creado como se indica arriba, instala las dependencias de compilación dentro de `.venv`:

```sh
.venv/bin/python -m pip install -r requirements-build.txt
```

Genera la aplicación:

```sh
.venv/bin/python -m PyInstaller --noconfirm --clean --windowed --onedir --name LaboratorioTransformaciones transformaciones_lineales.py
```

El resultado está en `dist/LaboratorioTransformaciones/`. Para abrirlo:

```sh
./dist/LaboratorioTransformaciones/LaboratorioTransformaciones
```

Comprueba el resultado en el equipo donde se vaya a usar: un ejecutable generado en Arch no garantiza compatibilidad con cualquier distribución o versión de Linux.

### Windows

Instala Python para Windows con Tkinter (incluido normalmente en el instalador oficial) y abre PowerShell en la carpeta del proyecto. Crea un entorno virtual independiente del de Linux:

```powershell
py -m venv .venv-windows
```

```powershell
.\.venv-windows\Scripts\python.exe -m pip install -r requirements-build.txt
```

```powershell
.\.venv-windows\Scripts\python.exe -m PyInstaller --noconfirm --clean --windowed --onedir --name LaboratorioTransformaciones transformaciones_lineales.py
```

Abre `dist\LaboratorioTransformaciones\LaboratorioTransformaciones.exe`. Para distribuirlo, comprime y entrega la carpeta `dist\LaboratorioTransformaciones` completa. Prueba el resultado en Windows antes de distribuirlo.

También puedes generar la versión Windows mediante GitHub Actions sin tener Windows instalado:

1. En GitHub abre la pestaña **Actions** del repositorio y selecciona **Compilar aplicación para Windows**.
2. Selecciona **Run workflow** y ejecuta el flujo en la rama deseada. También se ejecuta automáticamente con cada push a `main`.
3. Cuando termine correctamente, abre la ejecución y descarga el artefacto **LaboratorioTransformaciones-Windows**.
4. Descomprime el archivo descargado y ejecuta `LaboratorioTransformaciones.exe`. Conserva el resto de archivos y carpetas junto al ejecutable.

El artefacto de Actions tiene un periodo de retención limitado y no sustituye una publicación permanente en Releases. Prueba el ejecutable en Windows antes de distribuirlo.

PyInstaller también crea `build/` y un archivo `.spec`; son productos de compilación y se pueden borrar junto con `dist/` para deshacer el empaquetado. Los entornos `.venv` y `.venv-windows` también se pueden eliminar si ya no se necesitan.

## Créditos

Creado por Jose David Palacios, estudiante de Ingeniería en Sistemas — Univalle.
