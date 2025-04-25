import spacy

nlp = spacy.load("en_core_web_sm")
doc = nlp("Asha AI empowers women in tech.")
print([token.text for token in doc])
