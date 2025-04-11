import streamlit as st
import requests
import toml
from bs4 import BeautifulSoup

gemini_api_key = st.secrets.get("gemini", {}).get("api_key", None)

def call_gemini_api(text, images):
    """
    Calls the API with a minimal payload that combines the page text and image URLs.
    """
    if not gemini_api_key:
        return "Gemini API key not found. Please check your config.toml file."

    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_api_key}"

    combined_input = (
        "Web Page Content:\n" +
        text +
        "\n\nImages:\n" +
        (', '.join(images) if images else "None") +
        "\n\nPlease provide a brief summary of the above content."
    )

    payload = {
        "contents": [{
            "parts": [{"text": combined_input}]
        }]
    }

    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(gemini_url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        if "candidates" in data and data["candidates"]:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            return "No summary returned from Gemini API."
    except Exception as e:
        return f"Error calling Gemini API: {str(e)}"


def extract_content_from_url(url):
    """
    Scrapes the given URL and extracts both text and image URLs.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        for tag in soup(["script", "style"]):
            tag.decompose()

        text = " ".join(soup.stripped_strings)

        images = []
        for img in soup.find_all("img"):
            src = img.get("src")
            if src:
                absolute_url = requests.compat.urljoin(url, src)
                images.append(absolute_url)

        return text, images
    except Exception as e:
        return f"Error: {str(e)}", []


def main():
    st.title("Content Summarizer")
    st.write("Enter a URL to scrape for text and images, and to generate a summary with Gemini.")

    url = st.text_input("URL", "")

    if st.button("Analyze"):
        if url:
            with st.spinner("Extracting content..."):
                text, images = extract_content_from_url(url)

            if text.startswith("Error:"):
                st.error(text)
            else:
                with st.spinner("Generating summary with Gemini API..."):
                    summary = call_gemini_api(text, images)

                st.subheader("🧠 Summary")
                st.write(summary)

                st.subheader("🖼 Extracted Images")
                if images:
                    for image in images:
                        st.image(image, width=150)
                else:
                    st.info("No images found.")

                st.subheader("📝 Extracted Text")
                st.write(text)
        else:
            st.error("Please enter a valid URL.")


if __name__ == "__main__":
    main()
