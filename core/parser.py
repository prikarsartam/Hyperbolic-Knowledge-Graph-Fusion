import os
import requests
import xml.etree.ElementTree as ET
import logging

logger = logging.getLogger("Parser")

GROBID_URL = "http://localhost:8070/api/processFulltextDocument"

def parse_pdf_to_text(pdf_path: str) -> str:
    """Sends a PDF to a local GROBID server and extracts text/formulas."""
    logger.info(f"Sending {pdf_path} to GROBID at {GROBID_URL}")
    with open(pdf_path, 'rb') as f:
        files = {'input': (os.path.basename(pdf_path), f, 'application/pdf')}
        data = {'consolidateHeader': '0'}
        response = requests.post(GROBID_URL, files=files, data=data)

    if response.status_code != 200:
        raise RuntimeError(f"GROBID parsing failed: {response.status_code} - {response.text}")

    return _parse_tei_xml(response.text)

def _parse_tei_xml(xml_content: str) -> str:
    """Converts GROBID TEI XML to a flat Markdown string retaining LaTeX formulas."""
    root = ET.fromstring(xml_content)
    ns = {'tei': 'http://www.tei-c.org/ns/1.0'}
    
    markdown = []
    
    # Extract Abstract
    abstract = root.find('.//tei:profileDesc/tei:abstract', ns)
    if abstract is not None:
        markdown.append("## Abstract\n")
        _extract_text_and_formulas(abstract, ns, markdown)
        
    # Extract Body
    body = root.find('.//tei:body', ns)
    if body is not None:
        for div in body.findall('tei:div', ns):
            head = div.find('tei:head', ns)
            if head is not None and head.text:
                markdown.append(f"\n## {head.text}\n")
            _extract_text_and_formulas(div, ns, markdown)

    return "\n".join(markdown)

def _extract_text_and_formulas(element, ns, output_list):
    for p in element.findall('tei:p', ns):
        paragraph_text = ""
        # iterate over text and elements inside p
        for child in p.iter():
            if child.tag.endswith('formula'):
                eq_text = child.text if child.text else ""
                paragraph_text += f" $${eq_text.strip()}$$ "
            elif child.text and not child.tag.endswith('formula'):
                paragraph_text += child.text
            if child.tail:
                paragraph_text += child.tail
        
        # Clean up multiple spaces
        cleaned = " ".join(paragraph_text.split())
        output_list.append(cleaned)
