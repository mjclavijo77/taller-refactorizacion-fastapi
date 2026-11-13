1  Diagnostico Tecnico

A. Violacion de Principios SOLID
Single Responsibility Principle (SRP): En el archivo routers/checkout.py estamos violando este principio porque el controlador tiene demasiadas tareas en un solo flujo (transacciones, pagos, facturas y notificaciones). Un archivo de rutas solo deberia de encargarse de recibir la peticion HTTP y devolver una respuesta pero aqui se comporta como : cobra, descuenta stock, genera PDFs y manda correos. El problema de esto es que si la libreria del PDF llega a fallar se nos cae todo el endpoint de pago lo mismo ocurre en la clase NotificationDispatcher, que agrupa la logica de envio de miltiples canales en una sola funcion.

Open/Closed Principle (OCP): viola el principio de "abierto a extensiones, cerrado a modificación" en la clase NotificationDispatcher. Como usa bloques if/elif para comprobar los canales si el dia de mañana el negocio nos pide agregar notificaciones por WhatsApp, nos tocaria entrar a modificar ese archivo directamente y podriamos llegar a dañar algo.Lo correcto seria crear una clase independiente para la nueva funcionalidad sin tocar el codigo existente.

Dependency Inversion Principle (DIP): tambien no cumple con este principio ya que las rutas en routers/checkout.py dependen de implementaciones concretas, instanciando clases como TransactionManager() y StripePaymentGateway() directamente. Al amarrar nuestra logica principal a implementaciones exactas, se vuelve imposible poder hacer pruebas unitarias limpias, si intentamos correr hacer alguna prueba terminariamos ejecutando cobros reales en Stripe. Si dependieramos de abstracciones, podriamos inyectar un "Mock" para poder hacer estas pruebas sin llegar a afectar el sistema real.

B. Impacto de operaciones sincronas bloqueantes
FastAPI maneja la concurrencia de forma asincrona usando un unico hilo (el Event Loop). Podemos imaginar este hilo como un unico mesero que debe atender todo un restaurante. Al introducir operaciones sincronas bloqueantes dentro del código como time.sleep(0.5) y las peticiones HTTP con requests.post, obligamos a ese "mesero" a quedarse quieto en una sola mesa esperando a que termine un proceso. Esto crea un cuello de botella problematico: mientras espera el servidor queda totalmente incapacitado para procesar las peticiones simultáneas de otros usuarios.

C. Analisis matematico del stock 
El metodo begin_transaction sufre de una grave falla de concurrencia conocida como "condicion de carrera" al no contar con un bloqueo transaccional. El codigo obtiene el stock actual y aplica una pausa de 0.5 segundos antes de actualizar el valor, lo que genera el siguiente escenario:

Si el inventario de "PROD-A99" es de 10 unidades y 10 clientes intentan comprar 2 unidades en el mismo milisegundo

Las 10 peticiones van a la memoria al mismo tiempo y todas leen que el stock actual es 10.

Como todas leyeron un 10, todas hacen la validación matemática (10 >= 2), dando True para todas.

Las 10 transacciones hacen la resta en paralelo (10 - 2 = 8) y sobrescriben la base de datos con el número 8.

Matematicamente terminamos vendiendo 20 productos cuando solo teniamos 10 en existencia, pero la base de datos se piso a si misma y el registro final afirma que todavia nos quedan 8 disponibles, destruyendo la integridad del sistema.