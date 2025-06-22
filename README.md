# Badkamer Tegel Visualizer

This Streamlit application allows you to visualize how new tiles would look in your bathroom. You can upload a photo of your bathroom and a photo of the desired tiles, and the application will generate a new image with the tiles replaced.

## How to Run Locally

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Install dependencies:**
    Make sure you have Python installed. Then, install the required packages using pip:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Set up your Secrets:**
    This application uses the OpenAI API and requires a password for access. You need to provide your API key and set a password. For local development, create a file `.streamlit/secrets.toml` and add your secrets there:

    ```toml
    # .streamlit/secrets.toml
    OPENAI_API_KEY = "sk-..."
    PASSWORD = "your_secret_password"
    ```

4.  **Run the application:**
    ```bash
    streamlit run app.py
    ```

## Deploying to Streamlit Community Cloud

1.  **Push your code to a GitHub repository.** Streamlit Community Cloud deploys apps directly from GitHub.

2.  **Sign up for Streamlit Community Cloud:**
    If you don't have an account, you can sign up for free at [streamlit.io/cloud](https://streamlit.io/cloud).

3.  **Deploy the app:**
    - Click on "New app" from your workspace.
    - Connect your GitHub account and select the repository.
    - The branch and main file path (`app.py`) should be detected automatically.
    - In the "Advanced settings" section, you need to add your secrets.
        - **Secret 1:**
            - **Variable:** `OPENAI_API_KEY`
            - **Value:** Paste your actual OpenAI API key here (`sk-...`).
        - **Secret 2:**
            - **Variable:** `PASSWORD`
            - **Value:** Set the password you want to use.
    - Click "Deploy!". Streamlit will handle the rest. 