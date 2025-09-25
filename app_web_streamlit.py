import streamlit as st
import io
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
import zipfile
import base64
import os

# Importación condicional de cairosvg
try:
    import cairosvg
    CAIRO_AVAILABLE = True
except ImportError:
    CAIRO_AVAILABLE = False

st.set_page_config(
    page_title="🎯 Generador VS - Enfrentamientos", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #1e3a8a;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1fae5;
        border: 1px solid #10b981;
        color: #065f46;
        margin: 1rem 0;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fef3c7;
        border: 1px solid #f59e0b;
        color: #92400e;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Título principal
st.markdown('<div class="main-header">🎯 Generador de Imágenes VS</div>', unsafe_allow_html=True)
st.markdown("### Crea enfrentamientos deportivos profesionales")

# Advertencia sobre SVG
if not CAIRO_AVAILABLE:
    st.markdown("""
    <div class="warning-box">
        ⚠️ <strong>SVG no disponible:</strong> Solo se pueden usar logos en formato PNG/JPG
    </div>
    """, unsafe_allow_html=True)

# Inicializar session state
if 'enfrentamientos' not in st.session_state:
    st.session_state.enfrentamientos = []

# Sidebar para configuración
with st.sidebar:
    st.header("⚙️ Configuración")
    
    # Imagen de fondo
    st.subheader("🖼️ Imagen de Fondo")
    background_file = st.file_uploader(
        "Selecciona imagen de fondo",
        type=['png', 'jpg', 'jpeg'],
        key="background"
    )
    
    # Logos
    st.subheader("🏆 Logos de Equipos")
    
    if CAIRO_AVAILABLE:
        logo_types = ['png', 'jpg', 'jpeg', 'svg']
    else:
        logo_types = ['png', 'jpg', 'jpeg']
    
    logo_a_file = st.file_uploader(
        "Logo Equipo A",
        type=logo_types,
        key="logo_a"
    )
    
    logo_b_file = st.file_uploader(
        "Logo Equipo B", 
        type=logo_types,
        key="logo_b"
    )
    
    # Nombre de equipos
    st.subheader("📝 Nombres de Equipos")
    equipo_a_name = st.text_input("Nombre Equipo A", "")
    equipo_b_name = st.text_input("Nombre Equipo B", "")
    
    # Opciones adicionales
    st.subheader("🎨 Opciones")
    add_outline = st.checkbox("Contorno blanco en logos", value=False)

# Área principal
col1, col2 = st.columns([2, 1])

with col1:
    st.header("➕ Añadir Enfrentamiento")
    
    # Validar que todos los campos estén llenos
    can_add = all([background_file, logo_a_file, logo_b_file, equipo_a_name, equipo_b_name])
    
    if st.button("🎯 Añadir Enfrentamiento a la Cola", disabled=not can_add, use_container_width=True):
        if can_add:
            enfrentamiento = {
                'background': background_file,
                'logo_a': logo_a_file,
                'logo_b': logo_b_file,
                'equipo_a': equipo_a_name,
                'equipo_b': equipo_b_name,
                'add_outline': add_outline,
                'id': len(st.session_state.enfrentamientos)
            }
            
            st.session_state.enfrentamientos.append(enfrentamiento)
            st.success(f"✅ Añadido: {equipo_a_name} vs {equipo_b_name}")
            st.rerun()
    
    if not can_add:
        missing = []
        if not background_file: missing.append("imagen de fondo")
        if not logo_a_file: missing.append("logo equipo A")
        if not logo_b_file: missing.append("logo equipo B")
        if not equipo_a_name: missing.append("nombre equipo A")
        if not equipo_b_name: missing.append("nombre equipo B")
        
        st.warning(f"⚠️ Faltan: {', '.join(missing)}")

with col2:
    st.header("📋 Cola de Enfrentamientos")
    
    if st.session_state.enfrentamientos:
        st.write(f"**{len(st.session_state.enfrentamientos)} enfrentamiento(s) en cola**")
        
        for i, enf in enumerate(st.session_state.enfrentamientos):
            with st.expander(f"🥊 {enf['equipo_a']} vs {enf['equipo_b']}"):
                st.write(f"**Fondo:** {enf['background'].name}")
                st.write(f"**Logo A:** {enf['logo_a'].name}")
                st.write(f"**Logo B:** {enf['logo_b'].name}")
                
                if st.button(f"❌ Eliminar", key=f"delete_{i}"):
                    st.session_state.enfrentamientos.pop(i)
                    st.rerun()
        
        if st.button("🗑️ Limpiar Toda la Cola", use_container_width=True):
            st.session_state.enfrentamientos = []
            st.rerun()
    else:
        st.info("No hay enfrentamientos en la cola")

# Generar imágenes
st.header("🚀 Generar Imágenes")

if st.session_state.enfrentamientos:
    if st.button("🎨 Generar Todas las Imágenes", use_container_width=True, type="primary"):
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w') as zipf:
            total_enfrentamientos = len(st.session_state.enfrentamientos)
            
            for i, enfrentamiento in enumerate(st.session_state.enfrentamientos):
                status_text.text(f"Generando: {enfrentamiento['equipo_a']} vs {enfrentamiento['equipo_b']}")
                
                try:
                    # Generar las 3 resoluciones
                    images = generate_enfrentamiento_images(enfrentamiento)
                    
                    for resolution, img_data in images.items():
                        filename = f"{enfrentamiento['equipo_a']} vs {enfrentamiento['equipo_b']} - {resolution}.jpg"
                        zipf.writestr(filename, img_data)
                    
                    progress_bar.progress((i + 1) / total_enfrentamientos)
                    
                except Exception as e:
                    st.error(f"Error generando {enfrentamiento['equipo_a']} vs {enfrentamiento['equipo_b']}: {str(e)}")
        
        zip_buffer.seek(0)
        status_text.text("¡Generación completada!")
        
        # Botón de descarga
        st.download_button(
            label="⬇️ Descargar Todas las Imágenes (ZIP)",
            data=zip_buffer,
            file_name="enfrentamientos_generados.zip",
            mime="application/zip",
            use_container_width=True
        )
        
        st.markdown("""
        <div class="success-box">
            ✅ <strong>¡Listo!</strong> Se generaron todas las imágenes en 3 resoluciones:<br>
            • 1920x1080 (Full HD)<br>
            • 3840x2160 (4K)<br>
            • 480x720 (Móvil)
        </div>
        """, unsafe_allow_html=True)

else:
    st.info("Añade enfrentamientos a la cola para generar imágenes")

def load_and_convert_logo(file_obj):
    """Carga y convierte logo desde un archivo subido"""
    if file_obj.name.lower().endswith('.svg'):
        if not CAIRO_AVAILABLE:
            raise Exception("Los archivos SVG no están soportados. Usa PNG/JPG.")
        
        try:
            # Leer contenido SVG
            svg_content = file_obj.read()
            png_data = cairosvg.svg2png(bytestring=svg_content)
            return Image.open(io.BytesIO(png_data)).convert("RGBA")
        except Exception as e:
            raise Exception(f"Error procesando SVG: {str(e)}")
    else:
        try:
            return Image.open(file_obj).convert("RGBA")
        except Exception as e:
            raise Exception(f"Error cargando imagen: {str(e)}")

def resize_logo(logo_image, max_size=450):
    """Redimensiona el logo manteniendo aspecto"""
    w, h = logo_image.size
    if w > h:
        new_w = max_size
        new_h = int(h * (max_size / w))
    else:
        new_h = max_size
        new_w = int(w * (max_size / h))
    return logo_image.resize((new_w, new_h), Image.LANCZOS)

def generate_enfrentamiento_images(enfrentamiento):
    """Genera las 3 resoluciones para un enfrentamiento"""
    images = {}
    
    # Configuraciones para cada resolución
    configs = [
        (1920, 1080, (476, 666), (1440, 666), 450, 130, "1920x1080"),
        (3840, 2160, (952, 1332), (2880, 1332), 900, 260, "3840x2160"),
        (480, 720, (120, 230), (360, 515), 177, 60, "480x720"),
    ]
    
    for width, height, logo_a_pos, logo_b_pos, logo_size, font_size, res_str in configs:
        # 1. Procesar imagen de fondo
        bg_image = Image.open(enfrentamiento['background']).convert("RGB")
        bg_width, bg_height = bg_image.size
        aspect_ratio_bg = bg_width / bg_height
        aspect_ratio_output = width / height

        if aspect_ratio_bg > aspect_ratio_output:
            new_width = int(height * aspect_ratio_bg)
            new_height = height
            bg_image = bg_image.resize((new_width, new_height), Image.LANCZOS)
            left = (new_width - width) / 2
            top = 0
            right = (new_width + width) / 2
            bottom = height
            bg_image = bg_image.crop((left, top, right, bottom))
        else:
            new_width = width
            new_height = int(width / aspect_ratio_bg)
            bg_image = bg_image.resize((new_width, new_height), Image.LANCZOS)
            left = 0
            top = (new_height - height) / 2
            right = width
            bottom = (new_height + height) / 2
            bg_image = bg_image.crop((left, top, right, bottom))

        # Aplicar desenfoque
        blur_radius = 14 if width == 1920 else 20 if width == 3840 else 10
        bg_image = bg_image.filter(ImageFilter.GaussianBlur(blur_radius))
        
        image = bg_image
        draw = ImageDraw.Draw(image)

        # 2. Añadir logos
        logo_a = load_and_convert_logo(enfrentamiento['logo_a'])
        logo_a = resize_logo(logo_a, max_size=logo_size)
        x_a = logo_a_pos[0] - logo_a.width // 2
        y_a = logo_a_pos[1] - logo_a.height // 2
        image.paste(logo_a, (x_a, y_a), logo_a)

        logo_b = load_and_convert_logo(enfrentamiento['logo_b'])
        logo_b = resize_logo(logo_b, max_size=logo_size)
        x_b = logo_b_pos[0] - logo_b.width // 2
        y_b = logo_b_pos[1] - logo_b.height // 2
        image.paste(logo_b, (x_b, y_b), logo_b)

        # 3. Añadir texto "VS."
        try:
            font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()

        text = "VS."
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        text_x = (width - text_width) // 2
        text_y = (height - text_height) // 2
        draw.text((text_x, text_y), text, fill="white", font=font)

        # Guardar en memoria
        img_buffer = io.BytesIO()
        image.save(img_buffer, format='JPEG', quality=95)
        images[res_str] = img_buffer.getvalue()
        img_buffer.close()
    
    return images

# Footer
st.markdown("---")
st.markdown("### 📊 Estadísticas")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Enfrentamientos en Cola", len(st.session_state.enfrentamientos))
with col2:
    total_images = len(st.session_state.enfrentamientos) * 3
    st.metric("Imágenes a Generar", total_images)
with col3:
    formats = "SVG, PNG, JPG" if CAIRO_AVAILABLE else "PNG, JPG"
    st.metric("Formatos Soportados", formats)
