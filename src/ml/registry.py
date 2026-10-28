"""Versioned model registry for managing PyTorch and scikit-learn model artifacts and metadata."""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional


@dataclass
class ModelMetadata:
    """Versioned metadata record for a trained model artifact."""
    model_name: str
    version: int
    framework: str  # pytorch, scikit-learn
    architecture: str
    created_at: str
    hyperparameters: Dict[str, Any]
    eval_metrics: Dict[str, float]
    artifact_path: str
    status: str = "active"
    latest_version: Optional[int] = None

    def __post_init__(self):
        if self.latest_version is None:
            self.latest_version = self.version

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "version": self.version,
            "latest_version": self.version,
            "framework": self.framework,
            "architecture": self.architecture,
            "created_at": self.created_at,
            "hyperparameters": self.hyperparameters,
            "eval_metrics": self.eval_metrics,
            "artifact_path": self.artifact_path,
            "status": self.status,
        }


class ModelRegistry:
    """Filesystem-backed versioned model registry."""

    def __init__(self, registry_dir: Optional[Path] = None):
        self.registry_dir = registry_dir or Path("models/registry")
        self.registry_dir.mkdir(parents=True, exist_ok=True)

    def register_model(
        self,
        model_name: str,
        framework: str,
        architecture: str,
        hyperparameters: Dict[str, Any],
        eval_metrics: Dict[str, float],
        save_fn: Any,  # Callable taking target_path: Path
    ) -> ModelMetadata:
        """Register a new model version, saving weights and metadata.json."""
        model_dir = self.registry_dir / model_name
        model_dir.mkdir(parents=True, exist_ok=True)

        # Compute next sequential version
        existing_versions = []
        for d in model_dir.iterdir():
            if d.is_dir() and d.name.startswith("v"):
                try:
                    existing_versions.append(int(d.name[1:]))
                except ValueError:
                    pass

        next_version = (max(existing_versions) + 1) if existing_versions else 1
        version_dir = model_dir / f"v{next_version}"
        version_dir.mkdir(parents=True, exist_ok=True)

        # Save model artifact file
        artifact_ext = ".pt" if framework == "pytorch" else ".joblib"
        artifact_file = version_dir / f"model{artifact_ext}"
        save_fn(artifact_file)

        meta = ModelMetadata(
            model_name=model_name,
            version=next_version,
            framework=framework,
            architecture=architecture,
            created_at=datetime.now(timezone.utc).isoformat(),
            hyperparameters=hyperparameters,
            eval_metrics=eval_metrics,
            artifact_path=str(artifact_file).replace("\\", "/"),
            status="active",
        )

        # Write metadata.json
        meta_path = version_dir / "metadata.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta.to_dict(), f, indent=2)

        return meta

    def get_latest_metadata(self, model_name: str) -> Optional[ModelMetadata]:
        """Load metadata for the highest version of a model."""
        model_dir = self.registry_dir / model_name
        if not model_dir.exists():
            return None

        versions = []
        for d in model_dir.iterdir():
            if d.is_dir() and d.name.startswith("v"):
                try:
                    versions.append(int(d.name[1:]))
                except ValueError:
                    pass

        if not versions:
            return None

        latest_v = max(versions)
        meta_file = model_dir / f"v{latest_v}" / "metadata.json"
        if not meta_file.exists():
            return None

        with open(meta_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return ModelMetadata(**data)

    def list_models(self) -> List[Dict[str, Any]]:
        """List all registered models and their latest metadata."""
        models = []
        for d in self.registry_dir.iterdir():
            if d.is_dir():
                latest = self.get_latest_metadata(d.name)
                if latest:
                    models.append(latest.to_dict())
        return models
