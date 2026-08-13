# -*- coding: utf-8 -*-
import time
import motor
import config

def auditar_dfs_txt(n: int, limite_nodos: int = 150000):
    print(f"[INICIO] Iniciando Auditoria DFS para tablero {n}x{n}...")
    
    if not motor.validar_n(n):
        print(f"[ERROR] Tamano {n} no valido.")
        return

    estado_raiz = motor.estado_inicial(n)
    pila = [(estado_raiz, [])]
    visitados = set()
    
    nodos_evaluados = 0
    partidas_terminadas = 0
    
    # Creamos el archivo txt donde guardaremos las jugadas
    nombre_archivo = f"trazas_dodgem_{n}x{n}.txt"
    
    with open(nombre_archivo, "w", encoding="utf-8") as archivo:
        archivo.write(f"=== AUDITORIA DFS - DODGEM {n}x{n} ===\n\n")
        archivo.write("Nota: Se muestran las partidas que llegaron a un estado terminal.\n\n")
        
        while pila and nodos_evaluados < limite_nodos:
            estado_actual, traza = pila.pop()
            
            if estado_actual in visitados:
                continue
                
            visitados.add(estado_actual)
            nodos_evaluados += 1

            if nodos_evaluados % 10000 == 0:
                print(f"[PROGRESO] Evaluados: {nodos_evaluados} estados...")

            # Si llegamos al final de una partida, la escribimos en el TXT
            if motor.es_terminal(estado_actual):
                partidas_terminadas += 1
                ganador = motor.ganador(estado_actual)
                motivo = motor.motivo_de_termino(estado_actual)
                
                archivo.write(f"--- Partida Terminal #{partidas_terminadas} ---\n")
                archivo.write(f"Ganador: {config.NOMBRES_JUGADORES.get(ganador, ganador)}\n")
                archivo.write(f"Motivo: {motivo}\n")
                
                # Imprimir el paso a paso
                for i, paso in enumerate(traza):
                    archivo.write(f"  {i+1}. {paso}\n")
                archivo.write("\n")
                continue

            # Generar nuevos movimientos
            try:
                legales = motor.movimientos_legales(estado_actual)
                jugador = estado_actual.turno
                
                for mov in legales:
                    nuevo_estado = motor.aplicar(estado_actual, mov)
                    descripcion = motor.describir_movimiento(mov, jugador)
                    nueva_traza = traza + [descripcion]
                    
                    if nuevo_estado not in visitados:
                        pila.append((nuevo_estado, nueva_traza))
                        
            except Exception as e:
                archivo.write(f"\n[!] ERROR FATAL EN EL MOTOR:\n{e}\nTraza hasta el error:\n")
                for i, paso in enumerate(traza):
                    archivo.write(f"  {i+1}. {paso}\n")
                print(f"[ALERTA] El motor fallo. Revisa el archivo {nombre_archivo}")
                return

        archivo.write(f"\n=== RESUMEN ===\nNodos evaluados: {nodos_evaluados}\nPartidas terminadas: {partidas_terminadas}\n")
        
    print(f"\n[EXITO] Auditoria finalizada.")
    print(f"[ARCHIVO CREADO] Revisa el archivo: {nombre_archivo} en tu carpeta.")

if __name__ == "__main__":
    auditar_dfs_txt(n=4, limite_nodos=150000)