import spacy
from nltk.corpus import stopwords

def prepare_news_for_analysis(df):
    df['text'] = df['title'].fillna('') + " " + df['content'].fillna('')
    single_column_df = df[['text']].copy()
    single_column_df['text'] = single_column_df['text'].str.lower()
    single_column_df['text'] = single_column_df['text'].str.replace(r"[^a-zA-Z\s]", "", regex=True).str.replace(r'\s+', ' ', regex=True).str.strip()
    return single_column_df[['text']]

# Load spaCy model

nlp = spacy.load("en_core_web_sm")

# Define stopwords to keep
stop_words_to_keep = {
    "not", "no", "nor", "neither", "never", "n't", "very", "too", "so", "really", "just", 
    "only", "even", "still", "always", "ever", "ain", "aren", "aren't", "couldn", "couldn't", 
    "didn", "didn't", "doesn", "doesn't", "don", "don't", "hadn", "hadn't", "hasn", "hasn't",
    "haven", "haven't", "isn", "isn't", "mightn", "mightn't", "mustn", "mustn't", "needn",
    "needn't", "shan", "shan't", "shouldn", "shouldn't", "wasn", "wasn't", "weren", "weren't",
    "won", "won't", "wouldn", "wouldn't", "more", "most", "own"
}
stop_words = set(stopwords.words('english')).difference(stop_words_to_keep)

def lemmatize(text):
    doc = nlp(text)
    allowed_pos = {"ADJ", "NOUN", "PROPN", "ADV", "VERB"}
    return ' '.join([
        token.lemma_.lower()
        for token in doc
        if token.pos_ in allowed_pos and
           not token.is_punct and
           not token.is_space and
           token.lemma_.lower() not in stop_words
    ])

def clean_and_lemmatize_df(single_column_df):
    # lowercase, strip punctuation, remove extra whitespace
    df = single_column_df.copy()
    df['text'] = df['text'].str.lower()
    df['text'] = df['text'].str.replace(r"[^a-zA-Z\s]", "", regex=True)
    df['text'] = df['text'].str.replace(r'\s+', ' ', regex=True).str.strip()

    # remove stopwords and lemmatize
    df['text'] = df['text'].apply(lemmatize)

    return df