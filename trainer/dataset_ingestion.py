import os
import argparse
import tempfile
import shutil
import logging
from datasets import load_dataset
from minio import Minio
from minio.error import S3Error
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Load env variables from local environment
load_dotenv()

# Fallback: check if backend/.env contains MinIO variables
if not os.getenv("MINIO_ENDPOINT"):
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    backend_env = os.path.join(parent_dir, "backend", ".env")
    if os.path.exists(backend_env):
        logger.info(f"Loading environment variables from {backend_env}")
        load_dotenv(backend_env)

# MinIO Config
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "admin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "password123")
MINIO_SECURE_STR = os.getenv("MINIO_SECURE", "false")
MINIO_SECURE = MINIO_SECURE_STR.lower() in ("true", "1", "yes")

# Clean endpoint scheme if present
if MINIO_ENDPOINT.startswith("http://"):
    MINIO_ENDPOINT = MINIO_ENDPOINT[7:]
elif MINIO_ENDPOINT.startswith("https://"):
    MINIO_ENDPOINT = MINIO_ENDPOINT[8:]


def get_minio_client() -> Minio:
    """Initialize MinIO client based on configuration."""
    return Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=MINIO_SECURE,
    )


def ingest_dataset(dataset_name: str):
    """
    Downloads a Hugging Face dataset, saves it to disk, compresses it,
    and uploads the zip file to MinIO. Then cleans up local temporary files.
    """
    logger.info(f"Starting ingestion for dataset: '{dataset_name}'")
    
    # Map deprecated dataset script names to parquet-based alternatives if needed
    hf_dataset_name = dataset_name
    if dataset_name == "conll2003":
        hf_dataset_name = "lhoestq/conll2003"
        logger.info(f"Mapping 'conll2003' to parquet-based alternative: '{hf_dataset_name}'")

    # 1. Download Dataset from Hugging Face
    try:
        dataset = load_dataset(hf_dataset_name)
        logger.info(f"Successfully loaded dataset '{hf_dataset_name}' from Hugging Face.")
    except Exception as e:
        logger.error(f"Failed to load dataset '{dataset_name}' from Hugging Face: {e}")
        return

    # Count splits and rows for summary
    split_summaries = {}
    if hasattr(dataset, "keys"):
        for split in dataset.keys():
            split_summaries[split] = len(dataset[split])
    else:
        split_summaries["default"] = len(dataset)

    # 2. Save Dataset to disk and Compress to .zip
    temp_dir = tempfile.mkdtemp()
    dataset_dir = os.path.join(temp_dir, dataset_name)
    zip_base_path = os.path.join(temp_dir, dataset_name)
    zip_filepath = None

    try:
        logger.info(f"Saving dataset '{dataset_name}' to disk at: {dataset_dir}")
        dataset.save_to_disk(dataset_dir)

        logger.info("Compressing dataset folder to a single .zip archive...")
        # shutil.make_archive returns the path to the created archive (with .zip extension)
        zip_filepath = shutil.make_archive(zip_base_path, "zip", dataset_dir)
        file_size_bytes = os.path.getsize(zip_filepath)
        file_size_mb = file_size_bytes / (1024 * 1024)
        logger.info(f"Successfully created zip archive: {zip_filepath} ({file_size_mb:.2f} MB)")

        # 3. Connect to MinIO and ensure bucket exists
        logger.info(f"Connecting to MinIO at {MINIO_ENDPOINT} (Secure: {MINIO_SECURE})")
        client = get_minio_client()
        bucket_name = "datasets"

        try:
            if not client.bucket_exists(bucket_name):
                client.make_bucket(bucket_name)
                logger.info(f"Created bucket '{bucket_name}' in MinIO.")
            else:
                logger.info(f"Bucket '{bucket_name}' already exists in MinIO.")
        except S3Error as e:
            logger.error(f"MinIO S3 error checking/creating bucket: {e}")
            raise e

        # 4. Upload ZIP file to MinIO
        object_name = f"datasets/{dataset_name}/{dataset_name}.zip"
        logger.info(f"Uploading archive to MinIO object: '{object_name}' in bucket '{bucket_name}'")
        client.fput_object(
            bucket_name=bucket_name,
            object_name=object_name,
            file_path=zip_filepath
        )
        logger.info("Upload completed successfully.")

        # 5. Print final summary
        print("\n" + "=" * 50)
        print(" DATASET INGESTION SUMMARY")
        print("=" * 50)
        print(f"Dataset Name:  {dataset_name}")
        print("Split Rows:")
        for split, count in split_summaries.items():
            print(f"  - {split}: {count:,} rows")
        print(f"Object Key:    {object_name}")
        print(f"Bucket Name:   {bucket_name}")
        print(f"Archive Size:  {file_size_mb:.2f} MB ({file_size_bytes:,} bytes)")
        print("=" * 50 + "\n")

    except Exception as e:
        logger.error(f"An error occurred during the ingestion process: {e}")
    finally:
        # 6. Cleanup temporary directory and local zip file
        logger.info("Cleaning up temporary local files...")
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            logger.info("Temporary directory and local zip file deleted from local disk.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest datasets from Hugging Face and upload them to MinIO as zip archives.")
    parser.argument_default = argparse.SUPPRESS
    parser.add_argument(
        "--dataset",
        type=str,
        default="conll2003",
        help="Name of the Hugging Face dataset to ingest (default: conll2003)"
    )
    args = parser.parse_args()
    ingest_dataset(args.dataset)


# ==============================================================================
# Rationale for Saving and Compressing to ZIP before Uploading to MinIO:
# ==============================================================================
# 1. Reduces Object Count: Hugging Face datasets are saved on disk as split folders
#    containing multiple metadata files, arrow table files, and indexes. Uploading
#    these individually would result in dozens of objects per dataset. Compressing 
#    them to a single .zip file reduces the object count to 1 per dataset.
# 2. Simplifies Downstream Downloads: In the Trainer Worker stage, we only need to 
#    perform a single GET request to download the entire dataset archive instead of 
#    listing and downloading multiple files, saving latency and code complexity.
# 3. Ensures Atomic Ingestion: Downloading and extracting a single zip file is atomic;
#    either the entire dataset is successfully retrieved, or it fails, avoiding 
#    scenarios where a trainer worker tries to run with partially downloaded files.
# ==============================================================================
