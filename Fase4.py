#Universidad Nacional Abierta y a Distancia# 
# Escuela de Ciencias Básicas Tecnología e Ingeniería ECBTI#
#Programacion#
#Ejercicio 1: Sistema Integral de Gestión de Clientes, Servicios y Reservas#
#Integrantes: Maria Alejandra Avila,Henry Gonzalez Lopez#



from abc import ABC, abstractmethod
from datetime import datetime
import logging
import re

#Registro de eventos y errores#
logging.basicConfig(filename="sistema_software_fj.log", level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')

#Excepciones perosnalizadas#

class ErrorSistema(Exception):
    """Error base del sistema."""
class DatoInvalidoError(ErrorSistema):
    pass
    
class ServicioNoDisponibleError(ErrorSistema):
    pass
class ReservaError(ErrorSistema):
    pass

#Clase abstracta general#

class Entidad(ABC):
    def __init__(self, identificador):
        if not identificador or not str(identificador).strip():
            raise DatoInvalidoError("El identificador es obligatorio.")
        self._identificador = str(identificador).strip()

    # CORRECCIÓN: estos métodos estaban dentro de __init__; ahora son de la clase
    @property
    def identificador(self):
        return self._identificador

    @abstractmethod
    def descripcion(self):
        pass
        
#Cliente#
class Cliente(Entidad):
    def __init__(self, identificador, nombre, correo,telefono):
        super().__init__(identificador)
        
        nombre=str(nombre).strip()
        correo=str(correo).strip()
        telefono=str(telefono).strip()
        
        if len(nombre) < 3:
            raise DatoInvalidoError("El nombre del cliente debe tener al menos 3 caracteres.")
        if not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", correo): 
            raise DatoInvalidoError(f"El correo invalido: {correo}") 
        if not re.fullmatch(r"\d{10}", telefono):
            raise DatoInvalidoError(f"Teléfono inválido: {telefono}") 
        if not telefono.isdigit() or len(telefono) != 10:
            raise DatoInvalidoError("El teléfono debe contener exactamente 10 dígitos.")
        
        self._nombre = nombre
        self._correo = correo
        self._telefono = telefono

    # CORRECCIÓN: propiedades y descripcion estaban dentro de __init__
    @property
    def nombre(self):
        return self._nombre

    @property
    def correo(self):
        return self._correo

    @property
    def telefono(self):
        return self._telefono

    def descripcion(self):
        return f"Cliente: {self._nombre}, Correo: {self._correo}, Teléfono: {self._telefono}"
        
#Servicios#

class Servicio(Entidad,ABC):
    def __init__(self, identificador, nombre, precio):
        super().__init__(identificador)        
        nombre=str(nombre).strip()
        
        if not nombre:
            raise DatoInvalidoError("El nombre del servicio es obligatorio.")
        if not isinstance(precio, (int, float)) or precio <= 0:
            raise DatoInvalidoError("El precio del servicio debe ser un número mayor a cero.")
        
        
        self._nombre = nombre
        self._precio = float(precio)
        self._disponible = True  # Inicialmente, el servicio está disponible

    # CORRECCIÓN: todo lo siguiente estaba dentro de __init__; ahora son métodos de la clase
    @property
    def nombre(self):
        return self._nombre
        
    @property
    def precio(self):
        return self._precio

    @property
    def disponible(self):
        return self._disponible

    # AGREGADO: permite habilitar o deshabilitar el servicio
    def cambiar_disponibilidad(self, disponible):
        if not isinstance(disponible, bool):
            raise DatoInvalidoError("La disponibilidad debe ser True o False.")
        self._disponible = disponible
        logging.info(f"Disponibilidad del servicio {self._identificador} cambiada a {disponible}.")
        
    def validar_disponibilidad(self):
        if not self._disponible:
            raise ServicioNoDisponibleError(f"El servicio '{self._nombre}' no está disponible.")
        
    @abstractmethod
    def calcular_costo(self,duracion):  
        pass
        
    def costo_con_descuento(self, duracion, descuento=0, impuesto=0):
        costo_base = self.calcular_costo(duracion)
        if not (0 <= descuento <= 100):
            raise DatoInvalidoError("El descuento debe estar entre 0 y 100.")
        if not (0 <= impuesto <= 100):
            raise DatoInvalidoError("El impuesto debe estar entre 0 y 100.")
        # CORRECCIÓN: el impuesto se validaba pero no se sumaba al costo
        costo_final = costo_base * (1 - descuento / 100) * (1 + impuesto / 100)
        return round(costo_final, 2)
        
class ReservaSala(Servicio):
    def __init__(self, identificador, nombre, precio, capacidad):
        super().__init__(identificador, nombre, precio)
        if not isinstance(capacidad, int) or isinstance(capacidad, bool) or capacidad <= 0:
            raise DatoInvalidoError("La capacidad debe ser un número entero mayor a cero.")
        self._capacidad = capacidad
        
    @property
    def capacidad(self):
        return self._capacidad
    
    def calcular_costo(self, duracion):
        # CORRECCIÓN: "<= 0" (el mensaje dice "mayor a cero")
        if not isinstance(duracion, (int, float)) or isinstance(duracion, bool) or duracion <= 0:
            raise DatoInvalidoError("La duración debe ser un número mayor a cero.")
        return round(self._precio * duracion, 2)
    
    def descripcion(self):
        # CORRECCIÓN: el atributo se llama _precio (no _precio_base)
        return (f"Reserva de Sala: {self._nombre}, Capacidad: {self._capacidad}, Precio por hora: ${self._precio:.2f}")
    
class ReservaEquipo(Servicio):
    def __init__(self, identificador, nombre, precio, tipo_equipo):
        super().__init__(identificador, nombre, precio)
        tipo_equipo=str(tipo_equipo).strip()
        # CORRECCIÓN: la validación pedía un número entero, por eso siempre fallaba
        if not tipo_equipo:
            raise DatoInvalidoError("El tipo de equipo es obligatorio.")
        self._tipo_equipo = tipo_equipo
        
    @property
    def tipo_equipo(self):
        return self._tipo_equipo
    
    def calcular_costo(self, duracion):
        if not isinstance(duracion, (int, float)) or isinstance(duracion, bool) or duracion <= 0:
            raise DatoInvalidoError("La duración debe ser un número mayor a cero.")
        return round(self._precio * duracion, 2)
    
    def descripcion(self):
        return (f"Reserva de Equipo: {self._nombre}, Tipo de Equipo: {self._tipo_equipo}, Precio por hora: ${self._precio:.2f}")
    
class Asesoria(Servicio):
    def __init__(self, identificador, nombre, precio, especialista):
        super().__init__(identificador, nombre, precio)
        especialista=str(especialista).strip()
        if not especialista:
            raise DatoInvalidoError("El especialista es obligatorio.")
        self._especialista = especialista
        
    @property
    def especialista(self):
        return self._especialista
    
    def calcular_costo(self, duracion):
        if not isinstance(duracion, (int, float)) or isinstance(duracion, bool) or duracion <= 0:
            raise DatoInvalidoError("La duración debe ser un número mayor a cero.")
        return round(self._precio * duracion, 2)     

    
    def descripcion(self):
        return (f"Asesoría: {self._nombre}, Especialista: {self._especialista}, Precio por hora: ${self._precio:.2f}")
