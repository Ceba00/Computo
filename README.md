# chat

## Funcionamiento General

Este es un servidor que utiliza sockets por medio de una conexion TCP para simular un chat similar a los [clientes IRC](https://en.wikipedia.org/wiki/IRC) como [weechat](https://weechat.org/).

Permite enviar mensajes globales o privados por medio de `/msg <user> <msg>` o por medio de JSON (explicado posteriormente). El servidor utiliza hilos con `threading` para manejar a cada cliente con un diccionario y un lock para manejar la lista de usuarios conectados.

El servidor se crea utilizando `socket`:

```python
socket.socket(socket.AF_INET, socket.SOCK_STREAM)
```

Donde:

* `AF_INET` indica el uso de **direcciones IPv4**
* `SOCK_STREAM` indica el uso del **protocolo TCP**

> Las abreviaciones son heredadas de C

Para permitir que múltiples clientes se conecten simultáneamente cada que se conecta uno nuevo se delega a un hilo nuevo:

```python
thread = threading.Thread(target=handle_client, args=(conn, addr))
thread.start()
```

Dado que múltiples hilos pueden acceder al diccionario de clientes al mismo tiempo, existe el riesgo de _race conditions_:

* un hilo podría estar enviando mensajes
* mientras otro elimina un usuario desconectado

```python
# ejemplo
with clients_lock:
    clients[username] = conn
```

## Tipos de Mensajes

Se utiliza JSON para estructurar la comunicación entre cliente y servidor.

Ejemplo de mensaje global:

```json
{
  "type": "broadcast",
  "message": "Hola a todos"
}
```

Ejemplo de mensaje privado:

```json
{
  "type": "private",
  "to": "usuario",
  "message": "Hola"
}
```

Esto permite que el cliente pueda ser implementado de una manera muy sencilla.

> El _overhead_ del formato JSON en este caso es despreciable debido al alcance del proyecto

## Comandos

El sistema permite el uso de _comandos_ como `/users` y `/msg`:

```
/msg <user> <msg>
```

El servidor procesa este comando y envía el mensaje únicamente al destinatario.

```
/users
```

## Conexiones

Cuando un usuario se conecta:

1. el cliente envía un mensaje de login
2. el servidor registra el nombre
3. se añade al diccionario de clientes
4. se notifica a los demás usuarios

Ejemplo de mensaje del sistema:

```
<user> joined the chat
```

Cuando el usuario se desconecta:

1. se elimina del diccionario
2. se envía una notificación al chat

```
<user> left the chat
```

## Manejo de Errores

El servidor utiliza bloques `try/except` para manejar errores como:

* desconexión inesperada de clientes
* errores de red
* mensajes mal formateados

Esto evita que el servidor se detenga si un cliente falla.

## Escalabilidad y Rendimiento

El modelo utilizado es un hilo por cliente, debido a que es una implementación sencilla y para la magnitud del proyecto es mas que suficiente. Para mejorar el sistema se podrian usar eventos.

