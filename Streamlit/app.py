import streamlit as st
import ofrecer_ayuda
import pedir_ayuda

# la función st.button no permite cambiar el formato de los button (predeterminado)
def aplicar_estilos():
    st.markdown(
        """
        <style>
        /* Contenedor de los botones */
        .stButton > button {
            width: 100%;
            height: 100px;
            font-size: 22px;
            font-weight: bold;
            border-radius: 10px;
            border: none;
            transition: background-color 0.3s;
        }

        /* Botón de Ofrecer Ayuda */
        .stButton > button.ofrecer {
            background-color: #28a745; /* Verde */
            color: white;
        }
        .stButton > button.ofrecer:hover {
            background-color: #218838; /* Verde más oscuro */
        }

        /* Botón de Pedir Ayuda */
        .stButton > button.pedir {
            background-color: #dc3545; /* Rojo */
            color: white;
        }
        .stButton > button.pedir:hover {
            background-color: #c82333; /* Rojo más oscuro */
        }
        </style>
        """,
        unsafe_allow_html=True
    )

aplicar_estilos()


# Inicializar el estado de la sesión para la navegación
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'inicio'

def ir_a_ayudar():
    st.session_state.pagina = 'ayudar'
    st.rerun()

def ir_a_pedir():
    st.session_state.pagina = 'pedir'
    st.rerun()

if st.session_state.pagina == 'inicio':
    st.title("Bienvenido a la Plataforma de Ayuda")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🟢 OFRECER AYUDA", key="ofrecer", help="Haz doble clic para ofrecer ayuda", use_container_width=True):
            st.session_state.pagina = "ayudar"

    with col2:
        if st.button("🔴 PEDIR AYUDA", key="pedir", help="Haz doble clic para pedir ayuda", use_container_width=True):
            st.session_state.pagina = "pedir"

elif st.session_state.pagina == 'ayudar':
    ofrecer_ayuda.mostrar()  

elif st.session_state.pagina == 'pedir':
    pedir_ayuda.mostrar()


