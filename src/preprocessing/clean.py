"""
Text cleaning pipeline for news articles.

Operations:
- Lowercase
- URL removal
- Number removal
- Punctuation removal
- Whitespace normalization
- Stopword removal
- Empty text removal
"""

import re
import string
from typing import List

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Ensure NLTK resources are downloaded
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)
nltk.download('stopwords', quiet=True)

STOPWORDS = set(stopwords.words('english'))


def clean_text(text: str) -> str:
    """Clean a single text string."""
    if not isinstance(text, str):
        return ""

    # Lowercase
    text = text.lower()

    # URL removal
    text = re.sub(r'https?://\S+|www\.\S+', '', text)

    # Number removal
    text = re.sub(r'\d+', '', text)

    # Punctuation removal
    text = text.translate(str.maketrans('', '', string.punctuation))

    # Whitespace normalization
    text = re.sub(r'\s+', ' ', text).strip()

    # Stopword removal
    tokens = word_tokenize(text)
    tokens = [word for word in tokens if word not in STOPWORDS]
    text = ' '.join(tokens)

    return text if text else ""


def clean_texts(texts: List[str]) -> List[str]:
    """Clean a list of text strings."""
    return [clean_text(text) for text in texts]