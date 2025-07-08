import joblib
import os

# Load production artifacts
model_dir = "model"
model = joblib.load(os.path.join(model_dir, "model.pkl"))
vectorizer = joblib.load(os.path.join(model_dir, "vectorizer.pkl"))
label_encoder = joblib.load(os.path.join(model_dir, "label_encoder.pkl"))

def predict_sentiment(df):
    X_vec = vectorizer.transform(df["text"])
    preds = model.predict(X_vec)
    probs = model.predict_proba(X_vec).max(axis=1)  

    labels = label_encoder.inverse_transform(preds)

    return labels, probs
