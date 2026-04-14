# JSON Merger Pro

**Fusiona, filtra y limpia archivos JSON sin escribir una sola línea de código.**

Herramienta de escritorio para combinar múltiples archivos JSON, filtrar registros por condiciones, eliminar duplicados y exportar a CSV — todo desde una interfaz visual.


<img width="1920" height="1080" alt="{24E12D04-E2C6-4777-95D0-A33AB1ADA3BB}" src="https://github.com/user-attachments/assets/b7726f20-4e37-4388-a5d5-e0821b62960c" />
---

## Índice

- [Instalación](#instalación)
- [Carga de archivos](#carga-de-archivos)
- [Modos de unión](#modos-de-unión)
- [Filtrar registros](#filtrar-registros)
- [Deduplicar](#deduplicar)
- [JSONs anidados](#jsons-anidados)
- [Vista previa](#vista-previa)
- [Exportar y guardar](#exportar-y-guardar)
- [Otras funciones](#otras-funciones)
- [Preguntas frecuentes](#preguntas-frecuentes)

---

## Instalación

Requiere **Python 3.8 o superior**. Las dependencias se instalan automáticamente al ejecutar la app por primera vez.

```bash
python json_merger_pro.py
```
<img width="551" height="439" alt="{15E700BE-717A-4215-B65B-9A5B7C7AEE85}" src="https://github.com/user-attachments/assets/6aed8212-64bb-44f4-8151-36d43bcc87d5" />


Si la instalación automática falla (sin conexión o permisos restringidos), instala manualmente:

```bash
pip install customtkinter pyperclip
```

---

## Carga de archivos

Hay 2 formas de cargar archivos:

**Seleccionar Archivos** — abre el explorador y permite elegir uno o varios `.json` a la vez. También acepta cualquier otro formato de texto que contenga JSON válido.

**Cargar Carpeta** — carga automáticamente todos los `.json` que encuentre en la carpeta elegida, sin límite de cantidad.

### Indicadores de estado en la lista

Cada archivo cargado muestra un indicador visual:

| Indicador | Significado |
|-----------|-------------|
| nombre normal | JSON válido y listo |
| ⚠ naranja | Contenido JSON válido pero extensión no estándar (`.txt`, etc.) |
| ✗ rojo | El archivo tiene errores de sintaxis JSON y será ignorado al fusionar |

Los archivos con error no bloquean la app — simplemente se excluyen de la fusión con un aviso previo.

### Ordenar la lista

El botón segmentado **Ordenar por** reordena los archivos antes de fusionarlos:

- **Alfabéticamente** — orden A-Z por nombre de archivo
- **Por Fecha** — más reciente primero
- **Por Tamaño** — más grande primero

El orden importa: en el modo objeto `{}`, si hay claves repetidas gana el último archivo de la lista.

---

## Modos de unión

### Array `[ ]`

Todos los contenidos se combinan en una sola lista. Es el modo más habitual.

```
usuarios_enero.json  →  [ {id:1}, {id:2} ]
usuarios_febrero.json →  [ {id:3}, {id:4} ]

Resultado: [ {id:1}, {id:2}, {id:3}, {id:4} ]
```

Ideal para colecciones del mismo tipo: usuarios, productos, pedidos, registros de log, etc.

### Objeto `{ }`

Las claves de todos los archivos se fusionan en un único objeto. Si una clave aparece en varios archivos, el valor del último archivo prevalece.

```
config_base.json     →  { "timeout": 30, "retries": 3 }
config_produccion.json → { "timeout": 60, "debug": false }

Resultado: { "timeout": 60, "retries": 3, "debug": false }
```

Ideal para archivos de configuración, traducciones o cualquier estructura clave-valor.

---

## Filtrar registros

Permite quedarse solo con los registros que cumplen una condición. Funciona sobre **arrays de objetos**.

### Cómo usarlo

1. Carga tus archivos y pulsa **Filtrar Registros**
2. Elige la **clave** (campo) sobre la que filtrar
3. Elige el **operador**
4. Escribe el **valor** de comparación
5. Pulsa **Previsualizar** para ver cuántos registros coinciden antes de aplicar
6. Pulsa **Aplicar Filtro** para confirmar

El filtro queda activo (indicador naranja en la barra de herramientas). Puedes encadenar filtros sucesivos — cada uno opera sobre el resultado del anterior.

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

### Ejemplos prácticos

**Ejemplo 1 — Lista de usuarios: solo los activos**

Datos de entrada:
```json
[
  { "id": 1, "nombre": "Ana",   "estado": "activo"   },
  { "id": 2, "nombre": "Luis",  "estado": "inactivo" },
  { "id": 3, "nombre": "María", "estado": "activo"   }
]
```

Configuración:
```
Clave: estado   Operador: igual a   Valor: activo
```

Resultado (2 registros):
```json
[
  { "id": 1, "nombre": "Ana",   "estado": "activo" },
  { "id": 3, "nombre": "María", "estado": "activo" }
]
```

---

**Ejemplo 2 — Catálogo de productos: precio inferior a 50€**

```
Clave: precio   Operador: menor que   Valor: 50
```

Resultado: solo los productos con precio < 50, independientemente de cualquier otro campo.

---

**Ejemplo 3 — Registros de log: solo errores**

```
Clave: level   Operador: igual a   Valor: ERROR
```

---

**Ejemplo 4 — Clientes con teléfono registrado**

Para encontrar registros que tienen un campo concreto (aunque sea vacío):
```
Clave: telefono   Operador: existe
```
No hay que escribir nada en el campo Valor.

---

**Ejemplo 5 — Municipios de Brasil que contienen "Santa" en el nombre**

Con el archivo `brazil_municipios.json` (5.290 municipios):
```
Clave: name   Operador: contiene   Valor: Santa
```
Resultado: 192 municipios (Santa Catarina, Santa Rosa, Santa Maria...)

---

**Ejemplo 6 — Filtros encadenados (dos pasos)**

Para obtener los municipios del estado de Minas Gerais que empiezan por "São":

*Paso 1:*
```
Clave: state   Operador: igual a   Valor: Minas Gerais
```
*Aplicar → el filtro queda activo*

*Paso 2 (sobre el resultado anterior):*
```
Clave: name   Operador: empieza con   Valor: São
```
Resultado: solo municipios de Minas Gerais que empiezan por "São".

---

## Deduplicar

Elimina registros repetidos. Funciona sobre **arrays de objetos**.

### Cómo usarlo

1. Pulsa **Deduplicar**
2. Elige el **modo** de comparación
3. Pulsa **Previsualizar** para ver cuántos se eliminarían
4. Pulsa **Aplicar** para confirmar

### Modos de deduplicación

**Exacto** — elimina solo los registros donde todos los campos son idénticos. Si dos registros tienen el mismo `id` pero distinto `nombre`, no se consideran duplicados.

Útil cuando: has cargado el mismo archivo dos veces por error, o tienes archivos con solapamiento total de datos.

**Por clave** — elimina los registros que comparten el mismo valor en un campo concreto, aunque el resto de campos sean distintos. Mantiene la primera aparición y descarta las siguientes.

Útil cuando: tienes registros del mismo usuario/producto en distintos archivos y quieres quedarte con uno solo por identificador.

### Ejemplos prácticos

**Ejemplo 1 — El mismo archivo cargado dos veces (duplicados exactos)**

Tienes 500 registros y accidentalmente cargaste el mismo archivo dos veces → 1.000 registros totales.

```
Modo: Exacto
```
Previsualizar → "Se eliminarían 500 duplicados → quedarían 500 registros"

---

**Ejemplo 2 — Dos exportaciones de la misma BD con datos parcialmente actualizados**

```json
archivo_v1.json: { "id": 42, "nombre": "Carlos", "email": "carlos@old.com" }
archivo_v2.json: { "id": 42, "nombre": "Carlos", "email": "carlos@new.com" }
```

Con modo **Exacto** no se eliminaría nada (los registros no son idénticos).
Con modo **Por clave → id** sí se eliminaría el duplicado, conservando el primero de la lista.

> **Consejo:** Ordena los archivos por fecha (más reciente primero) antes de deduplicar por clave, así el valor más actualizado es el que se conserva.

---

**Ejemplo 3 — Lista de municipios con nombres repetidos en distintos estados**

El archivo `brazil_municipios.json` tiene municipios como "Cruzeiro do Sul" en tres estados diferentes (Acre, Paraná y Rio Grande do Sul). Son localidades distintas con el mismo nombre.

Con modo **Por clave → name**:
```
Modo: Por clave   Clave: name
```
Previsualizar → "Se eliminarían 256 duplicados → quedarían 5.034 registros"

Esto daría una lista de nombres únicos, útil si solo te interesa el catálogo de nombres sin importar el estado.

---

**Ejemplo 4 — Base de datos de clientes con registros duplicados por email**

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

Resultado (2 registros, se conserva el id:1 porque aparece primero):
```json
[
  { "id": 1, "nombre": "Ana García",  "email": "ana@mail.com", "plan": "basic" },
  { "id": 2, "nombre": "Luis Torres", "email": "luis@mail.com","plan": "basic" }
]
```

---

**Ejemplo 5 — Combinar filtro + deduplicación**

Para obtener un listado limpio de clientes activos sin duplicados:

*Paso 1 — Filtrar:*
```
Clave: estado   Operador: igual a   Valor: activo
```

*Paso 2 — Deduplicar (sobre el resultado filtrado):*
```
Modo: Por clave   Clave: email
```

El indicador naranja mostrará ambas operaciones activas. Al guardar, el archivo resultante tendrá solo los clientes activos y sin duplicados de email.

---

## JSONs anidados

Muchos JSONs del mundo real tienen estructura jerárquica en lugar de ser listas planas. Por ejemplo, un JSON de países que contiene estados, que contienen provincias, que contienen municipios.

Las herramientas de filtrado y deduplicación necesitan una lista plana para operar. Cuando detectan un objeto anidado, en vez de mostrar un error abren automáticamente el **selector de nivel**.

### Selector de nivel

Al pulsar Filtrar o Deduplicar sobre un JSON anidado aparece:

```
Este archivo tiene datos anidados
¿Con qué datos quieres trabajar?

  ○  cities
     27 registros · campos: name, lat, lng, districts

  ○  cities → districts
     339 registros · campos: name, lat, lng, subdistricts

  ●  cities → districts → subdistricts
     5.290 registros · campos: name, lat, lng

  [ Usar estos datos ]   [ Cancelar ]
```

La app escanea el JSON completo, agrupa los arrays por nivel y muestra el total real de registros por nivel. Eliges el nivel que te interesa y continúas normalmente con Filtrar o Deduplicar.

> **Nota:** trabajar con datos extraídos de un JSON anidado no modifica el archivo original. Si guardas el resultado, obtendrás un array plano con los registros del nivel elegido.

---

## Vista previa

El panel inferior muestra el contenido del archivo seleccionado o el resultado final, con resaltado de sintaxis:

| Color | Elemento |
|-------|----------|
| 🔵 Azul | Claves |
| 🟢 Verde | Cadenas de texto (valores) |
| 🟠 Naranja | Números |
| 🟣 Violeta | `true`, `false`, `null` |
| ⬜ Gris | Puntuación `{ } [ ] , :` |
| 🟡 Naranja itálica | Avisos de truncado |

Para archivos muy grandes, la vista previa muestra las primeras **500 líneas** con un aviso al final. El archivo guardado siempre contiene los datos completos.

---

## Exportar y guardar

### Unir y Guardar

Fusiona todos los archivos válidos (respetando el modo de unión elegido) y guarda el resultado como un nuevo `.json`. Si hay filtros o deduplicación activos, el archivo guardado los refleja.

El nombre sugerido incluye la fecha y hora: `merged_20250414_153022.json`

### Exportar CSV

Convierte el resultado a `.csv` compatible con Excel y Google Sheets. Funciona solo con arrays de objetos planos.

Los valores que son a su vez objetos o arrays se serializan como texto JSON en la celda correspondiente.

### Copiar al Portapapeles

Copia el JSON resultante directamente al portapapeles, listo para pegar en cualquier editor o herramienta.

---

## Otras funciones

### Resetear Filtros

Descarta el filtro o deduplicación activos y vuelve a los datos originales sin tocar los archivos. El indicador naranja desaparece.

### Cambio de tema

El interruptor ☀️ / 🌙 en la cabecera alterna entre tema oscuro y claro. El resaltado de sintaxis del panel de vista previa se adapta automáticamente.

### Menú contextual (clic derecho en la lista)

- **Eliminar archivo** — quita el archivo de la lista sin borrarlo del disco
- **Abrir en explorador** — abre la carpeta que contiene el archivo

---

## Preguntas frecuentes

**¿Se modifican los archivos originales?**
No. La app solo lee los archivos. El resultado se guarda siempre como un archivo nuevo.

**¿Qué pasa si cargo archivos con estructuras distintas?**
En modo array se mezclan todos los objetos en la misma lista aunque tengan campos diferentes. En modo objeto las claves se fusionan. La app no valida que todos los archivos tengan el mismo esquema.

**¿Puedo cargar archivos que no tengan extensión `.json`?**
Sí. La app acepta cualquier archivo de texto que contenga JSON válido. Aparecerá marcado en naranja con el aviso "extensión no estándar", pero funcionará con normalidad.

**El filtro no devuelve resultados aunque el valor existe**
Comprueba que el valor esté escrito exactamente igual (el operador `igual a` distingue mayúsculas). Usa `contiene` si no estás seguro de la capitalización exacta.

**¿Por qué la deduplicación "por clave" conserva el primero y no el último?**
Porque procesa los registros en el orden en que aparecen en la lista. Si quieres conservar el más reciente, ordena los archivos por fecha (más reciente primero) antes de deduplicar.

**¿Puedo encadenar varias operaciones antes de guardar?**
Sí. Puedes aplicar un filtro, luego deduplicar el resultado, y guardar al final. Cada operación trabaja sobre el resultado de la anterior. El indicador naranja te avisa de que hay datos modificados activos.

**¿Qué ocurre con los archivos inválidos al guardar?**
Se ignoran con un aviso previo. La app pregunta si quieres continuar con los archivos válidos restantes.

---

## Créditos

Desarrollado con ❤️ por [Aisurf3r](https://github.com/aisurf3r/Json-Merger) · v1.0
