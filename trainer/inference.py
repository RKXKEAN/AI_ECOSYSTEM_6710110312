import os
import logging
from typing import Optional, Dict, Any, List, Tuple
import torch
import mlflow
import mlflow.transformers
from dotenv import load_dotenv
from opentelemetry.trace import Status, StatusCode
from tracing import get_tracer

load_dotenv()

tracer = get_tracer("trainer-inference")

logger = logging.getLogger("trainer_inference")
logger.setLevel(logging.INFO)

CONLL2003_LABELS = [
    "O",
    "B-PER",
    "I-PER",
    "B-ORG",
    "I-ORG",
    "B-LOC",
    "I-LOC",
    "B-MISC",
    "I-MISC",
]

_PIPELINE_CACHE: Dict[str, Any] = {}


def _configure_mlflow_env() -> str:
    """Configure environment variables for MLflow and S3/MinIO artifact access."""
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
    mlflow.set_tracking_uri(tracking_uri)

    minio_endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
    if minio_endpoint.startswith("http://"):
        minio_endpoint = minio_endpoint[7:]
    elif minio_endpoint.startswith("https://"):
        minio_endpoint = minio_endpoint[8:]

    if "MLFLOW_S3_ENDPOINT_URL" not in os.environ:
        os.environ["MLFLOW_S3_ENDPOINT_URL"] = f"http://{minio_endpoint}"
    if "AWS_ACCESS_KEY_ID" not in os.environ:
        os.environ["AWS_ACCESS_KEY_ID"] = os.getenv("MINIO_ACCESS_KEY", "admin")
    if "AWS_SECRET_ACCESS_KEY" not in os.environ:
        os.environ["AWS_SECRET_ACCESS_KEY"] = os.getenv("MINIO_SECRET_KEY", "password123")
    if "MLFLOW_S3_IGNORE_TLS" not in os.environ:
        os.environ["MLFLOW_S3_IGNORE_TLS"] = "true"

    return tracking_uri


def resolve_model_version(
    model_name: str = "ner-conll2003",
    model_version: Optional[str] = None
) -> str:
    """
    Resolve model version:
    If model_version is explicitly provided, return it.
    Otherwise, fetch latest registered version from MLflow Model Registry.
    """
    if model_version is not None and str(model_version).strip():
        return str(model_version).strip()

    _configure_mlflow_env()
    client = mlflow.tracking.MlflowClient()

    try:
        model_info = client.get_registered_model(model_name)
        if model_info.latest_versions:
            sorted_versions = sorted(
                model_info.latest_versions,
                key=lambda v: int(v.version) if str(v.version).isdigit() else 0,
                reverse=True
            )
            latest = sorted_versions[0].version
            logger.info(f"Resolved latest model version for '{model_name}' via get_registered_model: {latest}")
            return str(latest)
    except Exception as e:
        logger.warning(f"Could not get model info via get_registered_model: {e}")

    # Fallback to search_model_versions
    versions = client.search_model_versions(f"name='{model_name}'")
    if not versions:
        raise ValueError(f"No registered model versions found for '{model_name}' in MLflow")

    sorted_versions = sorted(
        versions,
        key=lambda v: int(v.version) if str(v.version).isdigit() else 0,
        reverse=True
    )
    latest = sorted_versions[0].version
    logger.info(f"Resolved latest model version for '{model_name}' via search_model_versions: {latest}")
    return str(latest)


def get_ner_pipeline(
    model_version: Optional[str] = None,
    model_name: str = "ner-conll2003"
) -> Tuple[Any, str]:
    """
    Load or retrieve cached Hugging Face token classification pipeline from MLflow.
    Ensures model runs on GPU if available.
    """
    with tracer.start_as_current_span("get_ner_pipeline") as span:
        span.set_attribute("model_name", model_name)
        try:
            _configure_mlflow_env()
            resolved_version = resolve_model_version(model_name, model_version)
            span.set_attribute("resolved_version", resolved_version)
            cache_key = f"{model_name}:{resolved_version}"

            if cache_key in _PIPELINE_CACHE:
                logger.info(f"Using in-memory cached NER pipeline for {cache_key}")
                return _PIPELINE_CACHE[cache_key], resolved_version

            model_uri = f"models:/{model_name}/{resolved_version}"
            logger.info(f"Loading NER pipeline from MLflow: '{model_uri}'...")
            pipe = mlflow.transformers.load_model(model_uri, return_type="pipeline")

            if torch.cuda.is_available():
                pipe.model.to("cuda")
                logger.info(f"Moved model to GPU: {torch.cuda.get_device_name(0)}")
            else:
                logger.info("CUDA not available. Pipeline running on CPU.")

            _PIPELINE_CACHE[cache_key] = pipe
            return pipe, resolved_version
        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise


def predict_ner(
    input_text: str,
    model_version: Optional[str] = None,
    model_name: str = "ner-conll2003"
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Run Token Classification (NER) inference on input text.
    Returns formatted list of tokens and their predicted labels, and the resolved model version.
    """
    with tracer.start_as_current_span("predict_ner") as span:
        span.set_attribute("model_name", model_name)
        span.set_attribute("input_text_length", len(input_text) if input_text else 0)
        try:
            if not input_text or not input_text.strip():
                resolved_version = resolve_model_version(model_name, model_version)
                span.set_attribute("resolved_version", resolved_version)
                return [], resolved_version

            pipe, resolved_version = get_ner_pipeline(model_version=model_version, model_name=model_name)
            raw_predictions = pipe(input_text)

            formatted_results: List[Dict[str, Any]] = []
            for item in raw_predictions:
                raw_label = str(item.get("entity", item.get("label", "")))
                if raw_label.isdigit() and int(raw_label) < len(CONLL2003_LABELS):
                    pred_label = CONLL2003_LABELS[int(raw_label)]
                else:
                    pred_label = raw_label

                word = item.get("word", "")
                score = float(item.get("score", 0.0))
                formatted_results.append({
                    "token": word,
                    "word": word,
                    "predicted_label": pred_label,
                    "score": round(score, 4),
                    "start": item.get("start"),
                    "end": item.get("end"),
                })

            span.set_attribute("resolved_version", resolved_version)
            span.set_attribute("predictions_count", len(formatted_results))
            return formatted_results, resolved_version
        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise

