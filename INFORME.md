# TP Nivelador: Docker, Comunicaciones y Concurrencia

Retamozo Melina, 110065

## Protocolo implementado

Para la transmisión de las apuestas desde las agencias hacia el servidor central, se optó por una comunicación basada en un flujo de bytes sobre TCP, lo que requirió el diseño de un protocolo propio para garantizar la correcta serialización y delimitación de los datos.

### Modelado de una apuesta

```
Bet:
    first_name  string  
    last_name   string 
    document    uint32
    birthdate   string 
    number      uint32
    agency_id   uint32

```

El ordenamiento de los campos está dado por el archivo .csv de entrada. Se agregó el campo `agency_id` para que el servidor pueda identificar a qué agencia pertenece cada apuesta al momento de devolver los ganadores.

### Serialización

Para la serialización a bytes se utilizó un formato Type-Length-Value estructurado de la siguiente forma:

```
TOTAL_LENGTH (4B)
-----------------
FIELD_TYPE (1B)     FIELD_LENGTH (2B)        FIELD_VALUE 
...

```

Al deserializar un arreglo de bytes a una apuesta, el receptor lee primero el campo `TOTAL_LENGTH` para determinar la cantidad total de bytes del registro. Luego, procesa secuencialmente cada atributo identificando su tipo mediante un enum `FIELD_TYPE` y su extensión mediante `FIELD_LENGTH`, lo que permite asignar cada dato al atributo correspondiente dentro de la estructura de la apuesta.

### Serialización por batches

Para permitir el envío de múltiples apuestas en un mismo mensaje, el protocolo para un lote se definió de la siguiente manera:

```
TOTAL_LENGTH_BATCH (4B)
----------------------
AGENCY_ID (4B)   [ARREGLO DE APUESTAS SERIALIZADAS]

```

Cada apuesta se serializa por separado siguiendo el formato TLV. Se antecede un campo `AGENCY_ID` para que el servidor identifique el origen del lote sin necesidad de inspeccionar cada apuesta individual. Para el cálculo de `TOTAL_LENGTH_BATCH`, se contemplan los 4 bytes del identificador de la agencia más la suma del tamaño total del arreglo de apuestas.

El protocolo de lotes es asimétrico: la respuesta del servidor con la lista de ganadores no incluye el encabezado `AGENCY_ID`, dado que resulta una información redundante para la agencia receptora.

### Acknowledgement

Tras la recepción correcta de un lote, el servidor responde con un mensaje de confirmación con el siguiente formato:

```
1

```

Consiste en un único byte que confirma la recepción exitosa de los datos. Al no requerir información adicional, se priorizó un formato liviano para minimizar el overhead de red y agilizar el procesamiento.

### End of Transmission (EOT)

Para anunciar la finalización de la transmisión de datos, se envía un mensaje especial EOT que utiliza un `FIELD_TYPE` igual a 0, serializado de la siguiente forma:

```
TOTAL_LENGTH (4B)
-----------------
0 (FIELD_TYPE 1B)  0 (FIELD_LENGTH 2B)

```

---

## Herramientas de concurrencia

### Hilos por cliente

Se implementó un esquema de concurrencia multihilo. El Global Interpreter Lock (GIL) de Python no representa un límite en el rendimiento para este diseño, ya que el sistema es predominantemente I/O-bound (lectura/escritura en red y archivos) y no realiza operaciones intensivas de CPU.

### Locks para recursos compartidos

El recurso compartido por los hilos de los clientes es el archivo `.csv` donde el servidor almacena las apuestas. Para evitar condiciones de carrera, se utiliza `threading.Lock` mediante los métodos `store_bets_safe()` y `safe_load_bets()`, los cuales garantizan exclusión mutua durante las operaciones de lectura y escritura en disco.

### Barreras para el quórum

Se utilizaron dos barreras de tipo `threading.Barrier`:

* Primera barrera (`quorum`): Asegura que exista un mínimo de agencias en espera (`AGENCY_QUORUM_MIN`) antes de realizar el sorteo. Mediante el orden de llegada (`wait()`), el hilo que obtiene el índice `0` asume la responsabilidad de ejecutar el sorteo y registrar los ganadores.
* Segunda barrera (`reset_quorum`): Sincroniza la lectura de ganadores asegurando que todas las agencias hayan procesado sus resultados antes de reiniciar el estado global para una nueva ejecución.

### Eventos para los resultados

Dado que solo el hilo con índice `0` realiza la carga de apuestas y determinación de ganadores, los demás hilos deben esperar a que los resultados se encuentren disponibles. Para esta coordinación se utilizó un `threading.Event`, bloqueando la ejecución de los demás hilos hasta que el hilo ejecutor habilite la lectura de los resultados.