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

def generate_bathroom_visualization(original_image, selected_tile, client, tile_name=""):
    """Generate bathroom visualization with new tiles using gpt-4.1 responses API"""
    
    try:
        # Convert images to base64
        bathroom_b64 = encode_image_to_base64(original_image)
        tile_b64 = encode_image_to_base64(selected_tile)
        
        # Create the prompt
        prompt = """
        Generate a photorealistic bathroom image that maintains EXACTLY the same layout, flooring, fixtures, and overall appearance as the original bathroom photo, with ONLY the wall tiles changed to match the new tile style shown in the reference image.
CRITICAL REQUIREMENTS - DO NOT CHANGE:
Keep 100% identical:

Exact positions of toilet, sink, bathtub, and all fixtures
Same lighting conditions, shadows, and brightness levels
Identical spatial dimensions and camera perspective
Same faucets, handles, and hardware in exact positions
Same exact flooring material and color
Same window size and position
Same overall room condition and age
Same plumbing fixture styles and finishes

ONLY CHANGE:

Replace wall tiles with the new wall panel system from reference image
Apply new panels ONLY to wall surfaces that currently have tiles
Show panels as large, seamless surfaces without visible joints or grout lines
Maintain realistic lighting reflections on new panel surfaces
Panels should appear as continuous, smooth wall covering

TECHNICAL SPECIFICATIONS:

Style: Architectural photography documentation
Quality: Photorealistic interior rendering
Lighting: Match original photo's natural lighting exactly
Perspective: Keep identical camera angle and framing

IMPORTANT: This is a wall panel material substitution only - do not upgrade, modernize, or improve any other elements of the bathroom. The new wall covering should appear as seamless panels without panel joints or grout lines.
        """
        
        # Add finish-specific instructions to the prompt based on the tile name
        finish_instruction = ""
        tile_name_lower = tile_name.lower()
        if "glans" in tile_name_lower:
            finish_instruction = "\n\nFINISH-SPECIFIC REQUIREMENT: The new wall panels must have a glossy, high-shine finish. Ensure that reflections on the panels are sharp, clear, and accurately represent the lighting in the room, similar to polished marble or glass."
        elif "mat" in tile_name_lower:
            finish_instruction = "\n\nFINISH-SPECIFIC REQUIREMENT: The new wall panels must have a matte, non-reflective finish. Ensure that light on the panels is diffused and soft, with no sharp or clear reflections, similar to honed stone or a sandblasted surface."

        prompt += finish_instruction
        
        # Use the responses.create API with gpt-4.1
        response = client.responses.create(
            model="gpt-4.1",
            input=[
                {
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
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
            # Get the base64 encoded image
            image_base64 = image_data[0]
            image_bytes = base64.b64decode(image_base64)
            
            # Convert to PIL Image
            generated_image = Image.open(io.BytesIO(image_bytes))
            return generated_image
        else:
            # If no image was generated, show the text response
            st.error("Geen afbeelding gegenereerd. Antwoord van API:")
            if hasattr(response, 'output') and hasattr(response.output, 'content'):
                st.write(response.output.content)
            return None
        
    except Exception as e:
        st.error(f"Fout bij het genereren van afbeelding: {str(e)}")
        return None

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
        
        # Option 1: Upload custom tile image
        #st.subheader("Upload eigen tegelafbeelding")
        #uploaded_tile = st.file_uploader(
        #    "Upload een foto van de gewenste tegels",
        ##    type=['png', 'jpg', 'jpeg'],
        #    key="tile_upload"
        #)
        
        #st.markdown("<p style='text-align: center; font-weight: bold;'>OF</p>", unsafe_allow_html=True)

        # Option 2: Choose from a predefined list
        st.subheader("Kies een wandpaneel uit de lijst")

        # Define tile options (name -> image path)
        # TODO: Zorg ervoor dat de afbeeldingspaden correct zijn en de bestanden bestaan.
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
        
        # Determine which tile to use (uploaded or selected)
        final_tile_image = None
        
        #if uploaded_tile:
        #    final_tile_image = Image.open(uploaded_tile)
        #    st.image(final_tile_image, caption="Gekozen tegel (upload)", width=None)
        if selected_tile_name != "--- Selecteer een wandpaneel ---":
            tile_path = tile_options[selected_tile_name]
            try:
                final_tile_image = Image.open(tile_path)
                st.image(final_tile_image, caption=f"Gekozen wandpaneel: {selected_tile_name}", width=None)
            except FileNotFoundError:
                st.warning(f"Afbeelding voor '{selected_tile_name}' niet gevonden. Zorg dat het bestand op `{tile_path}` staat.")
                # Create a placeholder image if file not found
                final_tile_image = Image.new('RGB', (200, 200), color = 'grey')
                st.image(final_tile_image, caption=f"Placeholder voor {selected_tile_name}", width=None)

    
    # Generate button
    st.markdown("---")
    col_center = st.columns([1, 2, 1])[1]
    
    with col_center:
        if st.button("✨ Genereer Visualisatie", type="primary"):
            if uploaded_bathroom and final_tile_image:
                
                with st.spinner("Aan het genereren van je nieuwe badkamer ontwerp..."):
                    
                    # Determine tile name for prompt modification.
                    # This only applies when a tile is selected from the list.
                    tile_name_for_prompt = ""
                    #if not uploaded_tile and selected_tile_name != "--- Selecteer een wandpaneel ---":
                    if selected_tile_name != "--- Selecteer een wandpaneel ---":
                        tile_name_for_prompt = selected_tile_name

                    # Generate the visualization
                    result_image = generate_bathroom_visualization(
                        Image.open(uploaded_bathroom), 
                        final_tile_image, 
                        client,
                        tile_name=tile_name_for_prompt
                    )
                    
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
                            st.subheader("Na - Met nieuwe wandpanelen")
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
                            file_name="badkamer_nieuwe_panelen.png",
                            mime="image/png",
                            type="primary"
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