import fitz  # PyMuPDF
import re
from docx import Document

# Common English stop words
stop_words = set([
    "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", "yourself", "yourselves",
    "he", "him", "his", "himself", "she", "her", "hers", "herself", "it", "its", "itself", "they", "them", "their",
    "theirs", "themselves", "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are",
    "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an",
    "the", "and", "but", "if", "or", "because", "as", "until", "while", "of", "at", "by", "for", "with", "about",
    "against", "between", "into", "through", "during", "before", "after", "above", "below", "to", "from", "up",
    "down", "in", "out", "on", "off", "over", "under", "again", "further", "then", "once", "here", "there", "when",
    "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "no",
    "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", "can", "will", "just", "don",
    "should", "now"
])

def extract_text_from_pdf(file_stream):
    """Extract text from PDF file stream"""
    text = ""
    pdf = fitz.open(stream=file_stream.read(), filetype="pdf")
    for page in pdf:
        text += page.get_text()
    return text

def extract_text_from_docx(file_stream):
    """Extract text from DOCX file stream"""
    import io
    doc = Document(io.BytesIO(file_stream.read()))
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

def extract_text_from_file(file):
    """Unified file text extraction for PDF and DOCX"""
    filename = file.filename.lower()
    if filename.endswith('.pdf'):
        return extract_text_from_pdf(file)
    elif filename.endswith('.docx'):
        return extract_text_from_docx(file)
    return ""

def preprocess(text):
    """Clean and normalize text for AI matching"""
    text = text.lower()

    # 🔥 Fix: Use word boundaries to prevent corrupting words (e.g., 'detail' -> 'detartificial intelligence l')
    replacements = {
        r"\bml\b": "machine learning",
        r"\bai\b": "artificial intelligence",
        r"\bnlp\b": "natural language processing"
    }
    
    for pattern, replacement in replacements.items():
        text = re.sub(pattern, replacement, text)

    # Remove special characters except alphanumeric and spaces
    text = re.sub(r"[^a-zA-Z ]", " ", text)
    
    # Remove extra spaces
    text = re.sub(r"\s+", " ", text).strip()

    return text