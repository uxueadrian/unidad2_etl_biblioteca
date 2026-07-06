# Unidad 2 - ETL Biblioteca Data Warehouse

## 1. Objetivo del proyecto

Este proyecto implementa un proceso ETL completo utilizando un dataset de préstamos de biblioteca.

El flujo del proceso es:
dataset CSV → limpieza → validación → ETL → Data Warehouse en MySQL → consultas de verificación → evidencias

El objetivo es practicar:
- Lectura de datasets con Pandas
- Limpieza y transformación de datos
- Validación de errores controlados
- Creación de un Data Warehouse en MySQL
- Carga de datos válidos
- Registro de errores
- Generación de bitácora de ejecución

---

## 2. Requisitos para ejecutar el proyecto

- Python 3.10 o superior
- MySQL instalado o acceso a servidor MySQL
- Librerías de Python:

```bash
pip install pandas sqlalchemy pymysql
```

---

## 3. Cómo crear la base de datos

Crea la base de datos `biblioteca_dw` manualmente desde MySQL o DataGrip:

```sql
CREATE DATABASE biblioteca_dw;
```

El script crea las tablas automáticamente al ejecutarse.

---

## 4. Cómo instalar librerías

Ejecuta el siguiente comando:

```bash
pip install pandas sqlalchemy pymysql
```

---

## 5. Cómo ejecutar el script

Ejecuta el ETL desde la raíz del proyecto:

```bash
python scripts/etl_biblioteca.py
```

El script:
- Lee el dataset desde `data/prestamos_biblioteca_100.csv`
- Limpia y transforma los datos
- Valida registros duplicados y total_multa incorrecto
- Carga datos válidos en el Data Warehouse
- Registra errores en `etl_errores`
- Genera bitácora en `etl_log`
- Produce el reporte en `evidencias/reporte_ejecucion.txt`

---

## 6. Resultado esperado

```
LEIDAS: 100
CARGADAS: 98
RECHAZADAS: 2
ESTADO: FINALIZADO_CON_ERRORES
```

Errores detectados:
- `id_prestamo 5099`: total_multa incorrecto (esperado 70, real 40)
- `id_prestamo 5002`: id_prestamo duplicado (segunda aparición rechazada)

La tabla `fact_prestamos` debe contener 98 registros.
La tabla `etl_errores` debe contener 2 registros.