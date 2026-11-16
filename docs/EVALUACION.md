<!-- evaluacion:inicio -->
# Evaluación — ticketera-titopalo/backend-interfaz-de-administraci-n-palomajunent

> Documento **generado automáticamente** por la cátedra de Programación III (RepoSense + análisis de calidad + constancia). **No editar a mano**: se regenera en cada evaluación.
> Rama evaluada: `main`. Análisis **heurístico** (regex + métricas): es una criba para orientar la revisión, **no una nota**.
> Generado: 2026-11-16.

## 1. Veredicto

| Aspecto | Resultado |
|---|---|
| Tipo de proyecto | backend |
| Índice de calidad de servicios | **89/100** (mínimo 50) |
| Criterios cumplidos | **14/15** |
| Aprobado (semáforo) | **SI** |
| Código (LOC) | 1,184 |
| Archivos de código | 16 |
| Tests (archivos) | 6 |
| Cobertura de líneas | 90.9% (mínimo 80%) |
| Capas detectadas | presentacion, logica, datos |
| Pushes directos a `main` (sin PR) | 0 |

> **Aprobado** exige las compuertas críticas (**SEC**, **SQL**, **capas**, **índice ≥ 50** y **cobertura ≥ 80 %** cuando aplica) y tolera hasta **3 criterios en rojo** (12/15). No es una nota: sirve para ordenar y priorizar la revisión.

## 2. Autoría (RepoSense)

| Autor | Commits | Código (LOC) | Tests (LOC) | Docs (LOC) | Días activos | % del código |
|---|---:|---:|---:|---:|---:|---:|
| palojunent | 21 | 1,873 | 0 | 23 | 7 | 100% |

> _El LOC de autoría lo calcula RepoSense sobre el historial y puede diferir del LOC de código del análisis de calidad (que mira solo el estado de `main`)._

## 3. Constancia (IC) — todas las ramas

> El IC mide **cuándo** se trabajó (sesiones por semana, pausas y recencia), no cuánto ni con qué calidad. Se calcula sobre **todas las ramas** de todos los repositorios del alumno, no sólo `main`.

| Alumno | Sesiones | Cumplimiento | Pausa | Recencia | IC | Nivel | Para subir de nivel |
|---|--:|--:|--:|--:|--:|--|--|
| palojunent | 14 | 52% | 28 d | 86% | **46** | Aprueba | Cumplimiento 52% (mín. 100%); Pausa 28 d (máx. 5 d) |

> Para aprobar el IC: **2 sesiones por semana** sostenidas, sin pausas mayores a **10 días** y con actividad en las **últimas 2 semanas**. Se excluyen merges, bots y al docente. Zona horaria UTC-3.

## 4. Aspectos evaluados

Cada aspecto indica **qué mide**, **por qué importa** y **tu resultado**. Cuando el resultado está en rojo, se agregan preguntas para **investigar la causa** (no hay recetas: entender el porqué es parte de la evaluación).

### 1. Índice de calidad de servicios (indice) — OK

- **Qué mide:** Un resumen numérico (0-100) que combina todas las señales y métricas del análisis, con topes duros por duplicación.
- **Por qué importa:** Ordena y prioriza la revisión: un índice bajo indica varias señales que conviene mirar juntas.
- **Tu resultado:** índice **89/100** _(mínimo 50)_

### 2. Duplicación (DRY) (duplicacion) — OK

- **Qué mide:** Porcentaje de bloques de código repetidos (similitud) en el repositorio.
- **Por qué importa:** Cada copia se mantiene por separado: un arreglo hay que repetirlo y los defectos se multiplican.
- **Tu resultado:** **3.1%** de duplicación _(máximo 15%)_

### 3. Secretos hardcodeados (SEC) — OK

- **Qué mide:** Credenciales, tokens o claves escritos directamente en el código en vez de leerse de variables de entorno.
- **Por qué importa:** Un secreto en el repositorio queda expuesto en el historial aunque luego se borre, y compromete al servicio y a sus usuarios.
- **Tu resultado:** **0** secreto(s) hardcodeado(s) _(máximo 0)_

### 4. Consultas SQL por concatenación (SQL) — OK

- **Qué mide:** Consultas SQL armadas concatenando o interpolando valores en vez de usar parámetros.
- **Por qué importa:** Es la puerta clásica a inyección: un valor que llega de afuera puede cambiar la consulta.
- **Tu resultado:** **0** consulta(s) SQL por concatenación _(máximo 0)_

### 5. Separación en capas (capas) — OK

- **Qué mide:** Si el código está separado en capas reconocibles (backend: presentación / lógica / datos; frontend: vistas / servicios / estado).
- **Por qué importa:** Sin separación, cada archivo hace de todo y cualquier cambio toca varios lugares a la vez.
- **Tu resultado:** **3** capa(s) detectada(s): presentacion, logica, datos _(mínimo 2 capas (a partir de 150 LOC))_

### 6. Acceso a datos dentro del componente (HTTP) — OK

- **Qué mide:** Llamadas `fetch`/`axios` dentro de componentes de UI en vez de una capa de servicios/API.
- **Por qué importa:** Duplica la lógica de acceso a datos y acopla la vista al backend: un cambio de API toca muchos componentes.
- **Tu resultado:** **0** llamada(s) a la API dentro de componente(s) _(máximo 0)_

### 7. Depuración olvidada (DBG) — OK

- **Qué mide:** Mensajes de depuración olvidados (`console.log`, `print`, `debugger`).
- **Por qué importa:** Generan ruido en los registros, pueden filtrar datos y dan sensación de código sin terminar.
- **Tu resultado:** **0** mensaje(s) de depuración olvidado(s) _(máximo 0)_

### 8. Uso del tipo `any` (Any) — OK

- **Qué mide:** Uso de `any` en TypeScript, que desactiva la verificación de tipos.
- **Por qué importa:** Se pierde la ayuda del compilador justo donde los datos vienen de afuera (API, formularios).
- **Tu resultado:** **0** uso(s) de `any` _(máximo 2)_

### 9. Componente demasiado grande (BigC) — OK

- **Qué mide:** Componentes de UI muy extensos, que suelen mezclar render, estado y lógica.
- **Por qué importa:** Son difíciles de leer, probar y reutilizar, y sus cambios tienen efectos inesperados.
- **Tu resultado:** **0** componente(s) demasiado grande(s) _(máximo 1)_

### 10. Baja cohesión (Coh) — OK

- **Qué mide:** Una clase o unidad cuyos métodos y campos no están relacionados entre sí.
- **Por qué importa:** Una unidad que cambia por motivos distintos es frágil y cuesta entenderla.
- **Tu resultado:** **0** unidad(es) con baja cohesión _(máximo 0)_

### 11. Complejidad alta (Compl) — OK

- **Qué mide:** Complejidad ciclomática: cantidad de caminos posibles dentro de una función (condicionales, bucles, casos).
- **Por qué importa:** Muchos caminos = difícil de seguir y de probar; suelen esconderse casos sin cubrir.
- **Tu resultado:** **1** bloque(s) de complejidad alta _(máximo 5 por 1000 LOC (tenés 1184 LOC))_

### 12. Funciones/métodos largos o con muchos parámetros (Tam) — OK

- **Qué mide:** Tamaño de las funciones/métodos y cantidad de parámetros.
- **Por qué importa:** Una función que hace varias cosas cuesta leerla, nombrarla y reutilizarla.
- **Tu resultado:** **3** función/método(s) largos o con muchos parámetros _(máximo 10 por 1000 LOC)_

### 13. Acoplamiento alto (Acop) — A REVISAR

- **Qué mide:** Cuánto depende una unidad de las partes internas de otra.
- **Por qué importa:** Piezas muy enlazadas hacen que un cambio se propague y que sea difícil reemplazar partes.
- **Tu resultado:** **3** unidad(es) con acoplamiento alto _(máximo 2 por 1000 LOC)_
- **Para investigar la causa:**
    - ¿Las piezas se conocen en detalle entre sí (acceden a campos o estructuras internas)?
    - ¿El acceso a datos ocurre desde lugares que no son los responsables?
    - ¿Se puede cambiar una parte sin tocar las demás?

### 14. Cobertura de tests (Cob) — OK

- **Qué mide:** Porcentaje de líneas de código ejecutadas por la suite de tests (cobertura real, no cantidad de archivos de test).
- **Por qué importa:** Un test que existe pero no ejecuta el código no protege de nada: la cobertura muestra qué partes quedan sin verificar.
- **Tu resultado:** **90.9%** de líneas cubiertas · fuente: ejecución: pytest _(mínimo 80% de líneas)_

### 15. Endpoints del backend (EP) — OK

- **Qué mide:** Cantidad de endpoints (rutas HTTP) expuestos por el backend.
- **Por qué importa:** El backend se mide por lo que expone: pocos endpoints sugiere poca funcionalidad de servicio.
- **Tu resultado:** **38** endpoint(s) _(mínimo 5)_

## 5. Observaciones y qué falta

**Aprobado con observaciones.** Estos criterios quedan en rojo (se permiten hasta **3** sin que sean compuertas críticas), así que no bloquean la aprobación pero conviene corregirlos:

| Criterio | Resultado actual | Meta | Brecha | Cómo alcanzarlo |
|---|---|---|---|---|
| Acoplamiento alto (Acop) | **3** unidad(es) con acoplamiento alto | máximo 2 por 1000 LOC | 3 hallazgo(s); el máximo para 1,184 LOC es 2.4 | Hacé que cada unidad dependa de una interfaz o de un módulo de servicio, no de los detalles internos de otra; evitá acceder a campos ajenos. Meta: ≤2 por 1000 LOC. |

## 6. Actividad en clase y fuera de clase

> Se consideran las **27 clases** del período (miércoles y viernes, según `config/constancia.json`; feriados y semanas sin clase descontados). Para cada alumno se muestra la actividad **en cada clase** y también la actividad **fuera de los días de clase** (fines de semana u otros días). `Commits` = commits de trabajo (no-merge); `Merges` = merges de PR (también son push). Los días sin actividad dicen **sin actividad**.

### joaquin ardevol

**12/27 clases con actividad** · total del período: 30 commits · 29 merges

| Fecha | Actividad | Repositorios | Commits / merges |
|---|:--:|---|--:|
| 2026-08-14 | No | sin actividad | 0 / 0 |
| 2026-08-19 | **Sí** | frontend_interface-client-JoacoArdevol | 1 / 0 |
| 2026-08-21 | **Sí** | frontend_interface-client-JoacoArdevol | 1 / 0 |
| 2026-08-26 | No | sin actividad | 0 / 0 |
| 2026-08-28 | No | sin actividad | 0 / 0 |
| 2026-09-02 | **Sí** | frontend_interface-client-JoacoArdevol | 1 / 2 |
| 2026-09-04 | No | sin actividad | 0 / 0 |
| 2026-09-09 | No | sin actividad | 0 / 0 |
| 2026-09-11 | No | sin actividad | 0 / 0 |
| 2026-09-16 | No | sin actividad | 0 / 0 |
| 2026-09-18 | No | sin actividad | 0 / 0 |
| 2026-09-23 | No | sin actividad | 0 / 0 |
| 2026-09-25 | No | sin actividad | 0 / 0 |
| 2026-09-30 | **Sí** | frontend_interface-client-JoacoArdevol | 1 / 1 |
| 2026-10-02 | No | sin actividad | 0 / 0 |
| 2026-10-07 | No | sin actividad | 0 / 0 |
| 2026-10-09 | No | sin actividad | 0 / 0 |
| 2026-10-14 | No | sin actividad | 0 / 0 |
| 2026-10-16 | **Sí** | frontend_interface-client-JoacoArdevol | 2 / 1 |
| 2026-10-21 | **Sí** | frontend_interface-client-JoacoArdevol | 1 / 2 |
| 2026-10-23 | **Sí** | frontend_interface-client-JoacoArdevol | 0 / 2 |
| 2026-10-28 | **Sí** | frontend_interface-client-JoacoArdevol | 5 / 4 |
| 2026-10-30 | **Sí** | frontend_interface-client-JoacoArdevol | 7 / 5 |
| 2026-11-04 | No | sin actividad | 0 / 0 |
| 2026-11-06 | **Sí** | frontend_interface-client-JoacoArdevol | 1 / 3 |
| 2026-11-11 | **Sí** | frontend-interface-administracion-joacoardevol | 9 / 8 |
| 2026-11-13 | **Sí** | frontend-interface-administracion-joacoardevol | 1 / 1 |

**Fuera de clase:** 1 fecha(s) con actividad · 2 commits · 2 merges

| Fecha | Repositorios | Commits / merges |
|---|---|--:|
| 2026-11-15 | frontend-interface-administracion-joacoardevol, frontend_interface-client-JoacoArdevol | 2 / 2 |

### palojunent

**15/27 clases con actividad** · total del período: 43 commits · 32 merges

| Fecha | Actividad | Repositorios | Commits / merges |
|---|:--:|---|--:|
| 2026-08-14 | No | sin actividad | 0 / 0 |
| 2026-08-19 | **Sí** | backend-interfaz-de-cliente--palomaju-ent | 1 / 0 |
| 2026-08-21 | No | sin actividad | 0 / 0 |
| 2026-08-26 | No | sin actividad | 0 / 0 |
| 2026-08-28 | No | sin actividad | 0 / 0 |
| 2026-09-02 | **Sí** | backend-interfaz-de-cliente--palomaju-ent | 2 / 2 |
| 2026-09-04 | **Sí** | backend-interfaz-de-cliente--palomaju-ent | 2 / 0 |
| 2026-09-09 | **Sí** | backend-interfaz-de-cliente--palomaju-ent | 1 / 3 |
| 2026-09-11 | No | sin actividad | 0 / 0 |
| 2026-09-16 | No | sin actividad | 0 / 0 |
| 2026-09-18 | No | sin actividad | 0 / 0 |
| 2026-09-23 | No | sin actividad | 0 / 0 |
| 2026-09-25 | No | sin actividad | 0 / 0 |
| 2026-09-30 | **Sí** | backend-interfaz-de-cliente--palomaju-ent | 0 / 1 |
| 2026-10-02 | No | sin actividad | 0 / 0 |
| 2026-10-07 | **Sí** | backend-interfaz-de-cliente--palomaju-ent | 1 / 1 |
| 2026-10-09 | **Sí** | backend-interfaz-de-cliente--palomaju-ent | 1 / 1 |
| 2026-10-14 | **Sí** | backend-interfaz-de-cliente--palomaju-ent | 3 / 3 |
| 2026-10-16 | **Sí** | backend-interfaz-de-cliente--palomaju-ent | 4 / 3 |
| 2026-10-21 | No | sin actividad | 0 / 0 |
| 2026-10-23 | **Sí** | backend-interfaz-de-cliente--palomaju-ent | 0 / 1 |
| 2026-10-28 | **Sí** | backend-interfaz-de-cliente--palomaju-ent | 3 / 3 |
| 2026-10-30 | **Sí** | backend-interfaz-de-administraci-n-palomajunent | 4 / 1 |
| 2026-11-04 | No | sin actividad | 0 / 0 |
| 2026-11-06 | **Sí** | backend-interfaz-de-administraci-n-palomajunent | 14 / 8 |
| 2026-11-11 | **Sí** | backend-interfaz-de-administraci-n-palomajunent | 4 / 4 |
| 2026-11-13 | **Sí** | backend-interfaz-de-administraci-n-palomajunent | 3 / 1 |

**Fuera de clase:** 3 fecha(s) con actividad · 5 commits · 10 merges

| Fecha | Repositorios | Commits / merges |
|---|---|--:|
| 2026-11-12 | backend-interfaz-de-administraci-n-palomajunent, backend-interfaz-de-cliente--palomaju-ent | 3 / 4 |
| 2026-11-14 | backend-interfaz-de-administraci-n-palomajunent | 2 / 3 |
| 2026-11-15 | backend-interfaz-de-administraci-n-palomajunent | 0 / 3 |

## 7. Anexo: dónde mirar

Archivos donde el análisis encontró cada señal en rojo (sin número de línea, a propósito):

**Acoplamiento alto (Acop)** — 3 archivo(s):
- `app/models/purchase.py`
- `app/routes/concerts.py`
- `app/routes/users.py`

---
_Informe generado por la cátedra. Los umbrales corresponden al perfil `exigente`. Ante dudas, revisá el archivo señalado y el criterio en `CRITERIOS-CALIDAD.md`._
<!-- evaluacion:fin -->
