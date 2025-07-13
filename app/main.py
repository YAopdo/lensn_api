from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import uuid, shutil, os

from .read_draw_lens import download_zmx_file, parse_zmx_and_create_optic

app = FastAPI(title="LensNet wrapper")

# --- CORS (adjust origins list to be as strict or open as you need) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],           # or ["https://yourfrontend.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OUTPUT_ROOT = Path("/tmp/lensnet_outputs")
OUTPUT_ROOT.mkdir(exist_ok=True)

@app.get("/lens")
def generate_lens(
    efl: float = Query(..., gt=0),
    f_number: float = Query(..., gt=0),
    hfov: float = Query(..., gt=0)
):
    """
    Fetches a Zemax design and produces 3 PNG analyses.
    Returns URLs you can fetch immediately.
    """
    try:
        zmx_path = download_zmx_file(efl, f_number, hfov,
                                     output_dir=str(OUTPUT_ROOT))
        lens = parse_zmx_and_create_optic(zmx_path)

        # do the analysis and save files next to the zmx
        import matplotlib.pyplot as plt
        from optiland import analysis as oa

        folder = Path(zmx_path).parent
        files = []

        lens.draw(num_rays=10);            plt.savefig(folder/"layout.png", dpi=300);  plt.close()
        oa.Distortion(lens).view();        plt.savefig(folder/"distortion.png", dpi=300);  plt.close()
        oa.RayFan(lens).view();            plt.savefig(folder/"rayfan.png", dpi=300);  plt.close()

        for f in ["layout.png", "distortion.png", "rayfan.png"]:
            files.append(f"/static/{folder.name}/{f}")

        return {"files": files}

    import traceback
    
    except Exception as e:
        print("💥 Exception occurred:")
        traceback.print_exc()  # Logs full traceback
        raise HTTPException(status_code=500, detail=str(e))

