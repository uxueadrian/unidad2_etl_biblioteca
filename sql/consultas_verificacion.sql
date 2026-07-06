-- 1. Cuantos registros hay en fact_prestamos
SELECT COUNT(*) AS total_fact_prestamos
FROM fact_prestamos;

-- 2. Cuantos errores hay
SELECT COUNT(*) AS total_errores
FROM etl_errores;

-- 3. Errores registrados
SELECT id_registro, descripcion_error, fecha_error
FROM etl_errores;

-- 4. Último estado del ETL
SELECT *
FROM etl_log
ORDER BY fecha_ejecucion DESC
LIMIT 1;

-- 5. Total de multas por carrera
SELECT c.carrera, SUM(f.total_multa) AS total_multa
FROM fact_prestamos f
JOIN dim_carrera c ON f.id_carrera = c.id_carrera
GROUP BY c.carrera;

-- 6. Total de multas por categoría de libro
SELECT l.categoria, SUM(f.total_multa) AS total_multa
FROM fact_prestamos f
JOIN dim_libro l ON f.id_libro = l.id_libro
GROUP BY l.categoria;

-- 7. Promedio de días de préstamo por sede
SELECT s.sede, AVG(f.dias_prestamo) AS promedio_dias
FROM fact_prestamos f
JOIN dim_sede s ON f.id_sede = s.id_sede
GROUP BY s.sede;

-- 8. Top 5 libros con mayor multa
SELECT l.libro, SUM(f.total_multa) AS total_multa
FROM fact_prestamos f
JOIN dim_libro l ON f.id_libro = l.id_libro
GROUP BY l.libro
ORDER BY total_multa DESC
LIMIT 5;

-- 9. Detalle de préstamos
SELECT 
    f.id_prestamo,
    fe.fecha,
    a.alumno,
    c.carrera,
    l.libro,
    l.categoria,
    s.sede,
    f.total_multa
FROM fact_prestamos f
JOIN dim_fecha fe ON f.id_fecha = fe.id_fecha
JOIN dim_alumno a ON f.id_alumno = a.id_alumno
JOIN dim_carrera c ON f.id_carrera = c.id_carrera
JOIN dim_libro l ON f.id_libro = l.id_libro
JOIN dim_sede s ON f.id_sede = s.id_sede;

-- 10. Conteo de préstamos por sede
SELECT s.sede, COUNT(*) AS total_prestamos
FROM fact_prestamos f
JOIN dim_sede s ON f.id_sede = s.id_sede
GROUP BY s.sede;