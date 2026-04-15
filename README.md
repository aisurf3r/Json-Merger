# 🔀 JSON Merger Pro

> **Fusiona, filtra y limpia archivos JSON sin escribir una sola línea de código.**

Herramienta de escritorio para combinar múltiples archivos JSON, filtrar registros por condiciones, eliminar duplicados y exportar a CSV — todo desde una interfaz visual.
<img width="1920" height="1080" alt="{24E12D04-E2C6-4777-95D0-A33AB1ADA3BB}" src="https://github.com/user-attachments/assets/b7726f20-4e37-4388-a5d5-e0821b62960c" />
---

## 📋 Índice

- [⚙️ Instalación](#️-instalación)
- [📂 Carga de archivos](#-carga-de-archivos)
- [🔗 Modos de unión](#-modos-de-unión)
- [🔍 Filtrar registros](#-filtrar-registros)
- [🧹 Deduplicar](#-deduplicar)
- [🪆 JSONs anidados](#-jsons-anidados)
- [👁️ Vista previa](#️-vista-previa)
- [💾 Exportar y guardar](#-exportar-y-guardar)
- [🛠️ Otras funciones](#️-otras-funciones)
- [❓ Preguntas frecuentes](#-preguntas-frecuentes)

---

## ⚙️ Instalación
<img width="551" height="439" alt="{15E700BE-717A-4215-B65B-9A5B7C7AEE85}" src="https://github.com/user-attachments/assets/6aed8212-64bb-44f4-8151-36d43bcc87d5" />
Requiere **Python 3.8 o superior**. Las dependencias se instalan automáticamente al ejecutar la app por primera vez.

```bash
python json_merger_pro.py
```

Si la instalación automática falla (sin conexión o permisos restringidos), instala manualmente:

```bash
pip install customtkinter pyperclip
```

---

## 📂 Carga de archivos

Hay dos formas de cargar archivos:

- **Seleccionar Archivos** — abre el explorador y permite elegir uno o varios `.json` a la vez. También acepta cualquier otro formato de texto que contenga JSON válido.
- **Cargar Carpeta** — carga automáticamente todos los `.json` que encuentre en la carpeta elegida, sin límite de cantidad.

### 🚦 Indicadores de estado en la lista

Cada archivo cargado muestra un indicador visual:

| Indicador | Significado |
|-----------|-------------|
| ✅ nombre normal | JSON válido y listo |
| ⚠️ naranja | Contenido JSON válido pero extensión no estándar (`.txt`, etc.) |
| ❌ rojo | El archivo tiene errores de sintaxis JSON y será ignorado al fusionar |

> Los archivos con error no bloquean la app — simplemente se excluyen de la fusión con un aviso previo.

### 🔃 Ordenar la lista

El botón **Ordenar por** reordena los archivos antes de fusionarlos:

| Opción | Comportamiento |
|--------|---------------|
| Alfabéticamente | Orden A-Z por nombre de archivo |
| Por Fecha | Más reciente primero |
| Por Tamaño | Más grande primero |

> ⚠️ **El orden importa:** en el modo objeto `{}`, si hay claves repetidas gana el **último** archivo de la lista.

---

## 🔗 Modos de unión

### 📋 Array `[ ]`

Todos los contenidos se combinan en una sola lista. Es el modo más habitual.

```
pedidos_enero.json   →  [ {id:1}, {id:2} ]
pedidos_febrero.json →  [ {id:3}, {id:4} ]

Resultado: [ {id:1}, {id:2}, {id:3}, {id:4} ]
```

✅ Ideal para colecciones del mismo tipo: usuarios, productos, pedidos, registros de log, etc.

### 📦 Objeto `{ }`

Las claves de todos los archivos se fusionan en un único objeto. Si una clave aparece en varios archivos, el valor del **último archivo prevalece**.

```
config_base.json      →  { "timeout": 30, "retries": 3 }
config_produccion.json →  { "timeout": 60, "debug": false }

Resultado: { "timeout": 60, "retries": 3, "debug": false }
```

✅ Ideal para archivos de configuración, traducciones o cualquier estructura clave-valor.

---

## 🔍 Filtrar registros

Permite quedarse solo con los registros que cumplen una condición. Funciona sobre **arrays de objetos**.

### Cómo usarlo

1. Carga tus archivos y pulsa **Filtrar Registros**
2. Elige la **clave** (campo) sobre la que filtrar
3. Elige el **operador**
4. Escribe el **valor** de comparación
5. Pulsa **Previsualizar** para ver cuántos registros coinciden antes de aplicar
6. Pulsa **Aplicar Filtro** para confirmar

> 💡 El filtro queda activo (indicador naranja). Puedes **encadenar filtros** sucesivos — cada uno opera sobre el resultado del anterior.

### Operadores disponibles

| Operador | Descripción | Ejemplo |
|----------|-------------|---------|
| `igual a` | Coincidencia exacta | `estado` igual a `activo` |
| `contiene` | El valor incluye el texto (sin distinguir mayúsculas) | `nombre` contiene `garcía` |
| `empieza con` | El valor comienza con el texto | `email` empieza con `admin` |
| `termina con` | El valor termina con el texto | `email` termina con `.es` |
| `mayor que` | Comparación numérica | `edad` mayor que `18` |
| `menor que` | Comparación numérica | `precio` menor que `100` |
| `existe` | El campo está presente, sea cual sea su valor | `telefono` existe |

### 📌 Ejemplos prácticos

---

#### Ejemplo 1 — Filtrar por valor exacto: solo usuarios activos

Tienes una lista de usuarios con distintos estados y quieres quedarte solo con los activos:

```json
[
  { "id": 1, "nombre": "Ana",   "estado": "activo"   },
  { "id": 2, "nombre": "Luis",  "estado": "inactivo" },
  { "id": 3, "nombre": "María", "estado": "activo"   }
]
```

```
Clave: estado   Operador: igual a   Valor: activo
```

Resultado — 2 registros:

```json
[
  { "id": 1, "nombre": "Ana",   "estado": "activo" },
  { "id": 3, "nombre": "María", "estado": "activo" }
]
```

---

#### Ejemplo 2 — Filtrar por rango numérico: productos por debajo de un precio

Tienes un catálogo de productos y quieres solo los que cuestan menos de 50€:

```
Clave: precio   Operador: menor que   Valor: 50
```

Resultado: solo los productos con `precio < 50`, independientemente de cualquier otro campo.

---

#### Ejemplo 3 — Filtrar por tipo de registro: aislar errores en un log

Tienes archivos de log con registros de distintos niveles (`INFO`, `WARNING`, `ERROR`) y quieres aislar solo los errores:

```
Clave: level   Operador: igual a   Valor: ERROR
```

---

#### Ejemplo 4 — Filtrar por presencia de campo: clientes con teléfono registrado

Tienes una lista de clientes donde algunos tienen el campo `telefono` y otros no. Para quedarte solo con los que sí lo tienen:

```
Clave: telefono   Operador: existe
```

> No hay que escribir nada en el campo Valor con el operador `existe`.

---

#### Ejemplo 5 — Filtrar por texto parcial: buscar registros que contienen una palabra

Tienes una lista de lugares o personas y quieres todos los que incluyen una palabra concreta en su nombre:

```
Clave: name   Operador: contiene   Valor: San
```

Resultado: todos los registros cuyo campo `name` incluya "San" — "San Sebastián", "Santa Cruz", "Santiago"...

---

#### Ejemplo 6 — Filtros encadenados: dos condiciones aplicadas en serie

Quieres los pedidos del cliente con `id` 5 que además estén en estado `pendiente`:

**Paso 1:**
```
Clave: cliente_id   Operador: igual a   Valor: 5
```
*Aplicar → el filtro queda activo*

**Paso 2** (opera sobre el resultado del paso 1):
```
Clave: estado   Operador: igual a   Valor: pendiente
```

Resultado: solo los pedidos del cliente 5 que están pendientes.

---

## 🧹 Deduplicar

Elimina registros repetidos. Funciona sobre **arrays de objetos**.

### Cómo usarlo

1. Pulsa **Deduplicar**
2. Elige el **modo** de comparación
3. Pulsa **Previsualizar** para ver cuántos registros se eliminarían
4. Pulsa **Aplicar** para confirmar

### Modos de deduplicación

#### 🎯 Exacto
Elimina solo los registros donde **todos los campos son idénticos**. Si dos registros tienen el mismo `id` pero distinto `nombre`, no se consideran duplicados.

✅ Útil cuando has cargado el mismo archivo dos veces por error, o tienes archivos con solapamiento total de datos.

#### 🔑 Por clave
Elimina los registros que comparten el mismo valor en **un campo concreto**, aunque el resto de campos sean distintos. Mantiene la primera aparición y descarta las siguientes.

✅ Útil cuando tienes registros del mismo usuario o producto en distintos archivos y quieres quedarte con uno solo por identificador.

### 📌 Ejemplos prácticos

---

#### Ejemplo 1 — El mismo archivo cargado dos veces

Has cargado accidentalmente el mismo archivo dos veces. Tienes 500 registros pero aparecen 1.000 en la lista.

```
Modo: Exacto
```

```
Previsualizar → "Se eliminarían 500 duplicados → quedarían 500 registros"
```

---

#### Ejemplo 2 — Dos versiones del mismo fichero con datos actualizados

Tienes dos exportaciones de la misma base de datos tomadas en momentos distintos. Algunos registros han cambiado entre versiones:

```json
version_antigua.json: { "id": 42, "nombre": "Carlos", "email": "carlos@old.com" }
version_nueva.json:   { "id": 42, "nombre": "Carlos", "email": "carlos@new.com" }
```

- Con modo **Exacto**: no elimina nada — los registros no son idénticos campo a campo.
- Con modo **Por clave → `id`**: elimina el duplicado y conserva el primero de la lista.

> 💡 **Consejo:** si quieres conservar la versión más reciente, usa **Ordenar por → Por Fecha** (más reciente primero) antes de deduplicar. Así el registro conservado será siempre el más actualizado.

---

#### Ejemplo 3 — Cuidado con campos que parecen únicos pero no lo son

A veces un campo como `nombre` o `ciudad` puede repetirse en registros que son en realidad entidades distintas. Por ejemplo, puede haber dos ciudades llamadas "Valencia" en países diferentes — son lugares distintos con el mismo nombre.

Si deduplicas por `nombre`, la app eliminará una de ellas porque el valor del campo es igual. En casos así, usa el modo **Exacto** o elige un campo que sí sea verdaderamente único (`id`, `codigo`, `coordenadas`...).

> ⚠️ Antes de deduplicar por clave, asegúrate de que ese campo identifica de forma única cada registro en tus datos.

---

#### Ejemplo 4 — Base de datos de clientes con emails duplicados

Tienes una lista de clientes donde algunos se han registrado varias veces con el mismo email pero con datos distintos:

```json
[
  { "id": 1, "nombre": "Ana García",  "email": "ana@mail.com", "plan": "basic"   },
  { "id": 7, "nombre": "Ana G.",      "email": "ana@mail.com", "plan": "premium" },
  { "id": 2, "nombre": "Luis Torres", "email": "luis@mail.com","plan": "basic"   }
]
```

```
Modo: Por clave   Clave: email
```

Resultado — 2 registros (se conserva `id:1` porque aparece primero):

```json
[
  { "id": 1, "nombre": "Ana García",  "email": "ana@mail.com", "plan": "basic" },
  { "id": 2, "nombre": "Luis Torres", "email": "luis@mail.com","plan": "basic" }
]
```

---

#### Ejemplo 5 — Combinar filtro y deduplicación

Para obtener un listado limpio de clientes activos sin emails duplicados:

**Paso 1 — Filtrar:**
```
Clave: estado   Operador: igual a   Valor: activo
```

**Paso 2 — Deduplicar** (sobre el resultado filtrado):
```
Modo: Por clave   Clave: email
```

El indicador naranja confirma que ambas operaciones están activas. Al guardar, el archivo resultante tendrá **solo los clientes activos y sin duplicados de email**.

---

## 🪆 JSONs anidados

Muchos JSONs del mundo real tienen estructura jerárquica en lugar de ser listas planas. Por ejemplo, un JSON de un país que contiene regiones, que contienen provincias, que contienen municipios.

Las herramientas de filtrado y deduplicación necesitan una lista plana para operar. Cuando detectan un objeto anidado, en vez de mostrar un error abren automáticamente el **selector de nivel**.

### Selector de nivel

Al pulsar Filtrar o Deduplicar sobre un JSON anidado aparece una ventana como esta:

```
Este archivo tiene datos anidados
¿Con qué datos quieres trabajar?

  ○  regions
     8 registros · campos: name, code, provinces

  ○  regions → provinces
     52 registros · campos: name, code, municipalities

  ●  regions → provinces → municipalities
     8.131 registros · campos: name, lat, lng

  [ Usar estos datos ]   [ Cancelar ]
```

La app escanea el JSON completo, **agrupa los arrays por nivel** y muestra el total real de registros de cada nivel. Eliges el nivel que te interesa y continúas normalmente con Filtrar o Deduplicar.

> 📝 Trabajar con datos extraídos de un JSON anidado **no modifica el archivo original**. Si guardas el resultado, obtendrás un array plano con los registros del nivel elegido.

---

## 👁️ Vista previa

El panel inferior muestra el contenido del archivo seleccionado o el resultado final, con resaltado de sintaxis:

| Color | Elemento JSON |
|-------|--------------|
| 🔵 Azul | Claves |
| 🟢 Verde | Cadenas de texto (valores) |
| 🟠 Naranja | Números |
| 🟣 Violeta | `true`, `false`, `null` |
| ⬜ Gris | Puntuación `{ } [ ] , :` |
| 🟡 Naranja itálica | Avisos de truncado |

> Para archivos muy grandes, la vista previa muestra las primeras **500 líneas** con un aviso al final. El archivo guardado siempre contiene los datos **completos**.

---

## 💾 Exportar y guardar

### 💚 Unir y Guardar

Fusiona todos los archivos válidos (respetando el modo de unión elegido) y guarda el resultado como un nuevo `.json`. Si hay filtros o deduplicación activos, el archivo guardado los refleja.

El nombre sugerido incluye la fecha y hora: `merged_20250414_153022.json`

### 📊 Exportar CSV

Convierte el resultado a `.csv` compatible con Excel y Google Sheets. Funciona solo con arrays de objetos planos.

Los valores que son a su vez objetos o arrays se serializan como texto JSON en la celda correspondiente.

### 📋 Copiar al Portapapeles

Copia el JSON resultante directamente al portapapeles, listo para pegar en cualquier editor o herramienta.

---

## 🛠️ Otras funciones

### ↩️ Resetear Filtros

Descarta el filtro o deduplicación activos y vuelve a los datos originales sin tocar los archivos. El indicador naranja desaparece.

### 🌙 Cambio de tema

El interruptor ☀️ / 🌙 en la cabecera alterna entre tema oscuro y claro. El resaltado de sintaxis del panel de vista previa se adapta automáticamente.

### 🖱️ Menú contextual (clic derecho en la lista)

- **Eliminar archivo** — quita el archivo de la lista sin borrarlo del disco
- **Abrir en explorador** — abre la carpeta que contiene el archivo

---

## ❓ Preguntas frecuentes

**¿Se modifican los archivos originales?**
No. La app solo lee los archivos. El resultado se guarda siempre como un archivo nuevo.

**¿Qué pasa si cargo archivos con estructuras distintas?**
En modo array se mezclan todos los objetos en la misma lista aunque tengan campos diferentes. En modo objeto las claves se fusionan. La app no valida que todos los archivos tengan el mismo esquema.

**¿Puedo cargar archivos que no tengan extensión `.json`?**
Sí. La app acepta cualquier archivo de texto que contenga JSON válido. Aparecerá marcado en naranja con el aviso "extensión no estándar", pero funcionará con normalidad.

**El filtro no devuelve resultados aunque el valor existe**
Comprueba que el valor esté escrito exactamente igual — el operador `igual a` distingue mayúsculas. Usa `contiene` si no estás seguro de la capitalización exacta.

**¿Por qué la deduplicación "por clave" conserva el primero y no el último?**
Porque procesa los registros en el orden en que aparecen en la lista. Si quieres conservar el más reciente, usa **Ordenar por → Por Fecha** (más reciente primero) antes de deduplicar.

**¿Puedo encadenar varias operaciones antes de guardar?**
Sí. Puedes aplicar un filtro, luego deduplicar el resultado, y guardar al final. Cada operación trabaja sobre el resultado de la anterior. El indicador naranja te avisa de que hay datos modificados activos.

**¿Qué ocurre con los archivos inválidos al guardar?**
Se ignoran con un aviso previo. La app pregunta si quieres continuar con los archivos válidos restantes.

---

## 👤 Créditos

Desarrollado con ❤️ por [Aisurf3r](https://github.com/aisurf3r/Json-Merger) · v1.0
