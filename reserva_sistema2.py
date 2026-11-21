"""Segunda mitad del proyecto: clase Reserva, clase Sistema y demostración de operaciones.
Cada bloque está comentado para explicar qué hace y por qué."""
import logging  # Módulo estándar para escribir el archivo de logs

# IMPORTANTE: 'primera_parte' es el nombre del archivo de mi compañero (excepciones,
# Entidad, Cliente y servicios). Si su archivo se llama distinto, se cambia solo esta línea.
from primera_parte import (AlquilerEquipo, AsesoriaEspecializada, Cliente,
                           Entidad, ErrorReserva, ErrorSistema,
                           ErrorValidacion, ReservaSala, Servicio)


# ---------- Reserva ----------

class Reserva(Entidad):
    """Une un cliente y un servicio, y controla el estado de la reserva."""

    ESTADOS = {"Pendiente", "Confirmada", "Cancelada", "Procesada"}  # Estados permitidos

    def __init__(self, id_entidad, cliente, servicio, opciones_costo=None, descuento=0, impuesto=0):
        super().__init__(id_entidad)  # La clase base Entidad guarda el identificador

        # Validación: el cliente debe ser un objeto Cliente
        if not isinstance(cliente, Cliente):
            raise ErrorValidacion("Se debe indicar un cliente válido.")

        # Validación: el servicio debe ser un objeto Servicio
        if not isinstance(servicio, Servicio):
            raise ErrorValidacion("Se debe indicar un servicio válido.")

        # Validación: las opciones de costo deben venir en un diccionario (o no venir)
        if not isinstance(opciones_costo, (dict, type(None))):
            raise ErrorValidacion("Las opciones de costo deben estar en un diccionario.")

        # Validación: descuento e impuesto deben ser números (no texto ni booleanos)
        for nombre, valor in (("descuento", descuento), ("impuesto", impuesto)):
            if isinstance(valor, bool) or not isinstance(valor, (int, float)):
                raise ErrorValidacion(f"El {nombre} debe ser un número.")

        self._cliente = cliente  # Atributo protegido: cliente de la reserva
        self._servicio = servicio  # Atributo protegido: servicio reservado
        self._opciones_costo = dict(opciones_costo or {})  # Copia del diccionario (o vacío)
        self._descuento = descuento  # Porcentaje de descuento
        self._impuesto = impuesto  # Porcentaje de impuesto
        self._estado = "Pendiente"  # Toda reserva nueva empieza pendiente

    def _cambiar_estado(self, nuevo_estado):
        """Cambia el estado verificando que sea uno de los permitidos."""
        if nuevo_estado not in self.ESTADOS:  # Evita estados inventados
            raise ErrorReserva(f"Estado no permitido: {nuevo_estado}")
        self._estado = nuevo_estado

    @property
    def estado(self):
        """Estado actual (solo lectura desde fuera de la clase)."""
        return self._estado

    def confirmar(self):
        """Pasa la reserva de Pendiente a Confirmada."""
        if self._estado != "Pendiente":  # Solo se confirman reservas pendientes
            raise ErrorReserva("Solo se pueden confirmar reservas pendientes.")

        self._servicio.validar_disponibilidad()  # Lanza error si el servicio no está disponible
        self._cambiar_estado("Confirmada")  # Cambia el estado
        logging.info("Reserva %s confirmada.", self.id_entidad)  # Deja constancia en el log

    def cancelar(self):
        """Cancela la reserva si todavía se puede."""
        if self._estado in {"Cancelada", "Procesada"}:  # No se cancela algo ya cerrado
            raise ErrorReserva(f"No se puede cancelar una reserva {self._estado.lower()}.")

        self._cambiar_estado("Cancelada")
        logging.info("Reserva %s cancelada.", self.id_entidad)

    def procesar(self):
        """Calcula el total y deja la reserva Procesada. Usa try/except/else/finally."""
        if self._estado != "Confirmada":  # Primero debe estar confirmada
            raise ErrorReserva("La reserva debe estar confirmada antes de procesarse.")

        try:
            # Polimorfismo: cada servicio calcula el costo a su manera
            total = self._servicio.calcular_total(
                descuento=self._descuento,
                impuesto=self._impuesto,
                **self._opciones_costo  # Desempaqueta horas, días, cantidad, etc.
            )
        except ErrorSistema as error:
            # Error propio del sistema (dato inválido, servicio no disponible, etc.):
            # se convierte en ErrorReserva y se encadena con 'from' para conservar la causa
            # (la función intentar() lo registra, así no queda duplicado en el log)
            raise ErrorReserva(f"No se pudo procesar la reserva {self.id_entidad}.") from error
        except (TypeError, ValueError) as error:
            # Error de Python (por ejemplo, faltan opciones de costo): se convierte
            # en un error propio y se encadena con 'from' para no perder la causa original
            logging.error("Opciones de costo incorrectas en la reserva %s.", self.id_entidad)
            raise ErrorReserva("Las opciones de costo no son válidas para este servicio.") from error
        else:
            # Se ejecuta solo si NO hubo error: se marca como procesada
            self._cambiar_estado("Procesada")
            logging.info("Reserva %s procesada. Total: %.2f", self.id_entidad, total)
            return total
        finally:
            # Se ejecuta siempre, haya o no error
            logging.info("Fin del procesamiento de la reserva %s.", self.id_entidad)

    def descripcion(self):
        """Texto que resume la reserva (implementa el método abstracto de Entidad)."""
        return (f"Reserva {self.id_entidad}: cliente={self._cliente.nombre}, "
                f"servicio={self._servicio.nombre}, estado={self._estado}")


# ---------- Sistema de gestión ----------

class Sistema:
    """Guarda en listas los clientes, servicios y reservas (sin base de datos)."""

    def __init__(self):
        self.clientes = []  # Lista interna de clientes
        self.servicios = []  # Lista interna de servicios
        self.reservas = []  # Lista interna de reservas

    def registrar_cliente(self, cliente):
        if not isinstance(cliente, Cliente):  # Debe ser un Cliente
            raise ErrorValidacion("El objeto no es un cliente.")
        if any(c.id_entidad == cliente.id_entidad for c in self.clientes):  # Sin repetidos
            raise ErrorValidacion("Ya existe un cliente con ese identificador.")
        self.clientes.append(cliente)  # Se guarda en la lista
        logging.info("Cliente registrado: %s", cliente.descripcion())

    def registrar_servicio(self, servicio):
        if not isinstance(servicio, Servicio):
            raise ErrorValidacion("El objeto no es un servicio.")
        if any(s.id_entidad == servicio.id_entidad for s in self.servicios):
            raise ErrorValidacion("Ya existe un servicio con ese identificador.")
        self.servicios.append(servicio)
        logging.info("Servicio registrado: %s", servicio.descripcion())

    def registrar_reserva(self, reserva):
        if not isinstance(reserva, Reserva):
            raise ErrorValidacion("El objeto no es una reserva.")
        if any(r.id_entidad == reserva.id_entidad for r in self.reservas):
            raise ErrorValidacion("Ya existe una reserva con ese identificador.")
        self.reservas.append(reserva)
        logging.info("Reserva registrada: %s", reserva.descripcion())

    def buscar_cliente(self, id_cliente):
        for cliente in self.clientes:  # Recorre la lista buscando el identificador
            if cliente.id_entidad == str(id_cliente):
                return cliente
        raise ErrorValidacion(f"No se encontró el cliente {id_cliente}.")

    def buscar_servicio(self, id_servicio):
        for servicio in self.servicios:
            if servicio.id_entidad == str(id_servicio):
                return servicio
        raise ErrorValidacion(f"No se encontró el servicio {id_servicio}.")

    def buscar_reserva(self, id_reserva):
        for reserva in self.reservas:
            if reserva.id_entidad == str(id_reserva):
                return reserva
        raise ErrorValidacion(f"No se encontró la reserva {id_reserva}.")


# ---------- Ejecución controlada de operaciones ----------

def intentar(etiqueta, operacion):
    """Ejecuta una operación; si falla, registra el error y el programa sigue."""
    try:
        resultado = operacion()  # Se ejecuta la función recibida
        if resultado is not None:
            print(f"{etiqueta}: {resultado}")
        else:
            print(f"{etiqueta}: operación completada.")
        return resultado
    except ErrorSistema as error:  # Errores propios del sistema
        logging.error("Falló la operación '%s': %s", etiqueta, error)  # Un solo registro por error
        print(f"{etiqueta}: error controlado — {error}")
        if error.__cause__:  # Si hubo encadenamiento, se muestra la causa original
            print(f"    (causa original: {type(error.__cause__).__name__}: {error.__cause__})")
        return None
    except Exception as error:  # Red de seguridad para cualquier error inesperado
        logging.exception("Error inesperado en '%s'", etiqueta)  # Con traceback completo
        print(f"{etiqueta}: error inesperado — {error}")
        return None


# ---------- Demostración ----------

def demostracion():
    # El archivo de logs ya lo configura primera_parte.py (sistema_software_fj.log)
    sistema = Sistema()

    print("=== OPERACIONES VÁLIDAS ===")
    cliente1 = Cliente("C001", "Ana Pérez", "ana@email.com")
    cliente2 = Cliente("C002", "Luis Gómez", "luis@email.com")
    intentar("Registrar cliente Ana", lambda: sistema.registrar_cliente(cliente1))
    intentar("Registrar cliente Luis", lambda: sistema.registrar_cliente(cliente2))

    sala = ReservaSala("S001", "Sala principal", 50000, capacidad=20)
    equipo = AlquilerEquipo("S002", "Proyector", 25000, unidades_disponibles=5)
    asesoria = AsesoriaEspecializada("S003", "Asesoría tecnológica", 80000, "tecnología")
    intentar("Registrar sala", lambda: sistema.registrar_servicio(sala))
    intentar("Registrar equipo", lambda: sistema.registrar_servicio(equipo))
    intentar("Registrar asesoría", lambda: sistema.registrar_servicio(asesoria))

    reserva_sala = Reserva("R001", cliente1, sala, {"horas": 2}, descuento=10, impuesto=19)
    reserva_equipo = Reserva("R002", cliente2, equipo, {"dias": 3, "cantidad": 2})
    reserva_asesoria = Reserva("R003", cliente1, asesoria, {"horas": 1.5, "nivel_complejidad": 1.2})
    for reserva in (reserva_sala, reserva_equipo, reserva_asesoria):
        intentar(f"Registrar reserva {reserva.id_entidad}",
                 lambda r=reserva: sistema.registrar_reserva(r))

    for reserva in sistema.reservas:
        intentar(f"Confirmar reserva {reserva.id_entidad}", reserva.confirmar)
        total = intentar(f"Procesar reserva {reserva.id_entidad}", reserva.procesar)
        if total is not None:
            print(f"  Total: ${total:,.2f}")

    print("\n=== OPERACIONES INVÁLIDAS (el programa debe seguir funcionando) ===")
    intentar("Cliente con correo inválido", lambda: Cliente("C003", "Marta", "correo-invalido"))
    intentar("Cliente duplicado", lambda: sistema.registrar_cliente(cliente1))
    intentar("Servicio con tarifa negativa", lambda: ReservaSala("S004", "Sala rota", -5000, capacidad=10))
    intentar("Reserva sin cliente", lambda: Reserva("R004", None, sala))
    intentar("Confirmar una reserva ya procesada", reserva_sala.confirmar)
    intentar("Cancelar una reserva ya procesada", reserva_sala.cancelar)
    intentar("Reserva con descuento en texto", lambda: Reserva("R008", cliente1, sala, {"horas": 1}, descuento="diez"))
    intentar("Buscar reserva inexistente", lambda: sistema.buscar_reserva("R999"))

    # Reserva de más unidades de las que hay (el error aparece al procesar)
    r5 = Reserva("R005", cliente2, equipo, {"dias": 1, "cantidad": 10})
    intentar("Registrar reserva R005", lambda: sistema.registrar_reserva(r5))
    intentar("Confirmar reserva R005", r5.confirmar)
    intentar("Procesar R005 (10 unidades, solo hay 5)", r5.procesar)

    # Horas negativas: el error aparece al calcular el costo y se encadena
    r6 = Reserva("R006", cliente1, sala, {"horas": -3})
    intentar("Registrar reserva R006", lambda: sistema.registrar_reserva(r6))
    intentar("Confirmar reserva R006", r6.confirmar)
    intentar("Procesar R006 (horas negativas)", r6.procesar)

    # Opciones con una clave repetida: provoca un TypeError de Python que también se encadena
    r9 = Reserva("R009", cliente1, sala, {"horas": 1, "descuento": 5})
    intentar("Registrar reserva R009", lambda: sistema.registrar_reserva(r9))
    intentar("Confirmar reserva R009", r9.confirmar)
    intentar("Procesar R009 (opciones mal formadas)", r9.procesar)

    # Servicio no disponible
    equipo.cambiar_disponibilidad(False)  # Método de la clase Servicio
    r7 = Reserva("R007", cliente2, equipo, {"dias": 1})
    intentar("Registrar reserva R007", lambda: sistema.registrar_reserva(r7))
    intentar("Confirmar R007 (servicio no disponible)", r7.confirmar)

    print("\nReservas registradas:")
    for reserva in sistema.reservas:
        print(f"- {reserva.descripcion()}")
    print("\nEl programa terminó sin interrupciones. Revisar el archivo sistema_software_fj.log")


if __name__ == "__main__":
    demostracion()
