
import argparse
import time
from pathlib import Path

import requests
import torch
from tqdm.auto import tqdm

from shap_e.diffusion.sample import sample_latents
from shap_e.diffusion.gaussian_diffusion import diffusion_from_config
from shap_e.models.download import load_model, load_config
from shap_e.util.notebooks import decode_latent_mesh

CACHE_DIR = Path(__file__).parents[2] / "shap_e_model_cache"

MODEL_URLS = {
    "transmitter.pt":  "https://openaipublic.azureedge.net/main/shap-e/transmitter.pt",
    "text_cond.pt":    "https://openaipublic.azureedge.net/main/shap-e/text_cond.pt",
}


def download_with_resume(url: str, dest: Path, chunk: int = 1 << 20) -> None:
    """Download url → dest, resuming an interrupted .tmp file if present."""
    tmp = Path(str(dest) + ".tmp")
    existing = tmp.stat().st_size if tmp.exists() else 0
    headers = {"Range": f"bytes={existing}-"} if existing else {}
    r = requests.get(url, headers=headers, stream=True, timeout=60)
    if r.status_code == 416:          # range satisfied — file already complete
        tmp.rename(dest)
        return
    r.raise_for_status()
    total = existing + int(r.headers.get("content-length", 0))
    mode = "ab" if existing else "wb"
    print(f"  {'Resuming' if existing else 'Downloading'} {dest.name}"
          f" ({existing / 1024**2:.0f} / {total / 1024**2:.0f} MB)")
    with open(tmp, mode) as fh, tqdm(total=total, initial=existing,
                                     unit="iB", unit_scale=True) as bar:
        for data in r.iter_content(chunk):
            fh.write(data)
            bar.update(len(data))
    tmp.rename(dest)


def ensure_models(cache_dir: Path) -> None:
    """Pre-fetch model weights with resume support before Shap-E tries to load them."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    for filename, url in MODEL_URLS.items():
        dest = cache_dir / filename
        if not dest.exists():
            download_with_resume(url, dest)


def generate(prompt: str):
    if not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    output_dir = Path(__file__).parent / "outputs" / "samples"
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_dir = str(CACHE_DIR)

    print(f"Device: {device}")
    print(f"Prompt: {prompt}")

    start = time.time()

    try:
        print("Ensuring model weights are present...")
        ensure_models(CACHE_DIR)

        print("Loading Shap-E models...")
        xm = load_model("transmitter", device=device, cache_dir=cache_dir)
        model = load_model("text300M", device=device, cache_dir=cache_dir)
        diffusion = diffusion_from_config(load_config("diffusion", cache_dir=cache_dir))

        print("Generating 3D latent...")

        with torch.no_grad():
            latents = sample_latents(
                batch_size=1,
                model=model,
                diffusion=diffusion,
                guidance_scale=15.0,
                model_kwargs={"texts": [prompt]},
                progress=True,
                clip_denoised=True,
                use_fp16=(device.type == "cuda"),
                use_karras=True,
                karras_steps=64,
                sigma_min=1e-3,
                sigma_max=160,
                s_churn=0,
            )

            print("Decoding mesh...")

            mesh = decode_latent_mesh(xm, latents[0]).tri_mesh()

            obj_path = output_dir / "generated_asset.obj"
            ply_path = output_dir / "generated_asset.ply"

            with open(obj_path, "w", encoding="utf-8") as file:
                mesh.write_obj(file)

            with open(ply_path, "wb") as file:
                mesh.write_ply(file)

        elapsed = time.time() - start

        print("\nGeneration successful!")
        print(f"OBJ: {obj_path.resolve()}")
        print(f"PLY: {ply_path.resolve()}")
        print(f"Time: {elapsed:.2f} seconds")

        if device.type == "cuda":
            print(
                f"Peak GPU memory: "
                f"{torch.cuda.max_memory_allocated() / 1024**3:.2f} GB"
            )

    except torch.cuda.OutOfMemoryError:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        print("GPU out of memory. Try CPU execution or lower-memory settings.")
        raise

    except Exception as error:
        print(f"Generation failed: {type(error).__name__}: {error}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--prompt",
        required=True,
        help="Description of the 3D object to generate",
    )

    args = parser.parse_args()
    generate(args.prompt)
