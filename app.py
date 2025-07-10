import streamlit as st
import base64
from openai import OpenAI
import openai
from PIL import Image
import io
import os

def check_password():
    """Returns `True` if the user has entered the correct password."""
    
    try:
        # This will raise an error if secrets.toml doesn't exist or if the password is not set.
        password_from_secrets = st.secrets["PASSWORD"]
    except FileNotFoundError:
        st.error("No secrets file found.")
        st.info("To run this app, you need to create a `secrets.toml` file in a `.streamlit` directory at the root of your project.")
        st.code("""
# .streamlit/secrets.toml
OPENAI_API_KEY = "your-openai-api-key"
PASSWORD = "your-password"
        """, language="toml")
        st.info("Please add your credentials and then refresh the page.")
        return False
    except KeyError:
        st.error("Password not found in secrets.")
        st.info("Please add `PASSWORD = 'your-password'` to your `.streamlit/secrets.toml` file and refresh.")
        return False

    def password_entered():
        """Checks whether the password entered by the user is correct."""
        if st.session_state["password"] == password_from_secrets:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # delete password from session state
        else:
            st.session_state["password_correct"] = False

    if st.session_state.get("password_correct", False):
        return True

    # Show password input
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password"
    )

    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 Password incorrect")
        
    return st.session_state.get("password_correct", False)

# Initialize OpenAI client
@st.cache_resource
def get_openai_client():
    # Make sure you have the latest OpenAI library: pip install openai>=1.0.0
    if "OPENAI_API_KEY" not in st.secrets or not st.secrets["OPENAI_API_KEY"]:
        st.error("OpenAI API key not found in secrets.")
        st.info("Please add `OPENAI_API_KEY = 'sk-...'` to your `.streamlit/secrets.toml` file and refresh.")
        st.stop()
        
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    
    # Debug: Check if responses attribute exists
    if not hasattr(client, 'responses'):
        st.error("OpenAI library version might be incompatible. Please check requirements.")
        st.stop()
    
    return client

def encode_image_to_base64(image):
    """Convert PIL Image to base64 string"""
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode()

def get_finish_instruction(tile_name):
    """Get finish-specific instruction based on tile name"""
    if not tile_name:
        return "Apply appropriate finish based on reference image"
    
    tile_name_lower = tile_name.lower()
    if any(keyword in tile_name_lower for keyword in ["glans", "hoogglans"]):
        return "Apply glossy, reflective finish with sharp, clear reflections that accurately show the room's lighting"
    elif any(keyword in tile_name_lower for keyword in ["mat", "matte"]):
        return "Apply matte, non-reflective finish with soft, diffused lighting and no sharp reflections"
    else:
        return "Apply finish matching the reference image characteristics"

# def generate_with_inpainting_style(original_image, selected_tile, client, tile_name=""):
#     """Use inpainting-style prompting to be more precise about what to change"""
    
#     try:
#         bathroom_b64 = encode_image_to_base64(original_image)
#         tile_b64 = encode_image_to_base64(selected_tile)
        
#         finish_instruction = get_finish_instruction(tile_name)
        
#         inpainting_prompt = f"""
# INPAINTING TASK: Replace wall panel material in specific areas only, like digital inpainting.

# STEP-BY-STEP INSTRUCTIONS:
# 1. Analyze the bathroom image to identify main room wall surfaces (large vertical background walls)
# 2. Keep EVERYTHING else exactly identical - preserve all fixtures, surfaces, and details
# 3. Replace ONLY the main wall surfaces with the new panel material from reference
# 4. Ensure seamless, grout-free, joint-free installation of panels

# AREAS TO PRESERVE (copy exactly from original - DO NOT MODIFY):
# ✓ Bathtub: ALL tiles/cladding on front, sides, and edges of bathtub
# ✓ Toilet: ALL tiles/surfaces around toilet base and surrounding floor area
# ✓ Floor: ALL flooring tiles throughout the entire room
# ✓ Window: Exact size, position, frame, and glass
# ✓ Lighting: Same shadows, brightness, and light direction
# ✓ Hardware: All faucets, handles, towel bars, fixtures
# ✓ Perspective: Exact same camera angle and viewpoint
# ✓ Ceiling: All ceiling surfaces and features

# AREAS TO REPLACE (only these specific areas):
# → Main vertical wall surfaces in the background (large wall areas)
# → Wall surfaces that are clearly separate from fixture areas
# → Apply new panel material with completely seamless, continuous finish
# → Show as smooth, uninterrupted surface with ZERO joints, grout lines, or seams
# → Panels should appear as one continuous wall covering

# TECHNICAL EXECUTION REQUIREMENTS:
# - Photorealistic architectural photography quality
# - Exact lighting preservation from original image
# - {finish_instruction}
# - Maintain all spatial relationships and proportions exactly
# - No modernization, upgrading, or improvement of any elements

# CRITICAL CONSTRAINT: Think of this as selectively replacing ONLY the wall covering material on main room walls while preserving every other element perfectly. This is precise material substitution, not renovation.
# """
        
#         # Generate the image
#         response = client.responses.create(
#             model="gpt-4.1",
#             input=[
#                 {
#                     "role": "user",
#                     "content": [
#                         {"type": "input_text", "text": inpainting_prompt},
#                         {
#                             "type": "input_image",
#                             "image_url": f"data:image/png;base64,{bathroom_b64}",
#                         },
#                         {
#                             "type": "input_image",
#                             "image_url": f"data:image/png;base64,{tile_b64}",
#                         }
#                     ],
#                 }
#             ],
#             tools=[{"type": "image_generation"}],
#         )
        
#         # Extract image generation results
#         image_generation_calls = [
#             output
#             for output in response.output
#             if output.type == "image_generation_call"
#         ]
        
#         image_data = [output.result for output in image_generation_calls]
        
#         if image_data:
#             # Get the base64 encoded image
#             image_base64 = image_data[0]
#             image_bytes = base64.b64decode(image_base64)
            
#             # Convert to PIL Image
#             generated_image = Image.open(io.BytesIO(image_bytes))
#             return generated_image
#         else:
#             # If no image was generated, show the text response
#             st.error("Geen afbeelding gegenereerd. Antwoord van API:")
#             if hasattr(response, 'output'):
#                 for output in response.output:
#                     if hasattr(output, 'content'):
#                         st.write(output.content)
#             return None
#     except Exception as e:
#         st.error(f"Fout bij het genereren van afbeelding: {str(e)}")
#         return None

def generate_with_ultra_specific_masking(original_image, selected_tile, client, tile_name=""):
    """Use ultra-specific masking language to prevent fixture modification"""
    
    try:
        bathroom_b64 = encode_image_to_base64(original_image)
        tile_b64 = encode_image_to_base64(selected_tile)
        
        finish_instruction = get_finish_instruction(tile_name)
        
        ultra_specific_prompt = f"""
CRITICAL MASKING TASK: Apply new wall panels ONLY to specific masked areas.

MASKING RULES - ABSOLUTE BOUNDARIES:
🚫 PROTECTED ZONES (NEVER TOUCH - KEEP 100% ORIGINAL):
- Bathtub structure: ALL sides, front panel, edges, rim, and any tiles directly touching the bathtub
- Toilet area: ALL surfaces within 50cm radius of toilet, including floor and wall tiles around toilet
- Floor: ENTIRE floor surface throughout the room - no changes whatsoever
- Window and frame: Complete window assembly and surrounding areas
- All fixtures, hardware, pipes, faucets, handles, towel bars
- Ceiling and any ceiling-mounted elements

✅ MODIFICATION ZONE (ONLY THESE AREAS):
- Large vertical wall surfaces that are clearly separated from fixtures
- Main room background walls that do not touch or connect to bathtub or toilet
- Wall areas that are at least 1 meter away from any fixture

SPATIAL IDENTIFICATION PROCESS:
1. Identify the bathtub location and mark ALL adjacent surfaces as PROTECTED
2. Identify the toilet location and mark ALL surrounding surfaces as PROTECTED  
3. Mark the floor as completely PROTECTED
4. Find ONLY the main room walls that are isolated from fixtures
5. Apply panels ONLY to these isolated wall areas

PANEL APPLICATION REQUIREMENTS:
- Show panels as seamless, continuous surface with ZERO joints or grout lines
- {finish_instruction}
- Maintain exact lighting from original photo
- Apply ONLY to the identified safe wall zones

TECHNICAL EXECUTION:
- Photorealistic quality matching original
- Preserve exact camera angle and perspective
- No modernization or upgrades to any elements
- Think of this as applying wallpaper to specific wall sections only

VERIFICATION CHECK: Before applying panels, verify that NO part of the bathtub structure or toilet area will be modified. The bathtub must remain exactly as it is in the original photo.
"""
        
        # Generate the image
        response = client.responses.create(
            model="gpt-4.1",
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": ultra_specific_prompt},
                        {
                            "type": "input_image",
                            "image_url": f"data:image/png;base64,{bathroom_b64}",
                        },
                        {
                            "type": "input_image",
                            "image_url": f"data:image/png;base64,{tile_b64}",
                        }
                    ],
                }
            ],
            tools=[{"type": "image_generation"}],
        )
        
        # Extract image generation results
        image_generation_calls = [
            output
            for output in response.output
            if output.type == "image_generation_call"
        ]
        
        image_data = [output.result for output in image_generation_calls]
        
        if image_data:
            image_base64 = image_data[0]
            image_bytes = base64.b64decode(image_base64)
            generated_image = Image.open(io.BytesIO(image_bytes))
            return generated_image
        else:
            st.error("Geen afbeelding gegenereerd.")
            return None
        
    except Exception as e:
        st.error(f"Fout bij het genereren van afbeelding: {str(e)}")
        return None


# def generate_with_two_step_approach(original_image, selected_tile, client, tile_name=""):
#     """Two-step approach: First analyze, then generate"""
    
#     try:
#         bathroom_b64 = encode_image_to_base64(original_image)
#         tile_b64 = encode_image_to_base64(selected_tile)
        
#         # Step 1: Spatial analysis
#         analysis_prompt = """
# SPATIAL ANALYSIS TASK:

# Analyze this bathroom image and provide a detailed, factual description of:

# 1. BATHTUB STRUCTURE AND CLADDING:
#    - Precisely describe the bathtub's position.
#    - Identify ALL surfaces that form the bathtub structure itself. This includes the front panel/apron, the side panels, and the top rim.
#    - Describe the material/finish of these bathtub surfaces (e.g., 'tiled front panel', 'acrylic side'). THIS IS A CRITICAL DETAIL.

# 2. TOILET LOCATION AND BOUNDARIES:
#    - Where exactly is the toilet positioned?
#    - What surfaces are around the toilet base?
#    - What wall and floor areas are in the toilet zone?

# 3. WALLS vs. FIXTURE CLADDING:
#     - Distinguish between the main room walls and the tiles/panels attached to the bathtub.
#     - Explicitly list which surfaces are 'main walls' (safe to change) and which are 'bathtub cladding' (must be preserved).

# Your analysis must create a clear boundary between the room's walls and the bathtub's own surfaces.
# """
        
#         # Get spatial analysis
#         analysis_response = client.responses.create(
#             model="gpt-4.1",
#             input=[
#                 {
#                     "role": "user",
#                     "content": [
#                         {"type": "input_text", "text": analysis_prompt},
#                         {
#                             "type": "input_image",
#                             "image_url": f"data:image/png;base64,{bathroom_b64}",
#                         }
#                     ],
#                 }
#             ]
#         )
        
#         # Extract analysis text (you could process this further)
#         analysis_text = ""
#         if hasattr(analysis_response, 'output'):
#             for output in analysis_response.output:
#                 if hasattr(output, 'content'):
#                     analysis_text += str(output.content)
        
#         # Step 2: Generate with analysis context
#         finish_instruction = get_finish_instruction(tile_name)
        
#         generation_prompt = f"""
# PRECISION PANEL APPLICATION TASK:

# You must follow the provided spatial analysis to avoid modifying fixtures.

# ANALYSIS SUMMARY:
# {analysis_text[:1000]}...

# EXECUTION RULES (NON-NEGOTIABLE):
# 1. **PROTECT BATHTUB:** Preserve the bathtub and ALL of its own surfaces (front panel, side panel, rim) EXACTLY as they appear in the original image. The analysis identifies these as 'bathtub cladding'. DO NOT change the material of the bathtub's panels.
# 2. **MODIFY WALLS ONLY:** Apply the new panel material ONLY to the surfaces identified as 'main walls' in the analysis. These are the large, vertical background walls of the room itself.
# 3. **SEAMLESS FINISH:** The new panels on the walls must be seamless, with no grout lines.
# 4. {finish_instruction}
# 5. Maintain photorealistic quality, original lighting, and camera perspective.

# VERIFICATION: Before outputting the image, double-check that the bathtub's front and side panels are UNCHANGED from the original photo.
# """
        
#         # Generate final image
#         response = client.responses.create(
#             model="gpt-4.1",
#             input=[
#                 {
#                     "role": "user",
#                     "content": [
#                         {"type": "input_text", "text": generation_prompt},
#                         {
#                             "type": "input_image",
#                             "image_url": f"data:image/png;base64,{bathroom_b64}",
#                         },
#                         {
#                             "type": "input_image",
#                             "image_url": f"data:image/png;base64,{tile_b64}",
#                         }
#                     ],
#                 }
#             ],
#             tools=[{"type": "image_generation"}],
#         )
        
#         # Extract image
#         image_generation_calls = [
#             output for output in response.output
#             if output.type == "image_generation_call"
#         ]
        
#         if image_generation_calls:
#             image_data = image_generation_calls[0].result
#             image_bytes = base64.b64decode(image_data)
#             return Image.open(io.BytesIO(image_bytes))
        
#         return None
        
#     except Exception as e:
#         st.error(f"Fout bij het genereren van afbeelding: {str(e)}")
#         return None


# def generate_with_conservative_approach(original_image, selected_tile, client, tile_name=""):
#     """Most conservative approach - only touch obvious wall areas"""
    
#     try:
#         bathroom_b64 = encode_image_to_base64(original_image)
#         tile_b64 = encode_image_to_base64(selected_tile)
        
#         finish_instruction = get_finish_instruction(tile_name)
        
#         conservative_prompt = f"""
# CONSERVATIVE WALL PANEL APPLICATION:

# TASK: Replace wall covering on ONLY the most obvious, safe wall areas.

# ULTRA-CONSERVATIVE RULES:
# 🔒 COMPLETELY OFF-LIMITS (DO NOT EVEN CONSIDER):
# - Anything connected to or near the bathtub
# - Anything connected to or near the toilet  
# - Any horizontal surfaces (floor, bathtub rim, etc.)
# - Any fixture-adjacent areas
# - Window and window surrounds

# 🎯 SAFE MODIFICATION ZONES (ONLY IF CLEARLY SEPARATE):
# - Large, obvious background wall surfaces
# - Wall areas that are visibly distant from any fixture
# - Plain wall sections that clearly don't belong to fixtures

# APPLICATION METHOD:
# - Think like you're hanging wallpaper on a few select wall sections
# - Only touch areas you're 100% certain are main room walls
# - Show seamless panels with zero joints, grout, or texture lines
# - {finish_instruction}
# - Keep photorealistic quality and exact lighting

# SAFETY FIRST: When in doubt, don't modify. Better to change too little than to accidentally modify fixture areas.

# VERIFICATION: The bathtub should look exactly like the original photo - same color, same materials, same everything.
# """
        
#         response = client.responses.create(
#             model="gpt-4.1",
#             input=[
#                 {
#                     "role": "user",
#                     "content": [
#                         {"type": "input_text", "text": conservative_prompt},
#                         {
#                             "type": "input_image",
#                             "image_url": f"data:image/png;base64,{bathroom_b64}",
#                         },
#                         {
#                             "type": "input_image",
#                             "image_url": f"data:image/png;base64,{tile_b64}",
#                         }
#                     ],
#                 }
#             ],
#             tools=[{"type": "image_generation"}],
#         )
        
#         image_generation_calls = [
#             output for output in response.output
#             if output.type == "image_generation_call"
#         ]
        
#         if image_generation_calls:
#             image_data = image_generation_calls[0].result
#             image_bytes = base64.b64decode(image_data)
#             return Image.open(io.BytesIO(image_bytes))
        
#         return None
        
#     except Exception as e:
#         st.error(f"Fout bij het genereren van afbeelding: {str(e)}")
#         return None

def main():
    st.set_page_config(
        page_title="Badkamer Wandpaneel Visualizer",
        page_icon="🛁",
        layout="wide"
    )
    
    if not check_password():
        st.stop()
    
    st.title("🛁 Badkamer Wandpaneel Visualizer")
    st.markdown("Upload een foto van je badkamer en kies nieuwe wandpanelen om te zien hoe het eruit zou zien!")
    
    # Initialize OpenAI client
    try:
        client = get_openai_client()
    except Exception:
        # Errors from get_openai_client are handled with st.stop(),
        # but we catch here to prevent the app from continuing.
        st.stop()
    
    # Create two columns
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📸 Upload je badkamer foto")
        uploaded_bathroom = st.file_uploader(
            "Kies een foto van je badkamer",
            type=['png', 'jpg', 'jpeg'],
            key="bathroom_upload"
        )
        
        if uploaded_bathroom:
            bathroom_image = Image.open(uploaded_bathroom)
            st.image(bathroom_image, caption="Je badkamer", width=None)
    
    with col2:
        st.header("🏠 Kies je wandpanelen")
        
        # Choose from a predefined list
        st.subheader("Kies een wandpaneel uit de lijst")

        # Define tile options (name -> image path)
        tile_options = {
            "--- Selecteer een wandpaneel ---": None,
            "PVC Hoogglans Calacatta Wit": "tiles/pvc_hoogglans_calacatta_wit.jpg",
            "PVC Hoogglans Bianco Venato Wit": "tiles/pvc_hoogglans_bianco_venato_wit.jpg",
            "PVC Hoogglans Carrara Wit": "tiles/pvc_hoogglans_carrara_wit.jpg",
            "PVC Hoogglans Effen Wit": "tiles/pvc_hoogglans_effen_wit.jpg",
            "PVC Hoogglans Eclipse Marble": "tiles/pvc_hoogglans_eclipse_marble.jpg",
            "PVC Hoogglans Glazed Taupe Marble": "tiles/pvc_hoogglans_glazed_taupe_marble.jpg",
            "PVC Hoogglans Grigio Orobico Gold": "tiles/pvc_hoogglans_grigio_orobico_gold.jpg",
            "PVC Hoogglans Marquina Zwart": "tiles/pvc_hoogglans_marquina_zwart.jpg",
            "PVC Hoogglans Onyx Grigio": "tiles/pvc_hoogglans_onyx_grigio.jpg",
            "PVC Hoogglans Stone Marble": "tiles/pvc_hoogglans_stone_marble.jpg",
            "PVC Silver Wave Glans Grijs": "tiles/pvc_silver_wave_glans_grijs.jpg",
            "PVC Carnico Glans Grijs": "tiles/pvc_carnico_glans_grijs.jpg",
            "PVC Calacatta Gold Matte": "tiles/pvc_calacatta_gold_matte.jpg",
            "PVC Carnico Mat Grijs": "tiles/pvc_carnico_mat_grijs.jpg",
            "PVC Crema Marfil Mat Beige": "tiles/pvc_crema_marfil_mat_beige.jpg",
            "PVC Nero Marquina Gold Mat Zwart": "tiles/pvc_nero_marquina_gold_mat_zwart.jpg",
            "PVC Pietra Grey Mat Grijs": "tiles/pvc_pietra_grey_mat_grijs.jpg",
            "PVC Sandstone Mat Beige": "tiles/pvc_sandstone_mat_beige.jpg",
            "PVC Taupe Marble Matte": "tiles/pvc_taupe_marble_matte.jpg",
            "SPC Beton Look Mat Grijs": "tiles/spc_beton_look_mat_grijs.jpg",
            "SPC Breccia Pernice Mat": "tiles/spc_breccia_pernice_mat.jpg",
            "SPC Carrara Mat Grijs": "tiles/spc_carrara_mat_grijs.jpg",
            "SPC Carrara Matte White": "tiles/spc_carrara_matte_white.jpg",
            "SPC Crema Marfil Mat Beige": "tiles/spc_crema_marfil_mat_beige.jpg",
            "SPC Desert Mist Mat Taupe Beige": "tiles/spc_desert_mist_mat_taupe_beige.jpg",
            "SPC Emperador Dark Mat Bruin": "tiles/spc_emperador_dark_mat_bruin.jpg",
            "SPC Forest Slate Mat Groen Bruin": "tiles/spc_forest_slate_mat_groen_bruin.jpg",
            "SPC Granite Mist Matte": "tiles/spc_granite_mist_matte.jpg",
            "SPC Marmer Mat Beige Taupe": "tiles/spc_marmer_mat_beige_taupe.jpg",
            "SPC Rustic Copper Stone Mat Koper": "tiles/spc_rustic_copper_stone_mat_koper.jpg",
            "SPC Rustic Stone Mat": "tiles/spc_rustic_stone_mat.jpg",
            "SPC Serpeggiante Marble Mat Beige Groen": "tiles/spc_serpeggiante_marble_mat_beige_groen.jpg",
            "SPC Silk Marble Matte": "tiles/spc_silk_marble_matte.jpg",
            "SPC Smoky Granite Matte": "tiles/spc_smoky_granite_matte.jpg",
            "SPC Stone Grey Mat Grijs": "tiles/spc_stone_grey_mat_grijs.jpg",
        }
        
        selected_tile_name = st.selectbox(
            "Kies een wandpaneel",
            options=list(tile_options.keys())
        )
        
        # Determine which tile to use
        final_tile_image = None
        
        if selected_tile_name != "--- Selecteer een wandpaneel ---":
            tile_path = tile_options[selected_tile_name]
            try:
                final_tile_image = Image.open(tile_path)
                st.image(final_tile_image, caption=f"Gekozen wandpaneel: {selected_tile_name}", width=None)
            except FileNotFoundError:
                st.warning(f"Afbeelding voor '{selected_tile_name}' niet gevonden. Zorg dat het bestand op `{tile_path}` staat.")
                # Create a placeholder image if file not found
                final_tile_image = Image.new('RGB', (200, 200), color='grey')
                st.image(final_tile_image, caption=f"Placeholder voor {selected_tile_name}", width=None)

    # Generate button
    st.markdown("---")
    col_center = st.columns([1, 2, 1])[1]
    
    with col_center:
        # Simplified generation button
        if st.button("✨ Genereer Visualisatie", type="primary", use_container_width=True):
            if uploaded_bathroom and final_tile_image:
                
                with st.spinner("Bezig met genereren via de 'Ultra Specifiek' methode..."):
                    
                    try:
                        # Determine tile name for prompt modification
                        tile_name_for_prompt = ""
                        if selected_tile_name != "--- Selecteer een wandpaneel ---":
                            tile_name_for_prompt = selected_tile_name

                        # Generate with the best method
                        result_image = generate_with_ultra_specific_masking(
                            Image.open(uploaded_bathroom), 
                            final_tile_image, 
                            client,
                            tile_name=tile_name_for_prompt
                        )
                    
                    except Exception as e:
                        st.error(f"Er is een fout opgetreden bij het genereren: {str(e)}")
                        result_image = None
                    
                    if result_image:
                        st.success("✅ Visualisatie gegenereerd!")
                        
                        # Display results
                        st.header("🎨 Resultaat")
                        
                        # Show before and after
                        result_col1, result_col2 = st.columns(2)
                        
                        with result_col1:
                            st.subheader("Voor")
                            st.image(Image.open(uploaded_bathroom), width=None)
                        
                        with result_col2:
                            st.subheader("Na - Ultra Specifiek")
                            st.image(result_image, width=None)
                        
                        # Download option
                        st.markdown("---")
                        
                        # Convert image to bytes for download
                        img_buffer = io.BytesIO()
                        result_image.save(img_buffer, format='PNG')
                        img_bytes = img_buffer.getvalue()
                        
                        st.download_button(
                            label="💾 Download resultaat",
                            data=img_bytes,
                            file_name="badkamer_visualisatie.png",
                            mime="image/png",
                            type="primary",
                            use_container_width=True
                        )
                        
            else:
                st.warning("⚠️ Upload eerst een badkamer foto en kies een wandpaneel om te beginnen!")

    # Footer
    st.markdown("---")
    st.markdown("*Gemaakt door DeltaFlow AI*")
    
    # Debug info
    with st.expander("🔧 Debug Info"):
        st.write(f"OpenAI library version: {getattr(openai, '__version__', 'Unknown')}")
        try:
            client = get_openai_client() 
            st.write(f"Client has 'responses' attribute: {hasattr(client, 'responses')}")
        except Exception as e:
            st.write(f"Could not check client attributes: {e}")

if __name__ == "__main__":
    main()