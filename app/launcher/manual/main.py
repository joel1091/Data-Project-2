# launcher/manual/main.py
from ayudantes_generator import run_manual_generator as run_manual_ayudantes
from necesitados_generator import run_manual_generator as run_manual_necesitados

def main():
    print("Ejecutando generadores en modo MANUAL para demo.")
    print("Seleccione una opción:")
    print("  a) Ejecutar generador de AYUDANTES")
    print("  n) Ejecutar generador de NECESITADOS")
    print("  b) Ejecutar ambos generadores")
    
    opcion = input("Opción (a/n/b): ").strip().lower()
    
    if opcion == "a":
        run_manual_ayudantes()
    elif opcion == "n":
        run_manual_necesitados()
    elif opcion == "b":
        # En modo manual para ambos, se ejecuta uno en hilo y luego el otro
        import threading
        thread_ayudantes = threading.Thread(target=run_manual_ayudantes, daemon=True)
        thread_ayudantes.start()
        run_manual_necesitados()
    else:
        print("Opción no reconocida. Saliendo.")

if __name__ == "__main__":
    main()
