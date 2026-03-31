import os
import sys

# Define root path so imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import mlflow
from sklearn.linear_model import LogisticRegression
from sklearn.cluster import KMeans
from shared.config import settings
from shared.model_registry import model_registry

def seed_models():
    print(f"Connecting to MLflow at {settings.MLFLOW_TRACKING_URI}...")
    
    # 1. Dummy Persona Classifier
    persona_model = LogisticRegression()
    # Mock 'fit' just to make it a valid scikit-learn model object
    persona_model.fit([[0, 0], [1, 1]], [0, 1])
    
    print("Registering 'discovery.persona'...")
    model_registry.register_model(
        model=persona_model,
        engine_name="discovery.persona",
        metrics={"accuracy": 0.94, "f1_score": 0.91}
    )

    # 2. Dummy Benchmark Clusterer
    cluster_model = KMeans(n_clusters=3, n_init=10)
    cluster_model.fit([[1, 2], [1, 4], [1, 0], [10, 2], [10, 4], [10, 0]])
    
    print("Registering 'benchmark.cluster'...")
    model_registry.register_model(
        model=cluster_model,
        engine_name="benchmark.cluster",
        metrics={"silhouette_score": 0.82, "inertia": 14.5}
    )
    
    print("Seed complete! Open http://localhost:5000 to view your new models.")

if __name__ == "__main__":
    seed_models()
