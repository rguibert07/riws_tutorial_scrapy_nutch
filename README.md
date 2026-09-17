# Guía paso a paso — Crawling web: Scrapy y Apache Nutch
Basada en el material del curso *Recuperación de Información y Web Semántica* (Javier Parapar y Anxo Pérez, IRLab, UDC). Todo el contenido técnico (comandos, código, configuración) procede literalmente del PDF `03_tutorial_scrapy_nutch.pdf`. Esta guía solo añade la organización en pasos y las indicaciones de entorno (VS Code + Ubuntu + Git) que el PDF no detalla.

---

## PARTE 1 — Crawling web con Scrapy

### Paso 1. Conceptos: crawling y extracción de información (diapositiva 2)

Según el PDF:
- **Crawling**: descubrir y descargar páginas siguiendo enlaces desde unas URLs semilla.
- **Scraping**: extraer campos concretos del contenido descargado.
- **Scrapy** integra ambos procesos en un framework Python con peticiones, respuestas, selectores y pipelines.
- Objetivo del proyecto: obtener documentos de **al menos dos sitios web** y prepararlos para Elasticsearch.

### Paso 2. Entender qué ocurre durante un rastreo (diapositiva 3)

1. El spider crea las peticiones iniciales.
2. Scrapy las planifica y descarga las respuestas.
3. Un callback, como `parse`, extrae datos y crea nuevas peticiones.
4. Los items pasan por los pipelines y se exportan.

Nota importante del PDF: las descargas se gestionan de forma **asíncrona**. Seguir un enlace con `response.follow` agenda otra petición, **no** ejecuta una llamada recursiva directa a `parse`.

### Paso 3. Conocer el alcance de Scrapy (diapositiva 4)

- Adecuado para colecciones con páginas enlazadas, fichas, listados y paginación.
- Incluye control de concurrencia, filtrado de peticiones duplicadas, reintentos y exportación.
- **No ejecuta JavaScript por sí solo**. Procesa el HTML o los datos que devuelve la petición HTTP.
- Los datos cargados dinámicamente requieren localizar su respuesta de datos o integrar un navegador cuando sea necesario.

### Paso 4. Instalación (diapositiva 5)

En la terminal de VS Code:

```bash
python -m venv .venv
# Linux/macOS:
source .venv/bin/activate
# PowerShell: .venv\Scripts\Activate.ps1

python -m pip install scrapy
scrapy version -v
scrapy -h
```

> El PDF recomienda **registrar la versión instalada** para poder reproducir el proyecto, y consultar la documentación correspondiente a esa versión concreta.

En VS Code, selecciona el intérprete del entorno virtual (`Ctrl+Shift+P` → *Python: Select Interpreter* → elige `.venv`).

### Paso 5. Crear el proyecto Scrapy (diapositiva 6)

```bash
scrapy startproject recolector
cd recolector
scrapy genspider quotes quotes.toscrape.com
```

Estructura relevante (según el PDF):
- `recolector/spiders/`: spiders y reglas de extracción.
- `items.py`: definición opcional de los campos de los items.
- `pipelines.py`: limpieza y validación de los datos extraídos.
- `settings.py`: configuración. **Ejecutar los comandos de crawling desde la carpeta que contiene `scrapy.cfg`.**

### Paso 6. Sitio de práctica: Quotes to Scrape (diapositiva 7)

- Se usará *Quotes to Scrape*, un sitio de práctica.
- Cada página contiene varias citas; cada cita será un documento del corpus.
- Se extraerán **texto, autor y etiquetas**, y se seguirá el enlace a la siguiente página.
- Se conservarán la URL y la fuente, y se generará un identificador estable.
- **Requisito del proyecto**: añadir una **segunda fuente real** (no es un ejemplo, es una tarea que debes completar tú).

### Paso 7. Inspeccionar el HTML descargado (diapositiva 8)

- Localiza el contenedor de cada cita y sus elementos de texto, autor y etiquetas (usando las herramientas de desarrollador del navegador).
- **Comprueba los selectores sobre la respuesta que recibe Scrapy, no solo sobre el DOM del navegador** — este es el motivo del siguiente paso.

### Paso 8. Probar selectores con Scrapy shell (diapositiva 9)

```bash
scrapy shell "https://quotes.toscrape.com/"
```

Dentro de la shell:
```python
response.status
response.url
response.css("title::text").get()
len(response.css("div.quote"))
# shelp() muestra los objetos y atajos disponibles.
```

> La shell permite probar los selectores antes de escribir el spider. Entrecomillar las URLs evita que la terminal interprete caracteres como `&`.

### Paso 9. Selectores CSS: elementos y valores (diapositiva 10)

```python
q = response.css("div.quote")[0]
q.css("span.text::text").get()
q.css("small.author::text").get()
q.css("a.tag::text").getall()
response.css("li.next a::attr(href)").get()
```

- `.get()` devuelve la primera coincidencia o `None`. `.getall()` devuelve una lista.
- `::text` obtiene nodos de texto y `::attr(href)` el atributo del enlace.
- Extraer los campos **dentro de cada contenedor** evita mezclar el texto de una cita con el autor de otra.

### Paso 10. XPath y texto anidado (diapositiva 11)

```python
q.xpath('.//small[@class="author"]/text()').get()
q.xpath('.//a[@class="tag"]/text()').getall()

# Texto de un elemento, incluidos sus descendientes:
q.xpath('string(.//span[@class="text"])').get()
```

- XPath navega por el árbol HTML/XML y permite condiciones y funciones.
- `.//` busca desde el nodo actual; `//` empieza desde la raíz del documento.
- `::text` puede omitir texto dentro de elementos hijos. Comprobar siempre el HTML de la fuente.

### Paso 11. Extracción con expresiones regulares (diapositiva 12)

```python
response.css("title::text").re(r"Quotes.*")
# Lista de coincidencias sobre el texto seleccionado.

response.css("title::text").re_first(r"Quotes.*")
# Primera coincidencia, o None.
```

- Aplicar regex cuando interese un patrón dentro de un texto **ya localizado**.
- Usar CSS o XPath para navegar por la estructura del documento (no regex sobre el HTML entero).

Sal de la shell (`exit()` o `Ctrl+D`) y vuelve al proyecto en VS Code.

### Paso 12. Escribir el spider completo (diapositiva 13)

Edita el archivo `recolector/spiders/quotes.py` con el siguiente contenido exacto del PDF:

```python
# recolector/spiders/quotes.py
import scrapy

class QuotesSpider(scrapy.Spider):
    name = "quotes"
    allowed_domains = ["quotes.toscrape.com"]
    start_urls = ["https://quotes.toscrape.com/"]

    def parse(self, response):
        for q in response.css("div.quote"):
            autor = q.css("small.author::text").get("")
            yield {
                "titulo": "Cita de " + autor,
                "texto": q.css("span.text::text").get(""),
                "autor": autor,
                "categorias": q.css("a.tag::text").getall(),
                "url": response.url,
                "fuente": "quotes.toscrape.com"
            }
        siguiente = response.css("li.next a::attr(href)").get()
        if siguiente:
            yield response.follow(siguiente, callback=self.parse)
```

### Paso 13. Entender cómo funciona el spider (diapositiva 14)

- `name` identifica el spider al ejecutarlo. `start_urls` define las páginas iniciales.
- `allowed_domains` delimita los sitios permitidos para las peticiones del rastreo. También hay que seleccionar qué rutas seguir.
- `yield` puede entregar un **item** con datos o una **Request** que Scrapy descargará.
- `response.follow` resuelve enlaces relativos. Cuando llega la nueva respuesta, Scrapy invoca el callback.

### Paso 14. (Opcional) Definir Items con estructura declarada (diapositiva 15)

En `recolector/items.py`:

```python
# Alternativa opcional en recolector/items.py
import scrapy

class RecursoItem(scrapy.Item):
    id = scrapy.Field()
    titulo = scrapy.Field()
    texto = scrapy.Field()
    autor = scrapy.Field()
    categorias = scrapy.Field()
    url = scrapy.Field()
    fuente = scrapy.Field()
```

> El spider del Paso 12 ya usa diccionarios válidos. `Item` declara campos, pero **no valida automáticamente** sus tipos ni que estén completos.

### Paso 15. Pipeline: limpieza e identificador (diapositiva 16)

En `recolector/pipelines.py`:

```python
# recolector/pipelines.py
import hashlib
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem

class RecursoPipeline:
    def process_item(self, item, spider=None):
        a = ItemAdapter(item)
        a["texto"] = " ".join(a.get("texto", "").split())
        if not a["texto"] or not a.get("url"):
            raise DropItem("Falta texto o URL")
        clave = a["url"] + "|" + a["texto"]
        a["id"] = hashlib.sha256(clave.encode()).hexdigest()
        return item
```

> El argumento opcional `spider` permite usar este ejemplo con firmas antiguas y recientes. En versiones recientes basta `process_item(self, item)`.

### Paso 16. Identificadores y duplicados — criterios a decidir (diapositiva 17)

- El ejemplo combina URL y texto porque una página contiene varias citas.
- Si una ficha tiene una URL propia estable, puede ser mejor generar el ID a partir de esa URL.
- Con URL y texto, un cambio del texto crea otro ID: hay que decidir cómo actualizar o retirar documentos anteriores.
- El filtrado de **peticiones duplicadas** de Scrapy no elimina contenido repetido en distintas URLs; esa deduplicación pertenece al procesamiento de datos.

### Paso 17. Configurar `settings.py` para un crawling controlado (diapositiva 18)

Edita `recolector/settings.py` y añade/ajusta:

```python
ROBOTSTXT_OBEY = True
# Sustituir el contacto por el del grupo.
USER_AGENT = "RIWS-Crawler/1.0 (+mailto:grupo@example.org)"
CONCURRENT_REQUESTS_PER_DOMAIN = 2
DOWNLOAD_DELAY = 1
AUTOTHROTTLE_ENABLED = True
FEED_EXPORT_ENCODING = "utf-8"
ITEM_PIPELINES = {
    "recolector.pipelines.RecursoPipeline": 300,
}
```

- Las prioridades **menores** de los pipelines se ejecutan primero.
- Respetar las reglas del sitio y controlar frecuencia y alcance. Evitar bucles, parámetros infinitos y páginas fuera del dominio temático.

**Recuerda sustituir el `USER_AGENT` por el contacto real de tu grupo**, tal como indica el PDF.

### Paso 18. Ejecutar el spider y exportar (diapositiva 19)

Desde la carpeta que contiene `scrapy.cfg`:

```bash
scrapy crawl quotes -O recursos.jsonl
# Alternativa: un array JSON en un archivo distinto.
scrapy crawl quotes -O recursos.json
```

- `-O` sobrescribe el archivo. `-o` añade contenido cuando el formato lo permite (atención a duplicar datos en ejecuciones sucesivas).
- **JSONL**: un objeto JSON por línea, útil para procesar el corpus por lotes.
- Usar *feed exports* para guardar archivos; el pipeline se ocupa de la transformación y validación.

### Paso 19. Comprobar la extracción (diapositiva 20)

Crea un pequeño script de comprobación (por ejemplo `check.py`) con el contenido del PDF:

```python
import json

with open("recursos.jsonl", encoding="utf-8") as f:
    docs = [json.loads(linea) for linea in f]
print("Documentos:", len(docs))
print("IDs distintos:", len({d["id"] for d in docs}))
print("Fuentes:", {d["fuente"] for d in docs})
print(docs[:1])
```

> Esto es para una muestra pequeña. Revisar campos vacíos, duplicados, texto extraño y estadísticas del crawl. **No basta con que el proceso termine sin errores.**

### Paso 20. Añadir la segunda fuente (diapositiva 21) — tarea obligatoria del proyecto

El PDF indica el criterio a seguir:

- Crear **un spider por sitio** cuando tengan estructuras HTML diferentes.
- Extraer los datos con selectores específicos y **convertirlos al mismo conjunto de campos** que usa `quotes.py`.
- Conservar `fuente` y `url` para distinguir procedencia y permitir comprobaciones.
- Exportar cada fuente por separado y normalizar antes de combinar. No perder una fuente por sobrescribir el archivo.

```bash
scrapy crawl fuente_a -O fuente_a.jsonl
scrapy crawl fuente_b -O fuente_b.jsonl
```

> `fuente_a` y `fuente_b` son **nombres ilustrativos** del PDF: debes crear (con `scrapy genspider ...`) los spiders reales para las fuentes que elijas, siguiendo el mismo patrón de `quotes.py` (selectores CSS/XPath adaptados a cada sitio, mismo esquema de campos: `titulo`, `texto`, `autor`, `categorias`, `url`, `fuente`, `id`).

### Paso 21. Preparación para Elasticsearch (diapositiva 22)

- El archivo `recursos.jsonl` debe usar el **esquema del tutorial de Elasticsearch**, incluido el `id` generado por el pipeline.
- Crear un índice con tipos y analizador adecuados. Para citas en inglés, adaptar el analizador del ejemplo en castellano (del tutorial de Elasticsearch previo del curso).
- Usar la carga por lotes del tutorial de Elasticsearch y revisar los documentos rechazados.
- Conservar el corpus exportado permite reindexar sin repetir el crawling ni consumir otra vez tokens del LLM (si usas asistencia de IA en el proceso).

### Paso 22. Contenido dinámico y JavaScript (diapositiva 23) — si tu segunda fuente lo necesita

- Si los datos aparecen en el navegador pero faltan en `response.text`, inspecciona las peticiones de red del sitio.
- Cuando exista una respuesta JSON accesible y permitida, Scrapy puede solicitarla y procesarla directamente.
- Si hace falta renderizar JavaScript, integrar un navegador como **Playwright**. Esto añade dependencias y coste.
- Para empezar, elige páginas con HTML accesible. Una API aislada **no demuestra por sí sola** el crawling web requerido en el proyecto.

### Paso 23. Librerías complementarias (diapositiva 24, opcional)

- **Parsel / lxml**: selectores CSS y XPath (Scrapy ya los integra para sus respuestas).
- **BeautifulSoup**: API alternativa para navegar y extraer contenido de HTML/XML.
- **Playwright / Selenium**: automatización del navegador cuando se necesita ejecutar JavaScript.
- **w3lib / urllib.parse**: utilidades para trabajar con URLs.

Ejemplo de uso de BeautifulSoup dentro de un callback (diapositiva 25):

```python
# Alternativa de extraccion sobre una respuesta de Scrapy.
# Instalar antes: python -m pip install beautifulsoup4
from bs4 import BeautifulSoup

soup = BeautifulSoup(response.text, "html.parser")
for q in soup.select("div.quote"):
    nodo = q.select_one("span.text")
    if nodo is not None:
        texto = nodo.get_text(" ", strip=True)
        print(texto)

enlace = soup.select_one("li.next a")
siguiente = enlace.get("href") if enlace else None
```

> Fragmento ilustrativo: Scrapy sigue gestionando las descargas y la paginación; BeautifulSoup no sustituye al crawler.

### Paso 24. Diagnóstico del crawler (diapositiva 26)

Usa esta checklist si algo falla:

- **Cero items**: comprobar el estado HTTP, los selectores y el contenido real de la respuesta.
- **Solo la primera página**: revisar el enlace siguiente y la creación de nuevas peticiones.
- **Datos repetidos o incompletos**: revisar contenedores, normalización e identificadores.
- **Bloqueos o demasiadas peticiones**: respetar las restricciones, reducir ritmo y revisar el alcance. Consultar los logs antes de ampliar el rastreo.

### Paso 25. Documentación de referencia (diapositiva 27)

- Tutorial oficial de Scrapy
- Selectores / Scrapy shell
- Pipelines / Exportación de datos
- Configuración / Contenido dinámico

(Consulta la documentación correspondiente a la versión de Scrapy que registraste en el Paso 4.)

### Paso 26. Guardar el avance en GitHub

```bash
cd ~/ruta/a/tu-repo/scrapy-nutch-tutorial
git add recolector/ recursos.jsonl check.py
git commit -m "Scrapy: spider quotes + segunda fuente + pipeline + export JSONL"
git push
```

---

## PARTE 2 — Apache Nutch

### Paso 27. Qué es Apache Nutch (diapositiva 28)

- Es un *web crawler* extensible y escalable.
- Proporciona, entre otras cosas: web crawling; WebGraph y LinkRank; detección de formatos de documento y parsing; detección de lenguaje y codificación; mecanismo de extensión mediante plugins; soporte de múltiples *backends* de persistencia.
- Originalmente **Hadoop nació como parte de Nutch**.

### Paso 28. Elegir versión de Nutch (diapositiva 29)

Hay dos ramas soportadas:

- **Nutch 1.x**: versión madura. Usa estructuras de datos de Hadoop (HDFS).
- **Nutch 2.x**: versión más moderna. Emplea **Apache Gora** para gestionar la persistencia. Nutch 2.4 usa Gora 0.8, que soporta (entre otros backends): Apache Avro 1.8.1, Apache Hadoop 2.5.2, Apache HBase 1.2.3, Apache Cassandra 3.11.0, Apache Solr 6.5.1, MongoDB (driver) 3.5.0, Apache Accumulo 1.7.1, Apache Spark 1.4.1, Apache CouchDB 1.4.2, Amazon DynamoDB (driver) 1.10.55, Infinispan 7.2.5.Final, JCache 1.0.0 (con soporte Hazelcast 3.6.4), OrientDB 2.2.22, Aerospike 4.0.6.

> Esta guía sigue **Nutch 2.4 con MongoDB** como backend, tal como lo desarrolla el PDF paso a paso.

### Paso 29. Instalar Nutch 2.4 (I): descarga y agent name (diapositiva 30)

```bash
wget https://downloads.apache.org/nutch/2.4/apache-nutch-2.4-src
```

Configura Nutch en `conf/nutch-site.xml` (los valores por defecto están en `conf/nutch-default.xml`). Como mínimo hay que establecer el *agent name*:

```xml
<property>
<name>http.agent.name</name>
<value>My RIWS Spider 1.0</value>
</property>
```

### Paso 30. Instalar Nutch 2.4 (II): configurar MongoDB como backend (diapositiva 31)

1. Añade el backend en `conf/nutch-site.xml`:
```xml
<property>
<name>storage.data.store.class</name>
<value>org.apache.gora.mongodb.store.MongoStore</value>
<description>Class for storing data</description>
</property>
```

2. Descomenta el backend en `ivy/ivy.xml` y ajusta su versión:
```xml
<dependency org="org.apache.gora" name="gora-mongodb" rev="0.8" conf="*->default" />
```

3. Añade el backend en `conf/gora.properties`:
```
gora.mongodb.override_hadoop_configuration=false
gora.mongodb.mapping.file=/gora-mongodb-mapping.xml
gora.mongodb.servers=localhost:27017
gora.mongodb.db=nutch-riws
```

4. Compila el código:
```bash
ant runtime
```

### Paso 31. Instalar Nutch 2.4 (III): resolver dependencias que fallan (diapositiva 32)

Si falla la compilación porque no encuentra unas dependencias, añade un repositorio en `ivy/ivysettings.xml`:

```xml
<property name="repo.restlet"
value="https://maven.restlet.talend.com/"
override="false"/>
...
<resolvers>
<ibiblio name="restlet"
root="${repo.restlet}"
pattern="${maven2.pattern.ext}"
m2compatible="true"
/>
...
<chain name="default" dual="true">
<resolver ref="local"/>
<resolver ref="maven2"/>
<resolver ref="sonatype"/>
<resolver ref="apache-snapshot"/>
<resolver ref="spring-plugins"/>
<resolver ref="restlet"/>
</chain>
...
```

### Paso 32. Instalar y arrancar MongoDB 3.4.7 (diapositiva 33)

```bash
wget https://fastdl.mongodb.org/linux/mongodb-linux-x86_64-ubuntu1604-3.4.7.tgz
tar xzvf mongodb-linux-x86_64-ubuntu1604-3.4.7.tgz

mkdir data logs

./mongodb-linux-x86_64-ubuntu1604-3.4.7bin/mongod --dbpath data/ \
--logpath logs/mongo-riws.log
```

> Deja este proceso corriendo en una terminal de VS Code (o ábrelo en una segunda terminal integrada) mientras trabajas con Nutch.

### Paso 33. Usando Nutch 2.4 (I): configurar el esquema de Solr (diapositiva 34)

```bash
rm solr-8.4.1/server/solr/nutch-riws/conf/managed-schema
cp apache-nutch-2.4/conf/schema.xml \
solr-8.4.1/server/solr/nutch-riws/conf/
```

Después, en el `schema.xml` copiado al core de Solr:

- Elimina las ocurrencias de `enablePositionIncrements="true"`.
- Elimina `<solrQueryParser defaultOperator="OR"/>` y `<defaultSearchField>text</defaultSearchField>`.
- Comenta el bloque `<updateProcessor class="solr.AddSchemaFieldUpdateProcessorFactory" name="add-schema-fields">...` en `solr-8.4.1/server/solr/nutch-riws/conf/solrconfig.xml`, y elimina `add-schema-field` de la chain `"add-unknown-fields-to-the-schema"`.

### Paso 34. Usando Nutch 2.4 (II): arrancar Solr y añadir plugins (diapositiva 35)

```bash
# arranca Solr y comprueba en el navegador:
# http://localhost:8983/solr
```

Añade el plugin `indexer-solr` mediante la propiedad `plugin.includes` en `runtime/local/conf/nutch-site.xml`:

```xml
<property>
<name>plugin.includes</name>
<value>protocol-http|urlfilter-regex|
parse-(html|tika)|index-(basic|anchor)|
urlnormalizer-(pass|regex|basic)|
scoring-opic|indexer-solr</value>
</property>
```

### Paso 35. Usando Nutch 2.4 (III): definir alcance y lanzar el crawling (diapositiva 36)

1. Restringe el crawling al dominio deseado. Edita `runtime/local/conf/regex-urlfilter.txt` (indica qué URLs se pueden explorar) y cambia la última línea por:
```
+^https://www.fic.udc.es
```
> Sustituye este dominio por el que corresponda a tu propio crawling, siguiendo el mismo patrón `+^https://...`.

2. Añade las URLs semilla:
```bash
mkdir runtime/local/urls
echo "https://www.fic.udc.es/" > \
runtime/local/urls/seed.txt
```

3. Inicia el crawling:
```bash
cd runtime/local
bin/nutch inject urls
bin/nutch generate -topN 25
bin/nutch fetch -all
bin/nutch parse -all
bin/nutch updatedb -all
```

### Paso 36. Usando Nutch 2.4 (IV): indexar en Solr y consultar (diapositiva 37)

- Puedes repetir los últimos cuatro comandos del Paso 35 para profundizar en el crawling.
- Para pasar los datos de HBase/Gora a Solr:
```bash
bin/nutch solrindex http://localhost:8983/solr/nutch-riws -all
```
- Para consultar los datos importados:
```
http://localhost:8983/solr/#/nutch-riws/query
```
- Para definir nuevos campos en el crawling de Nutch o nuevas reglas de *parsing*, crea un **plugin**. Para indexar los nuevos campos en Solr, edita el `schema.xml`. Tutorial de referencia con ejemplo para almacenar metatags de las webs:
```
http://wiki.apache.org/nutch/IndexMetatags
```
- Clase de referencia relacionada:
```
src/plugin/index-metadata/src/java/org/apache/nutch/
indexer/metadata/MetadataIndexer.java
```

### Paso 37. Documentación de referencia de Nutch (diapositiva 38)

- Wiki de Nutch: `https://wiki.apache.org/nutch`
- Tutorial de Nutch 2: `http://wiki.apache.org/nutch/Nutch2Tutorial`
- Interfaz web autocontenida de Nutch: `https://issues.apache.org/jira/browse/NUTCH-841`
- Documentación del API REST de Nutch: `https://wiki.apache.org/nutch/NutchRESTAPI`

### Paso 38. Debugging (diapositiva 39)

- Cuando haya algún problema, consulta los **logs**. Todos los proyectos Apache tienen una carpeta `logs`.
- Si Nutch da problemas, comprueba que el *backend* de almacenamiento (MongoDB) está funcionando correctamente.
- Si no eres capaz de *crawlear* un sitio web, comprueba que no hay problemas de conexión y que la web no está bloqueando el rastreo. Puede ser útil cambiar el `useragent` de Nutch por otro de un navegador común, por ejemplo:
```
Mozilla/5.0 (X11; Linux x86_64; rv:42.0) Gecko/20...
```

### Paso 39. Guardar el avance de Nutch en GitHub

```bash
cd ~/ruta/a/tu-repo/scrapy-nutch-tutorial
git add nutch-config-notes.md   # tus notas de configuración (no subas binarios pesados ni datos de MongoDB)
git commit -m "Nutch 2.4 + MongoDB: configuración, crawling y volcado a Solr"
git push
```

> Nota: no subas al repo los binarios descargados (Nutch, MongoDB, Solr) ni las carpetas `data/`/`logs/`. Añádelos a un `.gitignore` si comparten carpeta con tu repo.

---

## Resumen de entregables del proyecto (según el PDF)

1. Spider Scrapy `quotes` funcionando (dado).
2. **Un segundo spider Scrapy** para una fuente real distinta, con el mismo esquema de campos (`titulo`, `texto`, `autor`, `categorias`, `url`, `fuente`, `id`).
3. Pipeline de limpieza y generación de `id` aplicado a ambas fuentes.
4. Exportación en JSONL de cada fuente, revisada con el script de comprobación.
5. Corpus preparado según el esquema del tutorial de Elasticsearch, listo para indexar.
6. Configuración y ejecución de un crawling con Apache Nutch 2.4 (o la rama que elijas) sobre un dominio propio, con volcado a Solr.
