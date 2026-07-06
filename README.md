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