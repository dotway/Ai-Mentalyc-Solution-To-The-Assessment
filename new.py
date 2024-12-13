# app.py

import streamlit as st
import time
import base64
import os
import PyPDF2
from vectors import EmbeddingsManager  # Import the EmbeddingsManager class
from chatbot import ChatbotManager  # Import the ChatbotManager class

def read_and_textify(files):
    text_list = []
    sources_list = []
    for file in files:
        pdfReader = PyPDF2.PdfReader(file)
        for i in range(len(pdfReader.pages)):
            pageObj = pdfReader.pages[i]
            text = pageObj.extract_text()
            pageObj.clear()
            text_list.append(text)
            sources_list.append(file.name + "_page_" + str(i))
    return [text_list, sources_list]

def displayPDF(file):
    # Reading the uploaded file
    base64_pdf = base64.b64encode(file.read()).decode('utf-8')
    # Embedding PDF in HTML
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="400" type="application/pdf"></iframe>'
    # Displaying the PDF
    st.markdown(pdf_display, unsafe_allow_html=True)

# Initialize session_state variables if not already present
if 'uploaded_files' not in st.session_state:
    st.session_state['uploaded_files'] = []

if 'chatbot_manager' not in st.session_state:
    st.session_state['chatbot_manager'] = None

if 'messages' not in st.session_state:
    st.session_state['messages'] = []

# Set the page configuration
st.set_page_config(
    page_title="Mentalyc Medical Chatbot AI App",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Sidebar
with st.sidebar:
    st.image("mentalyc_logo.png", use_container_width=True)
    st.markdown("### 📚 Your Personal Document Assistant")
    st.markdown("---")

    # Navigation Menu
    menu = ["🏠 Home", "🤖 Chatbot", "📧 Contact"]
    choice = st.selectbox("Navigate", menu)

# Home Page
if choice == "🏠 Home":
    st.title("📄 Mentalyc Medical Chatbot AI App")
    st.markdown("""
        Welcome to **Mentalyc Medical Chatbot AI App**! 🚀

        **Built using Open Source Stack (Llama 3.2, BGE Embeddings, and Qdrant running locally within a Docker Container.)**

        - **Upload Documents**: Easily upload your PDF documents.
        - **Summarize**: Get concise summaries of your documents.
        - **Chat**: Interact with your documents through our intelligent chatbot.

        Enhance your document management experience with Mentalyc Medical Chatbot! 😊
    """)

# Chatbot Page
elif choice == "🤖 Chatbot":
    st.title("🤖 Mentalyc Medical Chatbot Page")
    st.markdown("---")

    # Define two columns for layout
    col1, col2 = st.columns([1, 2])  # Adjust width ratios as needed

    # Left column: File Upload Section and Display Files
    with col1:
        st.header("📂 Upload and Display Files")
        uploaded_files = st.file_uploader("Upload PDF(s)", accept_multiple_files=True, type=["pdf", "txt"])

        if uploaded_files:
            st.session_state['uploaded_files'] = uploaded_files
            st.subheader("Uploaded Files Preview")
            for file in uploaded_files:
                st.markdown(f"**{file.name}**")
                with st.expander("Preview", expanded=False):
                    displayPDF(file)

    # Right column: Embeddings and Chatbot Interaction
    with col2:
        # Embeddings Section
        st.header("🧠 Create Embeddings")
        create_embeddings = st.button("✅ Create Embeddings")

        if create_embeddings:
            if not st.session_state['uploaded_files']:
                st.warning("⚠ Please upload at least two or more PDF file first.")
            else:
                try:
                    embeddings_manager = EmbeddingsManager(
                        model_name="sentence-transformers/all-mpnet-base-v2",
                        device="cpu",
                        encode_kwargs={"normalize_embeddings": True},
                        qdrant_url="http://localhost:6333",
                        collection_name="vector_db"
                    )
                    with st.spinner("🔄 Creating embeddings for uploaded files..."):
                        for file in st.session_state['uploaded_files']:
                            temp_path = f"temp_{file.name}"
                            with open(temp_path, "wb") as f:
                                f.write(file.getbuffer())
                            result = embeddings_manager.create_embeddings(temp_path)
                            os.remove(temp_path)
                    st.success("Embeddings created successfully!")

                    # Initialize chatbot manager after embeddings
                    if st.session_state['chatbot_manager'] is None:
                        st.session_state['chatbot_manager'] = ChatbotManager(
                            model_name="sentence-transformers/all-mpnet-base-v2",
                            device="cpu",
                            encode_kwargs={"normalize_embeddings": True},
                            llm_model="llama3.2:3b",
                            llm_temperature=0.7,
                            qdrant_url="http://localhost:6333",
                            collection_name="vector_db"
                        )
                except Exception as e:
                    st.error(f"An error occurred while creating embeddings: {e}")

        # Chatbot Interaction Section
        st.header("💬 Chat with Document")
        if st.session_state['chatbot_manager'] is None:
            st.info("🤖 Please upload two or more PDF files and create embeddings to start chatting.")
        else:
            # Display existing chat history
            for msg in st.session_state['messages']:
                st.chat_message(msg['role']).markdown(msg['content'])

            # Input area for user to type a message
            user_input = st.chat_input("Type your message here...")  # Displays the chat input box
            if user_input:
                # Append user's message to the chat history
                st.chat_message("user").markdown(user_input)
                st.session_state['messages'].append({"role": "user", "content": user_input})

                # Get and display the chatbot's response
                with st.spinner("🤖 Responding..."):
                    try:
                        answer = st.session_state['chatbot_manager'].get_response(user_input)
                    except Exception as e:
                        answer = f"⚠ An error occurred: {e}"

                # Append and display the chatbot's response
                st.chat_message("assistant").markdown(answer)
                st.session_state['messages'].append({"role": "assistant", "content": answer})



# Contact Page
elif choice == "📧 Contact":
    st.title("📬 Contact Us")
    st.markdown("""
        We'd love to hear from you! Whether you have a question, feedback, or want to contribute, feel free to reach out.

        - **Email:** [pope.dotun@gmail.com](mailto:pope.dotun@gmail.com) ✉
        - **GitHub:** [Contribute on GitHub](https://github.com/dotway?tab=repositories) 🛠

        If you'd like to request a feature or report a bug, please open a pull request on our GitHub repository. Your contributions are highly appreciated! 🙌
    """)

# Footer
st.markdown("---")
st.markdown("© 2024 Mentalyc Medical Chatbot App by AI Mentalyc. All rights reserved. 🛡")
