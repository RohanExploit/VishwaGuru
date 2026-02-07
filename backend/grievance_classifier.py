import joblib
import os
import logging

logger = logging.getLogger(__name__)

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'ml/grievance_model.joblib')

class GrievanceClassifier:
    def __init__(self):
        self.model = None
        self._initialized = False

    def load_model(self):
        if os.path.exists(MODEL_PATH):
            try:
                self.model = joblib.load(MODEL_PATH)
                logger.info("Grievance model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load grievance model: {e}")
                self.model = None
        else:
            logger.warning(f"Grievance model not found at {MODEL_PATH}")

    def predict(self, text: str):
        if not self.model:
            # Try reloading if it failed previously or file was created later
            self.load_model()
            if not self.model:
                return "Unknown (Model Unavailable)"

        try:
            prediction = self.model.predict([text])[0]
            return prediction
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return "Error"

# Global instance
_classifier = None

def get_grievance_classifier():
    global _classifier
    if _classifier is None:
        _classifier = GrievanceClassifier()
    return _classifier
