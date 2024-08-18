from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from openai import OpenAI
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import streamlit as st
import pandas as pd


class BrowserHandler:
    def __init__(self, url: str):
        self.url = url

    def fetch_page_content(self) -> str:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(self.url)
            content = page.content()
            browser.close()
            return content


class HTMLParser:
    def __init__(self, content: str):
        self.soup = BeautifulSoup(content, "html.parser")

    def extract_text_by_tags(self, tags: List[str]) -> Dict[str, List[str]]:
        content_dict = {}
        for tag in tags:
            elements = self.soup.find_all(tag)
            if elements:
                content_dict[tag] = [
                    element.get_text(strip=True) for element in elements
                ]
        return content_dict

    def extract_text(self) -> str:
        return self.soup.get_text(strip=True)

    def extract_links(self) -> List[Dict[str, str]]:
        links = []
        for link in self.soup.find_all("a"):
            link_text = link.get_text(strip=True)
            link_href = link.get("href")
            links.append({"text": link_text, "href": link_href})
        return links

    def extract_images(self) -> List[Dict[str, str]]:
        images = []
        for img in self.soup.find_all("img"):
            src = img.get("src")
            alt = img.get("alt")
            images.append({"src": src, "alt": alt})
        return images

    def extract_tables(self) -> List[pd.DataFrame]:
        try:
            return pd.read_html(str(self.soup))
        except:
            return []

    def extract_meta_tags(self) -> Dict[str, str]:
        return {
            meta.get("name"): meta.get("content") for meta in self.soup.find_all("meta")
        }

    def extract_title(self) -> str:
        return self.soup.title.string


class StructuredDataExtractor:
    def __init__(self):
        self.client = OpenAI()

    def extract_data(self, content: str, model: BaseModel) -> BaseModel | str:
        completion = self.client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert at structured data extraction. You will be given unstructured text and should convert it into the given structure.",
                },
                {"role": "user", "content": content},
            ],
            response_format=model,
        )

        message = completion.choices[0].message
        if message.refusal:
            return message.refusal
        else:
            return message.parsed


class StructuredData(BaseModel):
    CompanyName: Optional[str] = Field(description="Name of the company")
    Services: Optional[List[str]] = Field(description="List of services offered")
    Contact: Optional[List[str]] = Field(
        description="Contact information of the company"
    )
    Confident: Optional[int] = Field(
        description="Confidence level of the extracted data (0-100)"
    )


psp_dict = {
    "PayPal": "https://www.paypal.com/c2/webapps/mpp/home?locale.x=zh_C2",
    "Stripe": "https://stripe.com/zh-us",
    "Payoneer": "https://www.payoneer.com/zh-hant/",
}


def main():
    st.title("Payment Service Providers Scraper")
    option = st.selectbox(
        "What PSP would you like to scrape?", ("PayPal", "Stripe", "Payoneer")
    )

    url = psp_dict[option]
    st.write("You selected:", option)
    st.write("with URL:", psp_dict[option])

    # Fetch page content
    st.write("Fetching page content...")
    browser_handler = BrowserHandler(url)
    page_content = browser_handler.fetch_page_content()

    # Parse HTML content
    st.write("Parsing HTML content...")
    html_parser = HTMLParser(page_content)
    extracted_content = html_parser.extract_text()
    extracted_links = html_parser.extract_links()
    extracted_imgs = html_parser.extract_images()
    extracted_tables = html_parser.extract_tables()

    st.write("Extracted text:")
    st.write(extracted_content[:1000])

    st.write("Extracted links:")
    st.write(extracted_links)

    st.write("Extracted images:")
    st.write(extracted_imgs)
    for img in extracted_imgs[:3]:
        st.image(img["src"], caption=img["alt"])

    st.write("Extracted tables:")
    for table in extracted_tables:
        st.dataframe(table, use_container_width=True)

    # Extract structured data
    st.write("Extracting structured data using LLM...")
    st.write("Structured data schema:")
    st.json(StructuredData.model_json_schema())

    input_content = extracted_content + "\n" + str(extracted_links)
    extractor = StructuredDataExtractor()
    structured_content: StructuredData = extractor.extract_data(
        input_content, StructuredData
    )

    # Output the structured content
    st.json(structured_content.model_dump_json())

    st.write("Done")


main()
