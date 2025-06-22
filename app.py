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

def generate_bathroom_visualization(original_image, selected_tile, client):
    """Generate bathroom visualization with new tiles using gpt-4.1 responses API"""
    
    try:
        # Convert images to base64
        bathroom_b64 = encode_image_to_base64(original_image)
        tile_b64 = encode_image_to_base64(selected_tile)
        
        # Create the prompt
        prompt = """
        Generate a photorealistic bathroom image that maintains EXACTLY the same layout, fixtures, and overall appearance as the original bathroom photo, with ONLY the wall tiles changed to match the new tile style shown in the reference image.
CRITICAL REQUIREMENTS - DO NOT CHANGE:
Keep 100% identical:

Exact positions of toilet, sink, bathtub, and all fixtures
Same lighting conditions, shadows, and brightness levels
Identical spatial dimensions and camera perspective
Same faucets, handles, and hardware in exact positions
Same flooring material and color
Same window size and position
Same overall room condition and age
Same plumbing fixture styles and finishes

ONLY CHANGE:

Replace wall tiles with the new tile pattern/style from reference image
Apply new tiles ONLY to wall surfaces that currently have tiles
Maintain realistic lighting reflections on new tile surfaces

TECHNICAL SPECIFICATIONS:

Style: Architectural photography documentation
Quality: Photorealistic interior rendering
Lighting: Match original photo's natural lighting exactly
Perspective: Keep identical camera angle and framing

IMPORTANT: This is a tile material substitution only - do not upgrade, modernize, or improve any other elements of the bathroom.
        """
        
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
        page_title="Badkamer Tegel Visualizer",
        page_icon="🛁",
        layout="wide"
    )
    
    if not check_password():
        st.stop()
    
    st.title("🛁 Badkamer Tegel Visualizer")
    st.markdown("Upload een foto van je badkamer en kies nieuwe tegels om te zien hoe het eruit zou zien!")
    
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
        st.header("🏠 Kies je tegels")
        
        # Option 1: Upload custom tile image
        st.subheader("Upload eigen tegelafbeelding")
        uploaded_tile = st.file_uploader(
            "Upload een foto van de gewenste tegels",
            type=['png', 'jpg', 'jpeg'],
            key="tile_upload"
        )
        

        
        # Display selected tile
        if uploaded_tile:
            tile_image = Image.open(uploaded_tile)
            st.image(tile_image, caption="Gekozen tegels", width=None)

    
    # Generate button
    st.markdown("---")
    col_center = st.columns([1, 2, 1])[1]
    
    with col_center:
        if st.button("✨ Genereer Visualisatie", type="primary"):
            if uploaded_bathroom and uploaded_tile:
                
                with st.spinner("Aan het genereren van je nieuwe badkamer ontwerp..."):
                    
                    # Use uploaded tile
                    final_tile_image = Image.open(uploaded_tile)
           
                    # Generate the visualization
                    result_image = generate_bathroom_visualization(
                        Image.open(uploaded_bathroom), 
                        final_tile_image, 
                        client
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
                            st.subheader("Na - Met nieuwe tegels")
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
                            file_name="badkamer_nieuwe_tegels.png",
                            mime="image/png",
                            type="primary"
                        )
                        
            else:
                st.warning("⚠️ Upload eerst een badkamer foto en kies tegels om te beginnen!")


    
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