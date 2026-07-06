import pandas as pd
from pathlib import Path
from sqlalchemy import create_engine, text
from datetime import datetime
import os

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_PATH = BASE_DIR / "data" / "prestamos_biblioteca_100.csv"

engine = create_engine("mysql+pymysql://root:root@localhost:3306/biblioteca_dw")


def leer_dataset():
    return pd.read_csv(CSV_PATH)


def limpiar_datos(df):
    df = df.copy()
    df.columns = df.columns.str.strip().str.lower()

    cols_txt = ["alumno", "carrera", "libro", "categoria", "sede"]
    for c in cols_txt:
        df[c] = df[c].astype(str).str.strip()

    df["fecha_prestamo"] = pd.to_datetime(df["fecha_prestamo"])

    for c in ["dias_prestamo", "multa_diaria", "total_multa"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    return df


def validar_datos(df):
    validos = []
    errores = []
    vistos = set()

    for i, row in df.iterrows():
        idp = row["id_prestamo"]
        fila_csv = i + 2
        datos = ",".join(str(x) for x in row.values)

        if idp in vistos:
            errores.append({
                "fecha_error": datetime.now(),
                "archivo_origen": "prestamos_biblioteca_100.csv",
                "fila_csv": fila_csv,
                "id_registro": idp,
                "descripcion_error": "id_prestamo duplicado",
                "datos_originales": datos
            })
            continue

        esperado = row["dias_prestamo"] * row["multa_diaria"]

        if row["total_multa"] != esperado:
            errores.append({
                "fecha_error": datetime.now(),
                "archivo_origen": "prestamos_biblioteca_100.csv",
                "fila_csv": fila_csv,
                "id_registro": idp,
                "descripcion_error": "total_multa incorrecto",
                "datos_originales": datos
            })
            continue

        vistos.add(idp)
        validos.append(row)

    return pd.DataFrame(validos), errores


def crear_tablas():
    sqls = [
        """CREATE TABLE IF NOT EXISTS dim_alumno (
            id_alumno INT AUTO_INCREMENT PRIMARY KEY,
            alumno VARCHAR(100) UNIQUE
        )""",
        """CREATE TABLE IF NOT EXISTS dim_carrera (
            id_carrera INT AUTO_INCREMENT PRIMARY KEY,
            carrera VARCHAR(100) UNIQUE
        )""",
        """CREATE TABLE IF NOT EXISTS dim_libro (
            id_libro INT AUTO_INCREMENT PRIMARY KEY,
            libro VARCHAR(200),
            categoria VARCHAR(100),
            UNIQUE(libro, categoria)
        )""",
        """CREATE TABLE IF NOT EXISTS dim_sede (
            id_sede INT AUTO_INCREMENT PRIMARY KEY,
            sede VARCHAR(100) UNIQUE
        )""",
        """CREATE TABLE IF NOT EXISTS dim_fecha (
            id_fecha INT PRIMARY KEY,
            fecha DATE UNIQUE,
            anio INT,
            mes INT,
            dia INT
        )""",
        """CREATE TABLE IF NOT EXISTS fact_prestamos (
            id_prestamo INT PRIMARY KEY,
            id_fecha INT,
            id_alumno INT,
            id_carrera INT,
            id_libro INT,
            id_sede INT,
            dias_prestamo INT,
            multa_diaria DECIMAL(10,2),
            total_multa DECIMAL(10,2)
        )""",
        """CREATE TABLE IF NOT EXISTS etl_errores (
            id_error INT AUTO_INCREMENT PRIMARY KEY,
            fecha_error DATETIME,
            archivo_origen VARCHAR(255),
            fila_csv INT,
            id_registro INT,
            descripcion_error VARCHAR(255),
            datos_originales TEXT
        )""",
        """CREATE TABLE IF NOT EXISTS etl_log (
            id_log INT AUTO_INCREMENT PRIMARY KEY,
            fecha_ejecucion DATETIME,
            archivo_origen VARCHAR(255),
            filas_leidas INT,
            filas_cargadas INT,
            filas_rechazadas INT,
            estado VARCHAR(50)
        )"""
    ]

    with engine.begin() as conn:
        for s in sqls:
            conn.execute(text(s))


def limpiar_tablas():
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM fact_prestamos"))
        conn.execute(text("DELETE FROM dim_alumno"))
        conn.execute(text("DELETE FROM dim_carrera"))
        conn.execute(text("DELETE FROM dim_libro"))
        conn.execute(text("DELETE FROM dim_sede"))
        conn.execute(text("DELETE FROM dim_fecha"))
        conn.execute(text("DELETE FROM etl_errores"))


def cargar_dimensiones(df):
    with engine.begin() as conn:

        for _, r in df[["alumno"]].drop_duplicates().iterrows():
            conn.execute(text("INSERT IGNORE INTO dim_alumno(alumno) VALUES (:a)"), {"a": r["alumno"]})

        for _, r in df[["carrera"]].drop_duplicates().iterrows():
            conn.execute(text("INSERT IGNORE INTO dim_carrera(carrera) VALUES (:c)"), {"c": r["carrera"]})

        for _, r in df[["libro", "categoria"]].drop_duplicates().iterrows():
            conn.execute(
                text("INSERT IGNORE INTO dim_libro(libro,categoria) VALUES (:l,:c)"),
                {"l": r["libro"], "c": r["categoria"]}
            )

        for _, r in df[["sede"]].drop_duplicates().iterrows():
            conn.execute(text("INSERT IGNORE INTO dim_sede(sede) VALUES (:s)"), {"s": r["sede"]})

        for _, r in df[["fecha_prestamo"]].drop_duplicates().iterrows():
            fecha = r["fecha_prestamo"]
            conn.execute(
                text("""INSERT IGNORE INTO dim_fecha(id_fecha,fecha,anio,mes,dia)
                        VALUES (:id,:f,:a,:m,:d)"""),
                {
                    "id": int(fecha.strftime("%Y%m%d")),
                    "f": fecha.date(),
                    "a": fecha.year,
                    "m": fecha.month,
                    "d": fecha.day
                }
            )


def cargar_fact(df):
    with engine.begin() as conn:

        dims_a = pd.read_sql("SELECT * FROM dim_alumno", conn)
        dims_c = pd.read_sql("SELECT * FROM dim_carrera", conn)
        dims_l = pd.read_sql("SELECT * FROM dim_libro", conn)
        dims_s = pd.read_sql("SELECT * FROM dim_sede", conn)

        map_a = dict(zip(dims_a["alumno"], dims_a["id_alumno"]))
        map_c = dict(zip(dims_c["carrera"], dims_c["id_carrera"]))
        map_s = dict(zip(dims_s["sede"], dims_s["id_sede"]))
        map_l = dict(zip(zip(dims_l["libro"], dims_l["categoria"]), dims_l["id_libro"]))

        for _, r in df.iterrows():
            conn.execute(
                text("""INSERT INTO fact_prestamos VALUES
                (:id,:f,:a,:c,:l,:s,:d,:m,:t)"""),
                {
                    "id": int(r["id_prestamo"]),
                    "f": int(r["fecha_prestamo"].strftime("%Y%m%d")),
                    "a": map_a[r["alumno"]],
                    "c": map_c[r["carrera"]],
                    "l": map_l[(r["libro"], r["categoria"])],
                    "s": map_s[r["sede"]],
                    "d": int(r["dias_prestamo"]),
                    "m": float(r["multa_diaria"]),
                    "t": float(r["total_multa"])
                }
            )


def cargar_errores(errores):
    with engine.begin() as conn:
        for e in errores:
            conn.execute(
                text("""INSERT INTO etl_errores
                (fecha_error,archivo_origen,fila_csv,id_registro,descripcion_error,datos_originales)
                VALUES (:f,:a,:fila,:id,:d,:data)"""),
                {
                    "f": e["fecha_error"],
                    "a": e["archivo_origen"],
                    "fila": e["fila_csv"],
                    "id": e["id_registro"],
                    "d": e["descripcion_error"],
                    "data": e["datos_originales"]
                }
            )


def cargar_log(leidas, cargadas, rechazadas, estado):
    with engine.begin() as conn:
        conn.execute(
            text("""INSERT INTO etl_log
            (fecha_ejecucion,archivo_origen,filas_leidas,filas_cargadas,filas_rechazadas,estado)
            VALUES (:f,:a,:l,:c,:r,:e)"""),
            {
                "f": datetime.now(),
                "a": "prestamos_biblioteca_100.csv",
                "l": leidas,
                "c": cargadas,
                "r": rechazadas,
                "e": estado
            }
        )


def generar_reporte(leidas, cargadas, rechazadas, estado, errores):
    os.makedirs("evidencias", exist_ok=True)
    path = "evidencias/reporte_ejecucion.txt"

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"FILAS LEIDAS: {leidas}\n")
        f.write(f"FILAS CARGADAS: {cargadas}\n")
        f.write(f"FILAS RECHAZADAS: {rechazadas}\n")
        f.write(f"ESTADO: {estado}\n\n")
        for e in errores:
            f.write(f"{e['id_registro']} - {e['descripcion_error']}\n")

    return path


def main():
    df = leer_dataset()
    df = limpiar_datos(df)

    crear_tablas()
    limpiar_tablas()

    validos, errores = validar_datos(df)

    cargar_dimensiones(validos)
    cargar_fact(validos)
    cargar_errores(errores)

    estado = "FINALIZADO_CON_ERRORES" if len(errores) > 0 else "FINALIZADO"

    cargar_log(len(df), len(validos), len(errores), estado)

    print("LEIDAS:", len(df))
    print("CARGADAS:", len(validos))
    print("RECHAZADAS:", len(errores))
    print("ESTADO:", estado)

    generar_reporte(len(df), len(validos), len(errores), estado, errores)


if __name__ == "__main__":
    main()