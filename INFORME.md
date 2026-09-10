# TP Nivelador: Docker, Comunicaciones y Concurrencia
Retamozo Melina, 110065

## Protocolo implementado

Para poder compartir información de apuestas desde una agencia hacia el servidor central elegí la comunicación basada en stream de bytes, por lo tanto tuve que implementar también un protocolo que garantice la correcta serialización de los datos.

### Modelado de una apuesta

```
Bet:
    first_name  string  
    last_name   string 
    document    uint32
    birth_date  string 
    number      uint32
    agency_id   uint32
```

El ordenamiento de los campos viene dado por el archivo .csv de entrada. Se agrega el campo `agency_id` para que el servidor pueda identificar a quien pertenece cada apuesta al momento de devolver los ganadores.

### Serialización

Para la serialización a bytes se utilizó un formato Type-Length-Value de la siguiente forma:

```
TOTAL LENGTH (4B)
------------
FIELD_TYPE (1B)     FIELD_LENGTH (2B)        FIELD_VALUE 
...
```

De esta forma cuando el receptor quiere deserializar un arreglo de bytes a una apuesta primero lee el `TOTAL_LENGTH` y con eso puede obtener todos los bytes pertenecientes a la misma. Luego leerá primero el tipo de campo que es un enum y se usa para hacer un switch y almacenar cada dato en un struct de apuesta, con el `FIELD_LENGTH` puede saber hasta donde leer para el dato actual y sabe que lo siguiente en el arreglo de bytes será otro campo o la finalización del mismo.

### Serialización por batches

Un requerimiento de este trabajo era permitir enviar múltiples apuestas en un mismo mensaje, para garantizar que el servidor pueda leer correctamente todos los datos el protocolo implementado para un batch es el siguiente:

```
TOTAL_LENGTH_BATCH (4B)
------------------
AGENCY_ID (4B)   [ARREGLO DE APUESTAS SERIALIZADAS]
```

Se serializa cada apuesta por separado siguiendo el formato ya mencionado, se agrega un campo de `AGENCY_ID` adelante para que el servidor pueda separar las apuestas recibidas sin tener que leer los datos de cada una de ellas. Para el `TOTAL_LENGTH_BATCH` se toman en cuenta los 4 bytes del identificador de la agencia y se le suma el tamaño total del arreglo de apuestas.

El caso de batch no es simétrico, en el caso de la respuesta de ganadores por parte del servidor no inlcuye el `AGENCY_ID` porque sería información redundante para la agencia que la recibe.

### Acknowledgement

Cuando el servidor recibe un batch envía un mensaje de confirmación de la recepción con el siguiente formato:

```
1
```
Es un único byte que confirma que se recibió correctamente los datos enviados, al no contener información relevante se priorizó que sea rápido y fácil de interpretar.

### End of Transmission (EOT)

Para anunciar que se terminaron de enviar datos se usa un mensaje especial EOT que utiliza un FieldType igual a 0 y se serializa de la siguiente forma:
```
TOTAL_LENGHT (4B)
-----------------
0 (FIELD TYPE 1B)  0 (FIELD LENGTH 2B)
```

## Herramientas de concurrencia

### Hilos por cliente

### Locks para recursos compartidos

El recurso compartido por todos los hilos de los clientes es el archivo .csv donde el servidor almacena todas las apuestas. Para evitar condiciones de carrera se usa `threading.Lock` mediante los métodos `safe_store_bets()`, `safe_load_bets()`

### Barreras para el quorum

### Eventos para los resultados

