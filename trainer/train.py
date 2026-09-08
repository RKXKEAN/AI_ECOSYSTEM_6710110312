import os
import sys
import shutil
import zipfile
import tempfile
import inspect
import logging
from typing import Dict, Any, Optional, Tuple

import numpy as np
import torch
import datasets
from datasets import load_from_disk
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    DataCollatorForTokenClassification,
    TrainingArguments,
    Trainer,
    TrainerCallback,
)
from seqeval.metrics import f1_score, precision_score, recall_score, accuracy_score
from minio import Minio
from minio.error import S3Error
from dotenv import load_dotenv
import mlflow
import mlflow.transformers
import types

# Ensure torchvision module check in MLflow does not fail if uninstalled
if "torchvision" not in sys.modules:
    try:
        import torchvision
    except ImportError:
        dummy_tv = types.ModuleType("torchvision")
        dummy_tv.__version__ = "0.20.0"
        dummy_tv.__spec__ = types.SimpleNamespace(origin="torchvision")
        sys.modules["torchvision"] = dummy_tv

load_dotenv()

# MinIO Config
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "password123")
MINIO_SECURE_STR = os.getenv("MINIO_SECURE", "false")
MINIO_SECURE = MINIO_SECURE_STR.lower() in ("true", "1", "yes")

# Clean endpoint scheme if present
if MINIO_ENDPOINT.startswith("http://"):
    MINIO_ENDPOINT = MINIO_ENDPOINT[7:]
elif MINIO_ENDPOINT.startswith("https://"):
    MINIO_ENDPOINT = MINIO_ENDPOINT[8:]

# Configure AWS / S3 environment variables for MLflow boto3 artifact storage
if "MLFLOW_S3_ENDPOINT_URL" not in os.environ:
    os.environ["MLFLOW_S3_ENDPOINT_URL"] = f"http://{MINIO_ENDPOINT}"
if "AWS_ACCESS_KEY_ID" not in os.environ:
    os.environ["AWS_ACCESS_KEY_ID"] = MINIO_ACCESS_KEY
if "AWS_SECRET_ACCESS_KEY" not in os.environ:
    os.environ["AWS_SECRET_ACCESS_KEY"] = MINIO_SECRET_KEY
if "MLFLOW_S3_IGNORE_TLS" not in os.environ:
    os.environ["MLFLOW_S3_IGNORE_TLS"] = "true"


def get_minio_client() -> Minio:
    """Initialize MinIO client based on environment variables."""
    return Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_SECURE,
    )


def setup_logger(job_id: str) -> logging.Logger:
    """
    Set up a logger that logs to both stdout and a file /app/logs/{job_id}.log.
    """
    logs_dir = os.getenv("LOGS_DIR", "/app/logs")
    os.makedirs(logs_dir, exist_ok=True)

    logger_name = f"trainer_{job_id}"
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Clear existing handlers to prevent duplicate lines
    while logger.handlers:
        logger.handlers.pop()

    formatter = logging.Formatter(
        fmt="%(asctime)s - [%(levelname)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console output handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File output handler
    log_file_path = os.path.join(logs_dir, f"{job_id}.log")
    file_handler = logging.FileHandler(log_file_path, mode="a", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def download_dataset_from_minio(dataset_name: str) -> str:
    """
    Download datasets/{dataset_name}/{dataset_name}.zip from MinIO,
    extract it into a temporary directory, and return the path for load_from_disk().
    """
    client = get_minio_client()
    bucket_name = "datasets"
    object_name = f"datasets/{dataset_name}/{dataset_name}.zip"

    if not client.bucket_exists(bucket_name):
        raise ValueError(f"MinIO bucket '{bucket_name}' does not exist.")

    temp_dir = tempfile.mkdtemp(prefix=f"dataset_{dataset_name}_")
    zip_path = os.path.join(temp_dir, f"{dataset_name}.zip")
    extracted_dir = os.path.join(temp_dir, "extracted")
    os.makedirs(extracted_dir, exist_ok=True)

    try:
        client.fget_object(bucket_name, object_name, zip_path)
    except S3Error as e:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise RuntimeError(f"Failed to download object '{object_name}' from bucket '{bucket_name}': {e}")

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extracted_dir)

    if os.path.exists(zip_path):
        os.remove(zip_path)

    # Check if dataset_dict.json is at extracted root or nested
    if not os.path.exists(os.path.join(extracted_dir, "dataset_dict.json")):
        nested_dir = os.path.join(extracted_dir, dataset_name)
        if os.path.exists(os.path.join(nested_dir, "dataset_dict.json")):
            return nested_dir

    return extracted_dir


class CustomLoggingCallback(TrainerCallback):
    """
    Callback that logs training steps and evaluation metrics directly to the job logger.
    """
    def __init__(self, target_logger: logging.Logger):
        self.target_logger = target_logger

    def on_train_begin(self, args, state, control, **kwargs):
        self.target_logger.info(
            f"Training initiated: {args.num_train_epochs} epochs | Total planned steps: {state.max_steps}"
        )

    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs:
            step = state.global_step
            max_steps = state.max_steps
            pct = (step / max_steps * 100) if max_steps and max_steps > 0 else 0.0
            epoch = logs.get("epoch", state.epoch)
            loss = logs.get("loss")
            eval_loss = logs.get("eval_loss")
            eval_f1 = logs.get("eval_f1")
            lr = logs.get("learning_rate")

            log_items = [f"Step {step}/{max_steps} ({pct:.1f}%)"]
            if epoch is not None:
                log_items.append(f"Epoch {epoch:.2f}")
            if loss is not None:
                log_items.append(f"Train Loss: {loss:.4f}")
            if eval_loss is not None:
                log_items.append(f"Eval Loss: {eval_loss:.4f}")
            if eval_f1 is not None:
                log_items.append(f"Eval F1: {eval_f1:.4f}")
            if lr is not None:
                log_items.append(f"LR: {lr:.2e}")

            self.target_logger.info(" | ".join(log_items))

    def on_epoch_end(self, args, state, control, **kwargs):
        epoch_num = int(round(state.epoch)) if state.epoch is not None else 0
        self.target_logger.info(f"Finished Epoch {epoch_num}/{int(args.num_train_epochs)}")

    def on_train_end(self, args, state, control, **kwargs):
        self.target_logger.info("Training process completed.")


def train_ner_model(
    dataset_path: str,
    hyperparameters: Dict[str, Any],
    logger: logging.Logger,
    job_id: Optional[str] = None,
    dataset_name: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Fine-tunes a Token Classification model (distilbert-base-uncased) on the provided dataset
    following Hugging Face Course Chapter 7.2.
    Tracks parameters, metrics, and models using MLflow.
    Returns a tuple of (saved_model_dir, mlflow_run_id).
    """
    tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
    mlflow.set_tracking_uri(tracking_uri)
    logger.info(f"Configured MLflow Tracking URI: {tracking_uri}")

    experiment_name = "token-classification-ner"
    mlflow.set_experiment(experiment_name)
    logger.info(f"Configured MLflow Experiment: '{experiment_name}'")

    if not dataset_name:
        dataset_name = hyperparameters.get("dataset_name", "conll2003")

    run_name = f"job_{job_id}" if job_id else f"ner_{dataset_name}"

    with mlflow.start_run(run_name=run_name) as run:
        run_id = run.info.run_id
        logger.info(f"MLflow Run started: ID={run_id}, Name='{run_name}'")

        if job_id:
            mlflow.set_tag("job_id", str(job_id))
        mlflow.set_tag("dataset_name", dataset_name)
        if torch.cuda.is_available():
            mlflow.set_tag("hardware", torch.cuda.get_device_name(0))

        logger.info(f"Loading dataset from: {dataset_path}")
        raw_datasets = load_from_disk(dataset_path)
        logger.info(f"Dataset loaded. Available splits: {list(raw_datasets.keys())}")

        if "train" not in raw_datasets:
            raise ValueError(f"Dataset missing required 'train' split. Available: {list(raw_datasets.keys())}")

        # Inspect features and extract NER label names
        train_features = raw_datasets["train"].features
        tag_col = "ner_tags" if "ner_tags" in train_features else "tags"
        if tag_col not in train_features:
            raise ValueError(f"Could not find NER tag column in dataset features: {list(train_features.keys())}")

        feature = train_features[tag_col]
        if hasattr(feature, "feature") and hasattr(feature.feature, "names"):
            label_names = feature.feature.names
        elif hasattr(feature, "names"):
            label_names = feature.names
        else:
            unique_tags = set()
            for tags in raw_datasets["train"][tag_col]:
                unique_tags.update(tags)
            label_names = [str(t) for t in sorted(unique_tags)]

        num_labels = len(label_names)
        id2label = {i: label for i, label in enumerate(label_names)}
        label2id = {label: i for i, label in enumerate(label_names)}
        logger.info(f"Dataset has {num_labels} labels: {label_names}")

        # Base model & Tokenizer
        model_name = hyperparameters.get("model_name")
        if not model_name or model_name == "default":
            model_name = "distilbert-base-uncased"
        logger.info(f"Loading base model and tokenizer: '{model_name}'")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForTokenClassification.from_pretrained(
            model_name,
            num_labels=num_labels,
            id2label=id2label,
            label2id=label2id,
        )

        # Tokenize and align labels (Hugging Face Course Chapter 7.2)
        def tokenize_and_align_labels(examples):
            tokenized_inputs = tokenizer(
                examples["tokens"],
                truncation=True,
                is_split_into_words=True,
                max_length=512,
            )
            all_labels = examples[tag_col]
            new_labels = []
            for i, labels in enumerate(all_labels):
                word_ids = tokenized_inputs.word_ids(batch_index=i)
                previous_word_idx = None
                label_ids = []
                for word_idx in word_ids:
                    if word_idx is None:
                        label_ids.append(-100)
                    elif word_idx != previous_word_idx:
                        label_ids.append(labels[word_idx])
                    else:
                        label_ids.append(-100)
                    previous_word_idx = word_idx
                new_labels.append(label_ids)
            tokenized_inputs["labels"] = new_labels
            return tokenized_inputs

        logger.info("Aligning tokens and labels across dataset splits...")
        tokenized_datasets = raw_datasets.map(
            tokenize_and_align_labels,
            batched=True,
            remove_columns=raw_datasets["train"].column_names,
        )

        # Check GPU / CUDA availability
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
            cuda_ver = torch.version.cuda
            logger.info(f"GPU Hardware Detected: {gpu_name} ({vram_gb:.2f} GB VRAM, CUDA {cuda_ver}). Training on GPU.")
        else:
            logger.warning("CUDA is NOT available. Falling back to CPU training (performance will be significantly slower).")

        # Hyperparameters setup
        epochs = int(hyperparameters.get("epochs") or 3)
        batch_size = int(hyperparameters.get("batch_size") or 8)
        learning_rate = float(hyperparameters.get("learning_rate") or 2e-5)
        weight_decay = float(hyperparameters.get("weight_decay") or 0.01)
        logging_steps = int(hyperparameters.get("logging_steps") or 20)

        # Log Hyperparameters to MLflow
        mlflow.log_params({
            "epochs": epochs,
            "batch_size": batch_size,
            "learning_rate": learning_rate,
            "weight_decay": weight_decay,
            "logging_steps": logging_steps,
            "base_model_name": model_name,
            "dataset_name": dataset_name,
        })
        logger.info("Logged hyperparameters to MLflow")

        output_dir = tempfile.mkdtemp(prefix="trainer_tmp_")
        save_model_dir = tempfile.mkdtemp(prefix="saved_ner_model_")
        eval_split = "validation" if "validation" in tokenized_datasets else ("test" if "test" in tokenized_datasets else None)

        # Prepare TrainingArguments
        training_kwargs: Dict[str, Any] = {
            "output_dir": output_dir,
            "num_train_epochs": epochs,
            "per_device_train_batch_size": batch_size,
            "per_device_eval_batch_size": batch_size,
            "learning_rate": learning_rate,
            "weight_decay": weight_decay,
            "logging_steps": logging_steps,
            "save_strategy": "epoch" if eval_split else "no",
            "save_total_limit": 1,
            "load_best_model_at_end": True if eval_split else False,
            "metric_for_best_model": "f1" if eval_split else None,
            "greater_is_better": True,
            "report_to": ["mlflow"],
            "fp16": torch.cuda.is_available(),
            "logging_first_step": True,
        }

        # Compatibility check for transformers eval_strategy vs evaluation_strategy
        sig = inspect.signature(TrainingArguments.__init__)
        if "eval_strategy" in sig.parameters:
            training_kwargs["eval_strategy"] = "epoch" if eval_split else "no"
        else:
            training_kwargs["evaluation_strategy"] = "epoch" if eval_split else "no"

        training_args = TrainingArguments(**training_kwargs)
        data_collator = DataCollatorForTokenClassification(tokenizer=tokenizer)

        # Compute metrics with seqeval
        def compute_metrics(eval_preds):
            logits, labels = eval_preds
            predictions = np.argmax(logits, axis=-1)

            true_predictions = [
                [label_names[p] for (p, l) in zip(prediction, label) if l != -100]
                for prediction, label in zip(predictions, labels)
            ]
            true_labels = [
                [label_names[l] for (p, l) in zip(prediction, label) if l != -100]
                for prediction, label in zip(predictions, labels)
            ]

            return {
                "precision": precision_score(true_labels, true_predictions, zero_division=0),
                "recall": recall_score(true_labels, true_predictions, zero_division=0),
                "f1": f1_score(true_labels, true_predictions, zero_division=0),
                "accuracy": accuracy_score(true_labels, true_predictions),
            }

        trainer_kwargs = {
            "model": model,
            "args": training_args,
            "train_dataset": tokenized_datasets["train"],
            "eval_dataset": tokenized_datasets[eval_split] if eval_split else None,
            "data_collator": data_collator,
            "compute_metrics": compute_metrics if eval_split else None,
            "callbacks": [CustomLoggingCallback(logger)],
        }
        sig_trainer = inspect.signature(Trainer.__init__)
        if "processing_class" in sig_trainer.parameters:
            trainer_kwargs["processing_class"] = tokenizer
        elif "tokenizer" in sig_trainer.parameters:
            trainer_kwargs["tokenizer"] = tokenizer

        trainer = Trainer(**trainer_kwargs)

        logger.info(f"Starting Trainer.train() (Epochs: {epochs}, Batch Size: {batch_size}, LR: {learning_rate})...")
        train_result = trainer.train()
        logger.info(f"Training summary metrics: {train_result.metrics}")

        if eval_split:
            logger.info("Evaluating on evaluation split...")
            eval_results = trainer.evaluate()
            logger.info(f"Final Evaluation results: {eval_results}")

            # Log final Evaluation Metrics to MLflow
            final_metrics = {}
            if "eval_f1" in eval_results:
                final_metrics["F1"] = float(eval_results["eval_f1"])
                final_metrics["eval_f1"] = float(eval_results["eval_f1"])
            if "eval_precision" in eval_results:
                final_metrics["Precision"] = float(eval_results["eval_precision"])
                final_metrics["eval_precision"] = float(eval_results["eval_precision"])
            if "eval_recall" in eval_results:
                final_metrics["Recall"] = float(eval_results["eval_recall"])
                final_metrics["eval_recall"] = float(eval_results["eval_recall"])
            if "eval_accuracy" in eval_results:
                final_metrics["Accuracy"] = float(eval_results["eval_accuracy"])
                final_metrics["eval_accuracy"] = float(eval_results["eval_accuracy"])
            if "eval_loss" in eval_results:
                final_metrics["Eval_Loss"] = float(eval_results["eval_loss"])
                final_metrics["eval_loss"] = float(eval_results["eval_loss"])

            if final_metrics:
                mlflow.log_metrics(final_metrics)
                logger.info(f"Logged final evaluation metrics to MLflow: {final_metrics}")

        logger.info(f"Saving fine-tuned model and tokenizer to: {save_model_dir}")
        trainer.save_model(save_model_dir)
        tokenizer.save_pretrained(save_model_dir)

        # Log and register model in MLflow Model Registry
        registered_model_name = f"ner-{dataset_name}"
        logger.info(f"Logging model artifact to MLflow and registering in Model Registry as '{registered_model_name}'...")
        components = {
            "model": trainer.model,
            "tokenizer": tokenizer,
        }
        mlflow.transformers.log_model(
            transformers_model=components,
            artifact_path="model",
            registered_model_name=registered_model_name,
            task="token-classification",
            pip_requirements=["transformers", "torch", "accelerate"],
        )
        logger.info(f"Model successfully logged and registered in MLflow Model Registry as '{registered_model_name}'")

        # Clean up intermediate checkpoint directory
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir, ignore_errors=True)

        return save_model_dir, run_id


def upload_model_to_minio(model_dir: str, job_id: str, dataset_name: str) -> str:
    """
    Compresses model_dir into a zip archive and uploads it along with the training log to MinIO.
    Target object: models/{dataset_name}/{job_id}/model.zip
    Log object: models/{dataset_name}/{job_id}/training.log
    Cleans up local temporary model directory and zip file after upload.
    """
    client = get_minio_client()
    bucket_name = "models"

    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)

    temp_zip_dir = tempfile.mkdtemp(prefix="model_zip_")
    zip_base = os.path.join(temp_zip_dir, "model")
    zip_file = shutil.make_archive(zip_base, "zip", model_dir)

    model_object_name = f"models/{dataset_name}/{job_id}/model.zip"
    client.fput_object(bucket_name, model_object_name, zip_file)

    # Upload training log if present
    logs_dir = os.getenv("LOGS_DIR", "/app/logs")
    log_file_path = os.path.join(logs_dir, f"{job_id}.log")
    if os.path.exists(log_file_path):
        log_object_name = f"models/{dataset_name}/{job_id}/training.log"
        client.fput_object(bucket_name, log_object_name, log_file_path)

    # Cleanup local model files
    if os.path.exists(model_dir):
        shutil.rmtree(model_dir, ignore_errors=True)
    if os.path.exists(temp_zip_dir):
        shutil.rmtree(temp_zip_dir, ignore_errors=True)

    return model_object_name
