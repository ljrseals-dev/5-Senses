# Boy Scout: pretrained model acquisition

The model scout separates catalog discovery from weight acquisition.

- Discovery queries Hugging Face model metadata and writes a JSON inventory.
- Acquisition is a separate, explicit operation and requires a pinned revision.
- Files are downloaded outside the Git repository; weights are not committed.
- Never enable model-provided Python for routine inspection.
- Review the model card, license, intended use, tokenizer, architecture, and file formats.
  A catalog entry is not a license grant.
- Prefer compact quantized GGUF artifacts for local inference where supported;
  retain tokenizer/configuration and provenance alongside the weights.

Example: import search_models and write_model_inventory from
body_of_secrets.scouting.models, query for a model family, then write the results to
 data/inventory/models.json. For an approved candidate, inspect its immutable commit
SHA on the model host before calling acquire_model(repo_id, destination, revision=SHA).

Install the optional downloader with pip install huggingface_hub. This tool does not
certify model safety, quality, or license compatibility.
