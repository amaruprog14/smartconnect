# SmartConnect · Entrega 2 · Login JWT y segundo avance

API REST local para SmartConnect (Programación Back End, TI3041). Usa Django 5.2, Django REST Framework 3.16, Simple JWT y SQLite.

Los nombres reales de los integrantes, el repositorio, los PR y las capturas de Apidog deben aportarlos ustedes. Este material no acredita participación individual ni que una prueba se haya hecho en Apidog.

## 1. Qué incluye esta entrega

| Requisito | Dónde está |
| --- | --- |
| Cuatro CRUD maestros | `/api/personas/`, `/api/terrenos/`, `/api/viviendas/` y `/api/puntos-acceso/` |
| Operación del negocio con reglas comprobables | `POST /api/viviendas/{id}/participaciones/`: asigna una persona a una vivienda con su rol |
| Login JWT con renovación | `POST /api/token/` y `POST /api/token/refresh/` |
| Permisos por alcance (401 y 403) | `config/permissions.py` |
| ER actualizado | Carpeta [`er/`](er/) y sección 10 |
| Datos ficticios y cuentas de prueba | `manage.py cargar_demo` |
| Colección de Apidog | [`apidog/SmartConnect.postman_collection.json`](apidog/SmartConnect.postman_collection.json) |

| Responsable propuesto | Módulo | URL local |
| --- | --- | --- |
| Integrante 1 | Personas y Viviendas | `http://127.0.0.1:8000/api/personas/` y `/api/viviendas/` |
| Integrante 2 | Terrenos y Puntos de acceso | `http://127.0.0.1:8000/api/terrenos/` y `/api/puntos-acceso/` |

Ajusten esta distribución a la que realmente usen.

## 2. Requisitos en Windows

- Python 3.12 o superior, disponible como `py` (el proyecto se probó con Python 3.14).
- Git, un editor como VS Code y Apidog.
- Opcional: [Graphviz](https://graphviz.org/download/), solo para regenerar las imágenes del ER.

```powershell
py --version
```

## 3. Instalación, migraciones y datos de prueba

En PowerShell, dentro de la carpeta que contiene `manage.py`, ejecuten cada línea por separado:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py cargar_demo
.\.venv\Scripts\python.exe manage.py runserver
```

Se usa directamente el Python del entorno, así que no hace falta activar `.venv` ni cambiar la política de ejecución de PowerShell.

1. `venv` crea un entorno de paquetes propio del proyecto.
2. `pip install` instala Django, DRF y Simple JWT según `requirements.txt`.
3. `migrate` aplica las migraciones incluidas y crea o actualiza `db.sqlite3`.
4. `cargar_demo` crea o actualiza los datos ficticios y las cuentas de prueba. Se puede repetir sin duplicar datos: vuelve a dejar los valores y la contraseña de demostración.
5. `runserver` inicia la API en `http://127.0.0.1:8000`. Dejen esa terminal abierta; se detiene con `Ctrl+C`.

**Si ya tenían la base de la entrega 1:** después de `git pull`, vuelvan a ejecutar `pip install -r requirements.txt`, `migrate` y `cargar_demo`. Las migraciones nuevas cambian los `id` a `int`, agregan Vivienda, PuntoAcceso, ParticipacionVivienda y el vínculo entre Persona y la cuenta de usuario.

Las migraciones ya vienen incluidas. Si modifican modelos, ejecuten `manage.py makemigrations` y luego `manage.py migrate`, e incluyan los archivos de migración en el commit.

## 4. Cuentas y datos de prueba

Todas las cuentas de `cargar_demo` usan la contraseña **`Demo1234!`**. Es solo para localhost; no la reutilicen en otro lugar.

| Usuario | Persona | Qué permite demostrar |
| --- | --- | --- |
| `staff` | (sin persona) | `is_staff`: acceso completo a los maestros; único que asigna `PROPIETARIO_ADMIN`. También entra a `/admin/` |
| `ana` | Ana Rojas (PER-001) | Administra dos terrenos: TER-001 y TER-002 |
| `diego` | Diego Soto (PER-002) | Administra TER-003, es `PROPIETARIO_ADMIN` de Casa 1 (TER-001) y arrienda Casa 5 (TER-002) |
| `sofia` | Sofia Vidal (PER-005) | Persona sin terrenos ni viviendas: listados vacíos y 403 al escribir |

| Escenario del enunciado | Datos de `cargar_demo` |
| --- | --- |
| Una persona administra varios terrenos | Ana administra TER-001 y TER-002 |
| Una persona tiene viviendas en dos terrenos | Carla Fuentes: arrendataria en Casa 1 (TER-001) y propietaria en Depto 101 (TER-003) |
| Propietario administrador con arrendatario y conviviente | Casa 1: Diego `PROPIETARIO_ADMIN`, Carla `ARRENDATARIO` y Pedro Lagos `CONVIVIENTE` |
| Administrar un terreno y arrendar en otro | Diego administra TER-003 y es arrendatario en TER-002 |
| Accesos comunes y privados | TER-001: Porton principal y Puerta peatonal (comunes) y Puerta Casa 1 (de Casa 1). TER-003: Porton El Bosque |

Las cuentas se crean con `set_password`, que guarda la contraseña cifrada. Para vincular otra cuenta a una persona, usen Django Admin (`http://127.0.0.1:8000/admin/`, con `staff`): en Personas, campo **Usuario**.

Los `id` dependen de la BD. Revisen los reales con un GET; no supongan que siempre son 1, 2, 3.

## 5. Obtener y usar el token JWT

Toda la API exige un token, salvo las dos rutas de token. Sin token, o con uno inválido o vencido, la respuesta es **401**.

1. **Login.** `POST http://127.0.0.1:8000/api/token/` con body JSON:

   ```json
   {"username": "ana", "password": "Demo1234!"}
   ```

   Responde 200 con `access` y `refresh`.

2. **Usar el access.** En cada petición protegida agreguen el header:

   ```text
   Authorization: Bearer <access>
   ```

3. **Renovar.** Cuando el access venza (30 minutos), `POST http://127.0.0.1:8000/api/token/refresh/` con:

   ```json
   {"refresh": "<refresh>"}
   ```

   Responde 200 con un `access` nuevo. El refresh dura 1 día; después hay que volver a hacer login.

En Apidog, la colección ya hace esto: la petición de login guarda `access` y `refresh` en variables y las demás envían `Authorization: Bearer {{access}}`. Para probar a mano, creen una petición `POST {{base_url}}/api/token/`, copien el `access` de la respuesta y péguenlo en el header `Authorization` como `Bearer <access>` (o en la pestaña Auth, tipo Bearer Token).

La interfaz web de DRF en el navegador no envía el token, por lo que ahí verán 401. Usen Apidog para las pruebas.

## 6. Probar en Apidog

1. Ejecuten `migrate` y `cargar_demo`, y dejen `runserver` abierto.
2. En Apidog: `Settings > Import Data` (o la importación del proyecto), elijan **Postman** y suban `apidog/SmartConnect.postman_collection.json` (formato v2.1).
3. Revisen las variables importadas: `base_url` debe ser `http://127.0.0.1:8000`. Usen el servidor local real, no una URL de Mock.
4. Ejecuten las carpetas en orden. Cada descripción indica el estado esperado (`Estado esperado: 200.`).

| Carpeta | Qué demuestra | Estados |
| --- | --- | --- |
| 1. Autenticación JWT | Login de `staff` (guarda `access` y `refresh`), renovación, 401 sin token o con clave incorrecta, y login de `ana`, `diego` y `sofia` | 200, 401 |
| 2. Personas | CRUD como staff; Ana y Sofia ven solo su propia persona | 200, 201, 400 |
| 3. Terrenos | CRUD como staff, 409 al eliminar a un administrador y reasignación del terreno a Ana | 200, 201, 400, 409 |
| 4. Viviendas | CRUD como Ana, administradora del terreno de prueba; identificador repetido y Sofia sin permiso | 200, 201, 400, 403 |
| 5. Puntos de acceso | CRUD como Ana, punto común y de vivienda, vivienda de otro terreno | 200, 201, 400 |
| 6. Operación | Diego asigna una arrendataria (201); duplicado (400); Ana, Diego con `PROPIETARIO_ADMIN` y Sofia rechazados (403) | 200, 201, 400, 403 |
| 7. Permisos fuera del alcance | Terreno, vivienda y persona ajenos; Ana no elimina terrenos; Sofia ve una lista vacía | 200, 403 |
| 8. Limpieza | 409 por datos relacionados, eliminación de lo creado y 404 al consultarlo | 204, 404, 409 |

La colección guarda los `id` que necesita: `ana_persona_id` y `sofia_persona_id` (cada usuario ve solo su persona), `vivienda_demo_id` (la primera vivienda que ve Diego, Casa 1 de TER-001) y los `id` de lo que crea. Al terminar, los datos de `cargar_demo` quedan como estaban.

Si su versión de Apidog no conserva los scripts o las variables al importar, copien manualmente `access` y los `id` de las respuestas a las variables del entorno. En los cuerpos JSON, los `id` se envían como números.

**Evidencia sugerida:** login y renovación con su respuesta; un 401 y un 403; la operación válida y sus rechazos, con el GET posterior que muestra que los rechazos no se guardaron; un CRUD completo por integrante. Pueden reiniciar `runserver` y repetir un GET para demostrar persistencia. Registren capturas reales de su ejecución.

## 7. Endpoints

| Método y ruta | Qué hace |
| --- | --- |
| `POST /api/token/` | Login: entrega `access` y `refresh` |
| `POST /api/token/refresh/` | Entrega un `access` nuevo |
| `GET, POST /api/personas/` | Listar y crear personas |
| `GET, PUT, PATCH, DELETE /api/personas/{id}/` | Detalle, actualizar y eliminar |
| `GET, POST /api/terrenos/` y `/api/terrenos/{id}/` | CRUD de terrenos (`administrador` es el `id` de una persona) |
| `GET, POST /api/viviendas/` y `/api/viviendas/{id}/` | CRUD de viviendas (`terreno`, `identificador`, `tipo`: `CASA` o `DEPARTAMENTO`) |
| `GET, POST /api/puntos-acceso/` y `/api/puntos-acceso/{id}/` | CRUD de puntos de acceso (`terreno`, `vivienda` o `null`, `nombre`, `tipo`: `PUERTA` o `PORTON`, `activo`) |
| `GET /api/viviendas/{id}/participaciones/` | Lista las personas de la vivienda y su rol |
| `POST /api/viviendas/{id}/participaciones/` | Operación del negocio: `{"persona": <id>, "rol": "ARRENDATARIO"}` |

Reglas de datos:

- `Persona.codigo` y `Persona.email` son únicos. `codigo` es un identificador ficticio, no un RUT.
- El identificador de la vivienda es único dentro de su terreno: dos terrenos pueden tener una "Casa 1".
- Si un punto de acceso tiene vivienda, esa vivienda debe ser del mismo terreno (400). Sin vivienda, es un acceso común.
- No se puede mover a otro terreno una vivienda que tiene puntos de acceso (400).
- `PROTECT` responde **409** con un mensaje al eliminar una persona que administra terrenos, un terreno con viviendas o puntos, o una vivienda con puntos o participaciones. Hay que reasignar o eliminar antes lo relacionado.

## 8. Permisos por alcance

JWT identifica la cuenta. Los permisos deciden qué puede hacer según su vínculo con el terreno o la vivienda. Las clases están en `config/permissions.py` y cada ViewSet las declara en `permission_classes`.

| Recurso | Listar | Ver detalle | Crear | Editar | Eliminar |
| --- | --- | --- | --- | --- | --- |
| Personas | Solo la propia | Solo la propia | Staff | Solo la propia | Staff |
| Terrenos | Los que administra o donde tiene una vivienda | Igual que listar | Staff | Su administrador | Staff |
| Viviendas | Las de los terrenos que administra y donde participa | Igual que listar | Administrador del terreno | Administrador del terreno | Administrador del terreno |
| Puntos de acceso | Los de los terrenos que administra | Igual que listar | Administrador del terreno | Administrador del terreno | Administrador del terreno |
| Participaciones (operación) | Staff o quien participa en la vivienda | — | Ver sección 9 | — | — |

- `is_staff` tiene acceso completo a los cuatro maestros.
- Sin token: **401**. Con token, pero fuera del alcance: **403** con un `detail` que explica el motivo.
- Los listados se filtran en `get_queryset`. Al ver, editar o eliminar un registro existente fuera del alcance, la respuesta es 403 (no 404): el ViewSet lo busca entre todos y `has_object_permission` decide.
- Al crear o editar viviendas y puntos de acceso se comprueba, antes de guardar, que el terreno de destino lo administre quien hace la petición.
- Una cuenta sin persona vinculada recibe listados vacíos y 403 al escribir.

## 9. Operación del negocio: asignar una persona a una vivienda

`POST /api/viviendas/{id}/participaciones/` con `{"persona": <id>, "rol": "<ROL>"}`. Roles: `PROPIETARIO_ADMIN`, `PROPIETARIO`, `ARRENDATARIO` y `CONVIVIENTE`.

| Regla | Respuesta si no se cumple |
| --- | --- |
| Solo quien tiene una participación **activa** `PROPIETARIO_ADMIN` en **esa** vivienda puede asignar `PROPIETARIO`, `ARRENDATARIO` o `CONVIVIENTE` | 403 |
| Solo el staff puede asignar `PROPIETARIO_ADMIN` | 403 |
| Una persona tiene una sola participación por vivienda | 400 con `persona` explicando el duplicado |
| La persona debe existir y el rol debe ser válido | 400 |

Las reglas se comprueban antes de guardar, en este orden: autoridad (403), datos y duplicado (400) y, solo entonces, el guardado (201). Ningún rechazo modifica la BD; las pruebas automáticas lo verifican comparando el conteo de `ParticipacionVivienda`. El duplicado se valida en el serializer, sin depender del error de integridad de la BD; la restricción única `(persona, vivienda)` queda como respaldo.

**Supuestos para revisar con el docente:**

- Asignar `PROPIETARIO_ADMIN` lo hace solo el staff. El caso no dice quién nombra al primer propietario administrador de una vivienda.
- El administrador del terreno no gestiona a las personas de las viviendas: son alcances distintos. En la demo, Ana administra TER-001 y recibe 403 al asignar en Casa 1.
- La regla se aplica también al staff: no asigna `PROPIETARIO`, `ARRENDATARIO` ni `CONVIVIENTE` si no es `PROPIETARIO_ADMIN` de esa vivienda. Para casos administrativos puede usar Django Admin.
- `PROPIETARIO_ADMIN` incluye la condición de propietario.
- Las participaciones nuevas quedan activas. Cambiar el rol o desactivar una participación se hace por ahora desde Django Admin.
- Al eliminar una persona se eliminan sus participaciones (`CASCADE`): el vínculo actual pierde sentido sin la persona. Eliminar una vivienda con participaciones sí está protegido (409).

## 10. Diagrama ER

El diagrama completo está en [`er/`](er/): [PNG](er/diagrama_er_v1.png), [SVG ampliable](er/diagrama_er_v1.svg), la fuente [DOT](er/diagrama_er_v1.dot) y el [archivo de draw.io](er/SmartConnect_ER_v1.drawio) con dos pestañas: **ER v1 completo** y **BD inicial implementada**. En azul, las tablas implementadas; en gris, las previstas para siguientes entregas.

Notación pata de gallo: `||` exactamente uno, `|o` cero o uno y `o<` cero o varios. Los atributos se escriben como `nombre: tipo` con `PK`, `FK`, `UK` y `null`.

Tablas implementadas:

```mermaid
erDiagram
    PERSONA ||--o{ TERRENO : administra
    TERRENO ||--o{ VIVIENDA : contiene
    PERSONA ||--o{ PARTICIPACION_VIVIENDA : participa
    VIVIENDA ||--o{ PARTICIPACION_VIVIENDA : tiene
    TERRENO ||--o{ PUNTO_ACCESO : contiene
    VIVIENDA |o--o{ PUNTO_ACCESO : vincula_opcionalmente

    PERSONA {
        int id PK
        string codigo UK
        string nombres
        string apellidos
        string email UK
        int usuario_id FK, UK "null"
    }
    TERRENO {
        int id PK
        string codigo UK
        string nombre
        string direccion
        int administrador_id FK
    }
    VIVIENDA {
        int id PK
        int terreno_id FK
        string identificador
        string tipo
    }
    PARTICIPACION_VIVIENDA {
        int id PK
        int persona_id FK
        int vivienda_id FK
        string rol
        boolean activa
    }
    PUNTO_ACCESO {
        int id PK
        int terreno_id FK
        int vivienda_id FK "null"
        string nombre
        string tipo
        boolean activo
    }
```

`PERSONA.usuario_id` apunta a la tabla de usuarios de Django (`auth_user`), que gestiona las contraseñas y el login. Es opcional porque no todas las personas usan la API.

<details>
<summary>Diagrama completo previsto</summary>

```mermaid
erDiagram
    PERSONA ||--o{ TERRENO : administra
    TERRENO ||--o{ VIVIENDA : contiene
    PERSONA ||--o{ PARTICIPACION_VIVIENDA : participa
    VIVIENDA ||--o{ PARTICIPACION_VIVIENDA : tiene
    PERSONA ||--o{ TRABAJADOR_TERRENO : trabaja
    TERRENO ||--o{ TRABAJADOR_TERRENO : emplea
    PERSONA ||--o{ CREDENCIAL : posee
    TERRENO ||--o{ PUNTO_ACCESO : contiene
    VIVIENDA |o--o{ PUNTO_ACCESO : vincula_opcionalmente
    PERSONA ||--o{ AUTORIZACION_ACCESO : recibe
    PUNTO_ACCESO ||--o{ AUTORIZACION_ACCESO : habilita
    PUNTO_ACCESO ||--o{ INTENTO_ACCESO : registra
    PERSONA |o--o{ INTENTO_ACCESO : identificada
    CREDENCIAL |o--o{ INTENTO_ACCESO : utilizada

    PERSONA {
        int id PK
        string codigo UK
        string nombres
        string apellidos
        string email UK
        int usuario_id FK, UK "null"
    }
    TERRENO {
        int id PK
        string codigo UK
        string nombre
        string direccion
        int administrador_id FK
    }
    VIVIENDA {
        int id PK
        int terreno_id FK
        string identificador
        string tipo
    }
    PARTICIPACION_VIVIENDA {
        int id PK
        int persona_id FK
        int vivienda_id FK
        string rol
        boolean activa
    }
    TRABAJADOR_TERRENO {
        int id PK
        int persona_id FK
        int terreno_id FK
        string funcion
        boolean activo
    }
    CREDENCIAL {
        int id PK
        string uid UK
        int persona_id FK
        string estado
    }
    PUNTO_ACCESO {
        int id PK
        int terreno_id FK
        int vivienda_id FK "null"
        string nombre
        string tipo
        boolean activo
    }
    AUTORIZACION_ACCESO {
        int id PK
        int persona_id FK
        int punto_acceso_id FK
        boolean activa
    }
    INTENTO_ACCESO {
        int id PK
        int punto_acceso_id FK
        int persona_id FK "null"
        int credencial_id FK "null"
        string medio
        string uid_recibido "null para APP"
        datetime fecha_hora
        string resultado
        string motivo
        string estado_dispositivo
        string contexto_proximidad
    }
```

</details>

| Relación | Cardinalidad | Justificación |
| --- | --- | --- |
| Persona administra Terreno | Persona 0..N terrenos; Terreno exactamente 1 administrador | Se puede administrar varios terrenos y cada uno exige un responsable |
| Persona tiene una cuenta | Persona 0..1 cuenta; cuenta 0..1 persona | No todas las personas usan la API; una cuenta representa a una sola persona |
| Terreno contiene Vivienda | Terreno 0..N viviendas; Vivienda exactamente 1 terreno | Se puede registrar el terreno antes de sus viviendas |
| Persona participa en Vivienda | M:N mediante ParticipacionVivienda | Una persona puede tener varias viviendas y una vivienda varias personas; el rol depende de la vivienda |
| Terreno contiene PuntoAcceso | Terreno 0..N puntos; PuntoAcceso exactamente 1 terreno | Cada acceso pertenece a un terreno |
| Vivienda vincula PuntoAcceso | Vivienda 0..N puntos; PuntoAcceso 0..1 vivienda | Un acceso privado apunta a una vivienda; los comunes no tienen vivienda |
| Previstas | TrabajadorTerreno, Credencial, AutorizacionAcceso e IntentoAcceso | Se implementarán en siguientes entregas; deben revisarse con el docente |

Para regenerar las imágenes desde el DOT se necesita Graphviz (`dot`):

```powershell
dot -Tpng -Gdpi=225 er/diagrama_er_v1.dot -o er/diagrama_er_v1.png
dot -Tsvg er/diagrama_er_v1.dot -o er/diagrama_er_v1.svg
.\.venv\Scripts\python.exe er/limpiar_svg.py er/diagrama_er_v1.svg
```

El último paso quita del SVG las etiquetas transparentes de las relaciones, que solo sirven para distribuir el diagrama.

## 11. Cómo está organizado el código

```text
petición → config/urls.py → views.py → config/permissions.py → serializers.py → models.py → SQLite
```

| Archivo | Qué contiene |
| --- | --- |
| `config/settings.py` | Apps instaladas, SQLite, JWT (`REST_FRAMEWORK` y `SIMPLE_JWT`) |
| `config/urls.py` | Rutas de token y registro de los cuatro recursos en `DefaultRouter` |
| `config/permissions.py` | Clases de permiso por alcance y filtros de listados |
| `config/mixins.py` | Respuesta 409 cuando `PROTECT` impide eliminar |
| `personas/` | Persona y su vínculo con la cuenta (`usuario`); comando `cargar_demo` |
| `terrenos/` | Terreno y su administrador |
| `viviendas/` | Vivienda, ParticipacionVivienda y la operación `participaciones` |
| `accesos/` | PuntoAcceso y la validación de vivienda del mismo terreno |
| `*/tests.py` y `config/pruebas.py` | Pruebas automáticas y escenario común |

## 12. Pruebas automáticas

En otra terminal, desde la carpeta de `manage.py`:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test
```

Los 34 tests usan una BD de prueba separada y cubren:

- La colección de Apidog completa (62 peticiones, en orden y con login JWT real sobre los datos de `cargar_demo`). Cada rechazo se comprueba sin cambios en la BD y, al final, solo quedan los datos de demostración.
- 401 sin token o con token inválido; login con `access` y `refresh`; renovación con un `access` nuevo que funciona.
- 200/201 con acciones permitidas y lo que quedó guardado; 403 fuera del alcance (terreno, vivienda, punto y persona ajenos).
- La operación: asignación válida, duplicada (400), sin autoridad (403), con `PROPIETARIO_ADMIN` inactivo o de otra vivienda (403), sin que cambie el conteo de participaciones.
- Los CRUD de viviendas y puntos de acceso, incluida la vivienda de otro terreno, y `cargar_demo` repetible.

## 13. Checklist de la entrega 2

- [x] Cuatro CRUD maestros: personas, terrenos, viviendas y puntos de acceso.
- [x] Operación del negocio con reglas comprobadas antes de guardar, un caso válido y rechazos que no modifican la BD.
- [x] Login JWT, uso del token y renovación.
- [x] 401 sin autenticación y 403 fuera del alcance por terreno o vivienda.
- [x] ER actualizado en `er/` (DOT y draw.io).
- [ ] Exportar de nuevo `er/diagrama_er_v1.png` y `er/diagrama_er_v1.svg` con Graphviz (sección 10).
- [x] Datos ficticios suficientes y cuentas de prueba (`cargar_demo`).
- [x] Colección de Apidog guardada en el repositorio.
- [x] Instalación, migraciones y preparación de datos documentadas.
- [ ] Ejecutar la colección en Apidog y guardar capturas reales (login, 401, 403, operación y CRUD).
- [ ] Demostrar persistencia reiniciando `runserver`.
- [ ] Ramas por tarea y PR revisados por el compañero (sección 15).
- [ ] URL del repositorio y hash del commit revisado (`git rev-parse HEAD`).
- [ ] Cada integrante explica su aporte y una decisión del flujo.
- [ ] Revisar con el docente los supuestos de la sección 9.

## 14. Observaciones para la siguiente entrega

- Implementar TrabajadorTerreno, Credencial, AutorizacionAcceso e IntentoAcceso y su historial.
- Permitir que el propietario administrador cambie el rol o desactive una participación desde la API (hoy solo desde Django Admin).
- Revisar el `CASCADE` de Persona sobre sus participaciones cuando exista historial: puede convenir desactivar personas en vez de eliminarlas.
- Definir quién nombra al primer `PROPIETARIO_ADMIN` y si el staff debe poder asignar los demás roles.
- Evaluar si un recurso fuera del alcance debe responder 404 en vez de 403, para no revelar qué `id` existen.
- Agregar filtros y paginación a los listados (por ejemplo, viviendas por terreno).
- Para cerrar sesión antes de que venza el token, activar la lista negra de Simple JWT (`token_blacklist`) y la rotación del refresh.
- Antes de cualquier despliegue: `SECRET_KEY` y `DEBUG` desde variables de entorno y contraseñas distintas a la de demo.
- La colección toma `vivienda_demo_id` como la primera vivienda que ve Diego; si cambian el orden de `cargar_demo`, revisen ese paso.

## 15. Trabajo en equipo: ramas y PR

Cada bloque de esta entrega está en su propia rama, y cada una parte de la anterior. Ábranse los PR en este orden; al integrar uno, el siguiente queda con solo sus cambios:

| Orden | Rama | Contenido |
| --- | --- | --- |
| 1 | `chore/estructura-docs` | `er/` y `apidog/` versionados, `docs/` fuera de Git, claves primarias `int` |
| 2 | `docs/diagrama-er` | Diagrama ER en notación pata de gallo (PNG, DOT y draw.io) |
| 3 | `feature/viviendas-puntos-acceso` | CRUD de viviendas y puntos de acceso, 409 por `PROTECT` |
| 4 | `feature/jwt` | Simple JWT, rutas de token y vínculo Persona-cuenta |
| 5 | `feature/participacion-vivienda` | ParticipacionVivienda, operación del negocio y permisos por alcance |
| 6 | `feature/datos-pruebas-docs` | `cargar_demo`, pruebas, colección de Apidog, ER y README |

```powershell
git switch feature/jwt
git push -u origin feature/jwt
```

Revisen los cambios antes de cada commit. No suban `.venv`, `db.sqlite3`, `docs/`, contraseñas reales ni `__pycache__`. Para obtener el hash al finalizar: `git rev-parse HEAD`.

## 16. Si algo falla

| Mensaje o síntoma | Cómo resolverlo |
| --- | --- |
| `py` no se reconoce | Revisen la instalación de Python o usen `python` |
| No encuentra `manage.py` | Abran la terminal dentro de `smartconnect` |
| `No module named django` o `rest_framework_simplejwt` | Ejecuten `pip install -r requirements.txt` con `.\.venv\Scripts\python.exe` y usen ese mismo ejecutable |
| `no such table` o `no such column` | Ejecuten `manage.py migrate` |
| 401 en todas las peticiones | Falta el header `Authorization: Bearer <access>`, o el access venció: renuévenlo con `/api/token/refresh/` o hagan login otra vez |
| 401 en el login | Usuario o clave incorrectos. Ejecuten `cargar_demo` para restablecer `Demo1234!` |
| 403 con token válido | La acción está fuera del alcance de esa cuenta; el `detail` explica el motivo (sección 8) |
| Un listado viene vacío | La cuenta no tiene persona vinculada o no administra ni participa en nada |
| POST devuelve 400 | El JSON de respuesta explica el campo inválido o duplicado |
| DELETE devuelve 409 | Hay datos relacionados; reasignen o eliminen primero lo indicado |
| URL de detalle devuelve 404 | Revisen el `id` y la barra final `/` |
| Puerto 8000 ocupado | Ejecuten `manage.py runserver 8001` y cambien `base_url` en Apidog |
| La colección falla al repetirla | Una ejecución anterior pudo dejar `PER-PRUEBA` o `TER-PRUEBA`. Eliminen esos registros de práctica como `staff` (puntos, vivienda y terreno de prueba primero) y repitan |

- [Instalación de Django 5.2](https://docs.djangoproject.com/en/5.2/intro/install/)
- [Permisos en DRF](https://www.django-rest-framework.org/api-guide/permissions/)
- [Simple JWT](https://django-rest-framework-simplejwt.readthedocs.io/)
- [Importación de colecciones Postman en Apidog](https://docs.apidog.com/import-from-postman-635043m0)
