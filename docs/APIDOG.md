# Probar SmartConnect en Apidog

## Preparación

1. Ejecutar migraciones, cargar los datos y mantener `runserver` abierto siguiendo README.md.
2. Crear un proyecto en Apidog.
3. Abrir `Settings > Import Data`, o la opción de importación del proyecto.
4. Elegir Postman y subir `SmartConnect.postman_collection.json`, formato v2.1.
5. Revisar las variables importadas. `base_url` debe ser `http://127.0.0.1:8000`. Si el puerto es otro, cambiarlo.
6. Ejecutar las 18 peticiones en orden. Usar el servidor local real, no una URL de Mock.

La colección incluye scripts que comprueban el estado y guardan los ID creados como `persona_id` y `terreno_id`. Si su versión o configuración de importación no conserva esos scripts o variables, copien manualmente los ID de las respuestas POST y definan las dos variables en el entorno de Apidog. En los cuerpos JSON, administrador debe enviarse como número.

La importación y los scripts deben comprobarse en su instalación de Apidog. Las pruebas automáticas incluidas verifican las peticiones contra Django, no el funcionamiento de la interfaz de Apidog.

## JSON de ejemplo

POST `http://127.0.0.1:8000/api/personas/`

Headers: `Content-Type: application/json` y `Accept: application/json`.

```json
{
  "codigo": "PER-PRUEBA",
  "nombres": "Camila",
  "apellidos": "Perez",
  "email": "camila.prueba@example.com"
}
```

Debe responder 201 y entregar un `id`. Guárdenlo como `persona_id`.

POST `http://127.0.0.1:8000/api/terrenos/`

```json
{
  "codigo": "TER-PRUEBA",
  "nombre": "Conjunto de prueba",
  "direccion": "Pasaje Ficticio 500",
  "administrador": 3
}
```

El valor 3 es solo un ejemplo: sustitúyanlo por el ID real de la persona que crearon. Debe responder 201. Guarden el `id` del terreno como `terreno_id`. El campo de respuesta `administrador_nombre` es de solo lectura y no necesitan enviarlo.

## Secuencia guardada

| N.º | Acción | Estado esperado |
| --- | --- | --- |
| 01 | GET personas | 200 |
| 02 | POST persona de prueba, guardar ID | 201 |
| 03 | GET detalle de esa persona | 200 |
| 04 | PUT con todos sus campos de entrada | 200 |
| 05 | PATCH únicamente de nombres | 200 |
| 06 | POST con código de persona repetido | 400 |
| 07 | POST con correo inválido | 400 |
| 08 | GET terrenos | 200 |
| 09 | POST terreno relacionado, guardar ID | 201 |
| 10 | GET detalle de ese terreno | 200 |
| 11 | PUT con todos los campos de entrada del terreno | 200 |
| 12 | PATCH únicamente de dirección | 200 |
| 13 | POST terreno con administrador inexistente | 400 |
| 14 | DELETE de la persona que aún administra ese terreno | 409 |
| 15 | DELETE del terreno de práctica | 204 sin cuerpo |
| 16 | GET del terreno ya eliminado | 404 |
| 17 | DELETE de la persona de práctica | 204 sin cuerpo |
| 18 | GET de la persona ya eliminada | 404 |

Después de completar la secuencia, los datos de demostración originales deben seguir ahí. Si una ejecución quedó a medias, revisen los registros `PER-PRUEBA` y `TER-PRUEBA` antes de repetirla. No borren la BD como solución rutinaria.

## Qué guardar como evidencia

Por cada integrante: peticiones guardadas de su CRUD, estado HTTP y JSON visible para creación, lectura y modificación, y estado 204 al borrar seguido de GET 404. Para la relación, mostrar que `administrador` coincide con un ID existente y que `administrador_nombre` muestra a esa persona. Añadir un error 400 y explicar el motivo.

Antes de las eliminaciones pueden detener y reiniciar el servidor y repetir el GET para demostrar persistencia. Registrar capturas reales con nombres y fecha de su ejecución. No se incluyen capturas simuladas.

Referencia de importación: https://docs.apidog.com/import-from-postman-635043m0
