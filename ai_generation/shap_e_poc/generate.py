
import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from mesh_validator import validate_mesh
import torch
from shap_e.diffusion.sample import sample_latents
from shap_e.diffusion.gaussian_diffusion import diffusion_from_config
from shap_e.models.download import load_model, load_config
from shap_e.util.notebooks import decode_latent_mesh


BASE_DIR = Path(__file__).resolve().parent
CACHE_DIR = BASE_DIR.parents[1] / "shap_e_model_cache"
DEFAULT_OUTPUT_DIR = BASE_DIR / "outputs" / "samples"


def get_device(requested):
    if requested == "auto":
        return torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

    if requested == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but no CUDA GPU is available.")

    return torch.device(requested)


def set_seed(seed):
    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def generate(
    prompt,
    device_name="auto",
    steps=64,
    seed=42,
    guidance_scale=15.0,
    output_dir=DEFAULT_OUTPUT_DIR,
):
    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    if not 1 <= steps <= 128:
        raise ValueError("Steps must be between 1 and 128.")

    device = get_device(device_name)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%f")
    asset_name = f"shap_e_{timestamp}_{seed}"

    obj_path = output_dir / f"{asset_name}.obj"
    ply_path = output_dir / f"{asset_name}.ply"
    metadata_path = output_dir / f"{asset_name}.json"

    start_time = time.perf_counter()

    print("\n========== POLYGEN / SHAP-E ==========")
    print(f"Prompt: {prompt}")
    print(f"Device: {device}")
    print(f"Seed: {seed}")
    print(f"Steps: {steps}")
    print("======================================\n")

    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

        set_seed(seed)

        if device.type == "cuda":
            torch.cuda.reset_peak_memory_stats(device)

        print("[1/5] Loading transmitter model...")

        transmitter = load_model(
            "transmitter",
            device=device,
            cache_dir=str(CACHE_DIR),
        )

        print("[2/5] Loading text diffusion model...")

        model = load_model(
            "text300M",
            device=device,
            cache_dir=str(CACHE_DIR),
        )

        diffusion = diffusion_from_config(
            load_config(
                "diffusion",
                cache_dir=str(CACHE_DIR),
            )
        )

        print("[3/5] Generating 3D latent...")

        with torch.no_grad():
            latents = sample_latents(
                batch_size=1,
                model=model,
                diffusion=diffusion,
                guidance_scale=guidance_scale,
                model_kwargs={"texts": [prompt]},
                progress=True,
                clip_denoised=True,
                use_fp16=(device.type == "cuda"),
                use_karras=True,
                karras_steps=steps,
                sigma_min=1e-3,
                sigma_max=160,
                s_churn=0,
            )

            print("[4/5] Decoding 3D mesh...")

            mesh = decode_latent_mesh(
                transmitter,
                latents[0],
            ).tri_mesh()
            validation = validate_mesh(mesh)
            print(f"Mesh validation: {validation}")
            print("[5/5] Exporting 3D assets...")

            with open(obj_path, "w", encoding="utf-8") as file:
                mesh.write_obj(file)

            with open(ply_path, "wb") as file:
                mesh.write_ply(file)

        elapsed = time.perf_counter() - start_time

        gpu_memory = None

        if device.type == "cuda":
            gpu_memory = round(
                torch.cuda.max_memory_allocated(device) / (1024 ** 3),
                2,
            )

        metadata = {
            "project": "PolyGen",
            "provider": "Shap-E",
            "model": "text300M",
            "prompt": prompt,
            "seed": seed,
            "steps": steps,
            "guidance_scale": guidance_scale,
            "device": str(device),
            "generation_time_seconds": round(elapsed, 2),
            "peak_gpu_memory_gb": gpu_memory,
            "generated_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "files": {
                "obj": obj_path.name,
                "ply": ply_path.name,
            },
        }

        with open(metadata_path, "w", encoding="utf-8") as file:
            json.dump(metadata, file, indent=4)

        print("\n========== GENERATION SUCCESS ==========")
        print(f"OBJ: {obj_path.resolve()}")
        print(f"PLY: {ply_path.resolve()}")
        print(f"Metadata: {metadata_path.resolve()}")
        print(f"Time: {elapsed:.2f} seconds")

        if gpu_memory is not None:
            print(f"Peak GPU memory: {gpu_memory} GB")

        print("========================================\n")

        return metadata

    except torch.cuda.OutOfMemoryError as error:
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        print("\nGPU OUT OF MEMORY")
        print("Try CPU mode or reduce diffusion steps.")
        raise RuntimeError(
            "Shap-E generation exceeded available GPU memory."
        ) from error

    except Exception as error:
        print(
            f"\nGENERATION FAILED: "
            f"{type(error).__name__}: {error}"
        )
        raise


def main():
    parser = argparse.ArgumentParser(
        description="PolyGen Shap-E Text-to-3D Generator"
    )

    parser.add_argument(
        "--prompt",
        required=True,
        help="Description of the 3D object",
    )

    parser.add_argument(
        "--device",
        choices=["auto", "cuda", "cpu"],
        default="auto",
    )

    parser.add_argument(
        "--steps",
        type=int,
        default=64,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    parser.add_argument(
        "--guidance",
        type=float,
        default=15.0,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
    )

    args = parser.parse_args()

    generate(
        prompt=args.prompt,
        device_name=args.device,
        steps=args.steps,
        seed=args.seed,
        guidance_scale=args.guidance,
        output_dir=args.output,
    )


if __name__ == "__main__":
    main()
