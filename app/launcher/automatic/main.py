import threading
from ayudantes_generator import run_automatic_generator as run_automatic_ayudantes
from necesitados_generator import run_automatic_generator as run_automatic_necesitados

def main():
    print("Ejecutando ambos generadores en modo AUTOMÁTICO...")
    # Ejecuta el generador de ayudantes en un hilo en segundo plano.
    thread_ayudantes = threading.Thread(target=run_automatic_ayudantes, daemon=True)
    thread_ayudantes.start()
    # Ejecuta el generador de necesitados en el hilo principal.
    run_automatic_necesitados()

if __name__ == "__main__":
    main()
