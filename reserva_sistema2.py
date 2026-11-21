"""Segunda mitad del proyecto: clase Reserva, clase Sistema y demostración de operaciones.
Cada bloque está comentado para explicar qué hace y por qué."""
import logging  # Módulo estándar para escribir el archivo de logs

# Clases y excepciones que están en Fase4.py (primera mitad del proyecto)
from Fase4 import (Asesoria, Cliente, DatoInvalidoError, Entidad, ErrorSistema,
                   ReservaEquipo, ReservaError, ReservaSala, Servicio)


# ---------- Reserva ----------

class Reserva(Entidad):
    """Une un cliente y un servicio, y controla el estado de la reserva."""

    ESTADOS = ("Pendiente", "Confirmada", "Cancelada", "Completada")  # Estados permitidos

    def __init__(self, identificador, cliente, servicio, duracion, descuento=0, impuesto=0):
        super().__init__(identificador)  # La clase base Entidad valida y guarda el identificador

        # Validación: el cliente debe ser un objeto Cliente
        if not isinstance(cliente, Cliente):
            raise DatoInvalidoError("Se debe indicar un cliente válido.")

        # Validación: el servicio debe ser un objeto Servicio
        if not isinstance(servicio, Servicio):
            raise DatoInvalidoError("Se debe indicar un servicio válido.")

        # Validación: la duración (en horas) debe ser un número mayor a cero
        if isinstance(duracion, bool) or not isinstance(duracion, (int, float)) or duracion <= 0:
            raise DatoInvalidoError("La duración debe ser un número mayor a cero.")

        # Validación: descuento e impuesto deben ser números (no texto ni booleanos)
        for nombre, valor in (("descuento", descuento), ("impuesto", impuesto)):
            if isinstance(valor, bool) or not isinstance(valor, (int, float)):
                raise DatoInvalidoError(f"El {nombre} debe ser un número.")

        self._cliente = cliente  # Atributo protegido: cliente de la reserva
        self._servicio = servicio  # Atributo protegido: servicio reservado
        self._duracion = duracion  # Duración en horas
        self._descuento = descuento  # Porcentaje de descuento
        self._impuesto = impuesto  # Porcentaje de impuesto
        self._estado = "Pendiente"  # Toda reserva nueva empieza pendiente
        self._total = None  # Se calcula al completar la reserva

    def _cambiar_estado(self, nuevo_estado):
        """Cambia el estado verificando que sea uno de los permitidos."""
        if nuevo_estado not in self.ESTADOS:  # Evita estados inventados
            raise ReservaError(f"Estado no permitido: {nuevo_estado}")
        self._estado = nuevo_estado

    @property
    def estado(self):
        """Estado actual (solo lectura desde fuera de la clase)."""
        return self._estado

    @property
    def total(self):
        """Costo final (None mientras la reserva no esté completada)."""
        return self._total

    def confirmar(self):
        """Pasa la reserva de Pendiente a Confirmada."""
        if self._estado != "Pendiente":  # Solo se confirman reservas pendientes
            raise ReservaError("Solo se pueden confirmar reservas pendientes.")

        self._servicio.validar_disponibilidad()  # Lanza error si el servicio no está disponible
        self._cambiar_estado("Confirmada")  # Cambia el estado
        logging.info("Reserva %s confirmada.", self.identificador)  # Deja constancia en el log

    def cancelar(self):
        """Cancela la reserva si todavía se puede."""
        if self._estado in ("Cancelada", "Completada"):  # No se cancela algo ya cerrado
            raise ReservaError(f"No se puede cancelar una reserva {self._estado.lower()}.")

        self._cambiar_estado("Cancelada")
        logging.info("Reserva %s cancelada.", self.identificador)

    def completar(self):
        """Calcula el costo final y deja la reserva Completada. Usa try/except/else/finally."""
        if self._estado != "Confirmada":  # Primero debe estar confirmada
            raise ReservaError("La reserva debe estar confirmada antes de completarse.")

        try:
            self._servicio.validar_disponibilidad()  # El servicio pudo deshabilitarse después
            # Polimorfismo: cada servicio calcula el costo a su manera
            total = self._servicio.costo_con_descuento(
                self._duracion, self._descuento, self._impuesto)
        except ErrorSistema as error:
            # Error propio del sistema (dato inválido, servicio no disponible, etc.):
            # se convierte en ReservaError y se encadena con 'from' para conservar la causa
            # (la función intentar() lo registra, así no queda duplicado en el log)
            raise ReservaError(f"No se pudo completar la reserva {self.identificador}.") from error
        except (TypeError, ValueError) as error:
            # Error de Python (por ejemplo, un tipo de dato inesperado): se convierte
            # en un error propio y se encadena con 'from' para no perder la causa original
            logging.error("Datos incorrectos en la reserva %s.", self.identificador)
            raise ReservaError("Los datos de costo no son válidos para esta reserva.") from error
        else:
            # Se ejecuta solo si NO hubo error: se guarda el total y se completa
            self._total = total
            self._cambiar_estado("Completada")
            logging.info("Reserva %s completada. Total: %.2f", self.identificador, total)
            return total
        finally:
            # Se ejecuta siempre, haya o no error
            logging.info("Fin del procesamiento de la reserva %s.", self.identificador)

    def descripcion(self):
        """Texto que resume la reserva (implementa el método abstracto de Entidad)."""
        return (f"Reserva {self.identificador}: cliente={self._cliente.nombre}, "
                f"servicio={self._servicio.nombre}, {self._duracion} h, estado={self._estado}")


# ---------- Sistema de gestión ----------

class Sistema:
    """Guarda en listas los clientes, servicios y reservas (sin base de datos)."""

    def __init__(self):
        self.clientes = []  # Lista interna de clientes
        self.servicios = []  # Lista interna de servicios
        self.reservas = []  # Lista interna de reservas

    def registrar_cliente(self, cliente):
        if not isinstance(cliente, Cliente):  # Debe ser un Cliente
            raise DatoInvalidoError("El objeto no es un cliente.")
        if any(c.identificador == cliente.identificador for c in self.clientes):  # Sin repetidos
            raise DatoInvalidoError("Ya existe un cliente con ese identificador.")
        self.clientes.append(cliente)  # Se guarda en la lista
        logging.info("Cliente registrado: %s", cliente.descripcion())

    def registrar_servicio(self, servicio):
        if not isinstance(servicio, Servicio):
            raise DatoInvalidoError("El objeto no es un servicio.")
        if any(s.identificador == servicio.identificador for s in self.servicios):
            raise DatoInvalidoError("Ya existe un servicio con ese identificador.")
        self.servicios.append(servicio)
        logging.info("Servicio registrado: %s", servicio.descripcion())

    def registrar_reserva(self, reserva):
        if not isinstance(reserva, Reserva):
            raise DatoInvalidoError("El objeto no es una reserva.")
        if any(r.identificador == reserva.identificador for r in self.reservas):
            raise DatoInvalidoError("Ya existe una reserva con ese identificador.")
        self.reservas.append(reserva)
        logging.info("Reserva registrada: %s", reserva.descripcion())

    def buscar_cliente(self, id_cliente):
        for cliente in self.clientes:  # Recorre la lista buscando el identificador
            if cliente.identificador == str(id_cliente):
                return cliente
        raise DatoInvalidoError(f"No se encontró el cliente {id_cliente}.")

    def buscar_servicio(self, id_servicio):
        for servicio in self.servicios:
            if servicio.identificador == str(id_servicio):
                return servicio
        raise DatoInvalidoError(f"No se encontró el servicio {id_servicio}.")

    def buscar_reserva(self, id_reserva):
        for reserva in self.reservas:
            if reserva.identificador == str(id_reserva):
                return reserva
        raise DatoInvalidoError(f"No se encontró la reserva {id_reserva}.")


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
    # El archivo de logs ya lo configura Fase4.py (sistema_software_fj.log)
    sistema = Sistema()

    print("=== OPERACIONES VÁLIDAS ===")
    cliente1 = Cliente("C001", "Ana Pérez", "ana@email.com", "3101234567")
    cliente2 = Cliente("C002", "Luis Gómez", "luis@email.com", "3209876543")
    intentar("Registrar cliente Ana", lambda: sistema.registrar_cliente(cliente1))
    intentar("Registrar cliente Luis", lambda: sistema.registrar_cliente(cliente2))

    sala = ReservaSala("S001", "Sala principal", 50000, capacidad=20)
    equipo = ReservaEquipo("S002", "Proyector", 25000, "Video proyector")
    asesoria = Asesoria("S003", "Asesoría tecnológica", 80000, "Ingeniero de sistemas")
    intentar("Registrar sala", lambda: sistema.registrar_servicio(sala))
    intentar("Registrar equipo", lambda: sistema.registrar_servicio(equipo))
    intentar("Registrar asesoría", lambda: sistema.registrar_servicio(asesoria))

    reserva_sala = Reserva("R001", cliente1, sala, 2, descuento=10, impuesto=19)
    reserva_equipo = Reserva("R002", cliente2, equipo, 3)
    reserva_asesoria = Reserva("R003", cliente1, asesoria, 1.5, impuesto=19)
    for reserva in (reserva_sala, reserva_equipo, reserva_asesoria):
        intentar(f"Registrar reserva {reserva.identificador}",
                 lambda r=reserva: sistema.registrar_reserva(r))

    for reserva in sistema.reservas:
        intentar(f"Confirmar reserva {reserva.identificador}", reserva.confirmar)
        total = intentar(f"Completar reserva {reserva.identificador}", reserva.completar)
        if total is not None:
            print(f"  Total: ${total:,.2f}")

    print("\n=== OPERACIONES INVÁLIDAS (el programa debe seguir funcionando) ===")
    intentar("Cliente con correo inválido",
             lambda: Cliente("C003", "Marta Díaz", "correo-invalido", "3001112233"))
    intentar("Cliente con teléfono inválido",
             lambda: Cliente("C004", "Pedro Ruiz", "pedro@email.com", "12345"))
    intentar("Cliente duplicado", lambda: sistema.registrar_cliente(cliente1))
    intentar("Servicio con precio negativo",
             lambda: ReservaSala("S004", "Sala rota", -5000, capacidad=10))
    intentar("Reserva sin cliente", lambda: Reserva("R004", None, sala, 2))
    intentar("Reserva con duración 0", lambda: Reserva("R005", cliente1, sala, 0))
    intentar("Confirmar una reserva ya completada", reserva_sala.confirmar)
    intentar("Cancelar una reserva ya completada", reserva_sala.cancelar)
    intentar("Buscar reserva inexistente", lambda: sistema.buscar_reserva("R999"))

    # Descuento imposible: el error aparece al completar y se encadena
    r6 = Reserva("R006", cliente2, sala, 1, descuento=150)
    intentar("Registrar reserva R006", lambda: sistema.registrar_reserva(r6))
    intentar("Confirmar reserva R006", r6.confirmar)
    intentar("Completar R006 (descuento del 150 %)", r6.completar)

    # El servicio se deshabilita después de confirmar: también se encadena
    r7 = Reserva("R007", cliente1, asesoria, 2)
    intentar("Registrar reserva R007", lambda: sistema.registrar_reserva(r7))
    intentar("Confirmar reserva R007", r7.confirmar)
    asesoria.cambiar_disponibilidad(False)  # La asesoría deja de estar disponible
    intentar("Completar R007 (servicio ya no disponible)", r7.completar)

    # Intentar reservar un servicio no disponible
    r8 = Reserva("R008", cliente2, asesoria, 1)
    intentar("Registrar reserva R008", lambda: sistema.registrar_reserva(r8))
    intentar("Confirmar R008 (servicio no disponible)", r8.confirmar)
    intentar("Cancelar reserva R008", r8.cancelar)
    intentar("Cancelar R008 por segunda vez", r8.cancelar)

    print("\nReservas registradas:")
    for reserva in sistema.reservas:
        print(f"- {reserva.descripcion()}")
    print("\nEl programa terminó sin interrupciones. Revisar el archivo sistema_software_fj.log")


if __name__ == "__main__":
    demostracion()
