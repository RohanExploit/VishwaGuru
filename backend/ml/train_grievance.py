import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import joblib
import os

def train_model():
    # Paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(current_dir, '../data/grievances.csv')
    model_path = os.path.join(current_dir, 'grievance_model.joblib')

    # Load Data
    print(f"Loading data from {data_path}...")
    try:
        df = pd.read_csv(data_path)
    except FileNotFoundError:
        print("Error: Dataset not found.")
        return

    # Check data
    if df.empty:
        print("Error: Dataset is empty.")
        return

    X = df['grievance_text']
    y = df['category']

    # Create Pipeline
    print("Training model...")
    text_clf = Pipeline([
        ('vect', CountVectorizer(stop_words='english')),
        ('tfidf', TfidfTransformer()),
        ('clf', MultinomialNB()),
    ])

    # Train
    text_clf.fit(X, y)

    # Save
    print(f"Saving model to {model_path}...")
    joblib.dump(text_clf, model_path)
    print("Model trained and saved successfully.")

    # Test
    test_phrases = [
        "No electricity in my house",
        "Dirty water coming from tap",
        "Someone stole my wallet"
    ]
    print("\nTest Predictions:")
    for phrase in test_phrases:
        pred = text_clf.predict([phrase])[0]
        print(f"'{phrase}' -> {pred}")

if __name__ == "__main__":
    train_model()
