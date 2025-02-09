import streamlit as st

# Función para aplicar estilos CSS personalizados
def aplicar_estilos():
    st.markdown(
        """
        <style>
        .boton-panel {
            display: inline-block;
            width: 45%;
            height: 200px;
            margin: 2%;
            color: white;
            font-size: 24px;
            font-weight: bold;
            text-align: center;
            line-height: 200px;
            border-radius: 10px;
            cursor: pointer;
            text-decoration: none;
        }
        .boton-ayudar {
            background-color: rgba(0, 128, 0, 0.7); /* Verde transparente */
        }
        .boton-pedir {
            background-color: rgba(255, 0, 0, 0.7); /* Rojo transparente */
        }
        .boton-panel:hover {
            opacity: 0.9;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


aplicar_estilos()

# Inicializar el estado de la sesión para la navegación
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'inicio'

# Funciones para manejar la navegación
def mostrar_inicio():
    st.title("Bienvenido a la Plataforma de Ayuda")
    st.markdown(
        """
        <a href="#" class="boton-panel boton-ayudar" onclick="window.location.href = '?pagina=ayudar';">OFRECER AYUDA</a>
        <a href="#" class="boton-panel boton-pedir" onclick="window.location.href = '?pagina=pedir';">PEDIR AYUDA</a>
        """,
        unsafe_allow_html=True
    )

def mostrar_ayudar():
    st.title("Formulario para Ofrecer Ayuda")
    st.write("Gracias por ofrecer tu ayuda. Por favor, completa la siguiente información.")
    if st.button("Volver al inicio"):
        st.session_state.pagina = 'inicio'

def mostrar_pedir():
    st.title("Formulario para Pedir Ayuda")
    st.write("Estamos aquí para ayudarte. Por favor, completa la siguiente información.")
    if st.button("Volver al inicio"):
        st.session_state.pagina = 'inicio'

# Lógica de navegación
if st.session_state.pagina == 'inicio':
    mostrar_inicio()
elif st.session_state.pagina == 'ayudar':
    mostrar_ayudar()
elif st.session_state.pagina == 'pedir':
    mostrar_pedir()

# Manejar la navegación basada en la URL
query_params = st.experimental_get_query_params()
if 'pagina' in query_params:
    st.session_state.pagina = query_params['pagina'][0]
