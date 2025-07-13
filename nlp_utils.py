import spacy

# Load the small English model
nlp = spacy.load("en_core_web_sm")

def extract_order_items(text):
    doc = nlp(text)
    items = []

    for token in doc:
        if token.pos_ == "NUM":
            quantity = token.text
            product = token.nbor(2).text if token.i + 2 < len(doc) else ""
            items.append({
                "product": product,
                "quantity": quantity
            })
    
    return items
