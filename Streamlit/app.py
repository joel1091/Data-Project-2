import streamlit as st
import ofrecer_ayuda
import pedir_ayuda

def aplicar_estilos():
    st.markdown(
        """
        <style>
        /* Estilos generales */
        .main {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: white;
            font-family: 'Inter', sans-serif;
        }
        
        /* Título principal */
        .main-title {
            color: white;
            text-align: center;
            font-size: 3.5rem;
            font-weight: 800;
            padding: 1rem 0;
            margin-bottom: 1.5rem !important;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            background: linear-gradient(90deg, #4facfe 0%, #00f2fe 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        /* Sección de información */
        .info-section {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            padding: 2rem;
            margin-top: 1rem !important;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .info-title {
            color: white;
            font-size: 1.5rem;
            margin-bottom: 1rem;
            font-weight: 600;
        }

        .info-text {
            color: #a0aec0;
            line-height: 1.6;
        }

        /* Botones más visibles */
        .stButton > button {
            width: 100%;
            height: 150px;
            border-radius: 40px;
            border: 3px solid rgba(255, 255, 255, 0.3);
            font-size: 26px;
            font-weight: 800;
            letter-spacing: 0.5px;
            transition: all 0.3s ease-in-out;
            margin: 15px 0;
            position: relative;
            overflow: hidden;
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 8px 25px rgba(0,0,0,0.3);
            text-transform: uppercase;
        }

        /* Efecto de iluminación */
        .stButton > button::before {
            content: '';
            position: absolute;
            top: -100%;
            left: -100%;
            width: 300%;
            height: 300%;
            background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 10%, transparent 80%);
            transition: transform 0.5s ease;
            transform: translateX(-50%) translateY(-50%);
        }

        .stButton > button:hover::before {
            transform: translateX(0) translateY(0);
        }

        /* Efecto de profundidad al hacer clic */
        .stButton > button:active {
            transform: scale(0.96);
            box-shadow: 0 5px 20px rgba(0, 0, 0, 0.4);
        }

        /* Botón Ofrecer Ayuda */
        .stButton > button:first-child {
            background: linear-gradient(135deg, #00c6ff, #0072ff);
            border-color: #0072ff;
        }
        
        .stButton > button:first-child:hover {
            background: linear-gradient(135deg, #0072ff, #00c6ff);
            box-shadow: 0 10px 30px rgba(0, 114, 255, 0.5);
        }

        /* Botón Pedir Ayuda */
        .stButton > button:last-child {
            background: linear-gradient(135deg, #ff512f, #dd2476);
            border-color: #dd2476;
        }

        .stButton > button:last-child:hover {
            background: linear-gradient(135deg, #dd2476, #ff512f);
            box-shadow: 0 10px 30px rgba(221, 36, 118, 0.5);
        }

        /* Responsive */
        @media (max-width: 768px) {
            .main-title {
                font-size: 2.5rem;
            }
            .stButton > button {
                height: 120px;
                font-size: 22px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True
    )

aplicar_estilos()

# Inicializar el estado de la sesión
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'inicio'

if st.session_state.pagina == 'inicio':
    # Título principal
    st.markdown('<h1 class="main-title">PLATAFORMA DE AYUDA MUTUA</h1>', unsafe_allow_html=True)
    
    # Contenedor de información
    st.markdown("""
        <div class="info-section">
            <div class="info-title">Conectando personas, construyendo comunidad</div>
            <p class="info-text">Una plataforma que une a quienes necesitan ayuda con quienes pueden ofrecerla.</p>
        </div>
    """, unsafe_allow_html=True)

    # Espacio extra antes de los botones
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🤝 OFRECER AYUDA", key="ofrecer", help="Únete como voluntario", use_container_width=True):
            st.session_state.pagina = "ayudar"

    with col2:
        if st.button("💝 PEDIR AYUDA", key="pedir", help="Solicita asistencia", use_container_width=True):
            st.session_state.pagina = "pedir"

    # Sección de información mejorada
    st.markdown("""
        <div class="info-section">
            <div class="info-title">¿Cómo funciona?</div>
            <p class="info-text">
                1. Elige tu rol: voluntario o solicitante<br>
                2. Completa un breve formulario con tus datos<br>
                3. Conectamos contigo instantáneamente con las personas adecuadas<br>
                4. Comienza a hacer la diferencia en tu comunidad
            </p>
        </div>
    """, unsafe_allow_html=True)

elif st.session_state.pagina == 'ayudar':
    ofrecer_ayuda.mostrar()

elif st.session_state.pagina == 'pedir':
    pedir_ayuda.mostrar()
