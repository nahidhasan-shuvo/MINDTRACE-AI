from pathlib import Path
from tempfile import TemporaryDirectory
import shutil

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from inference import AutismInference

app = FastAPI(
    title="MINDTRACE AI API",
    description="Multimodal Autism Research Platform",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = AutismInference()

ALLOWED_EXTENSIONS = {
    "image": {".jpg", ".jpeg", ".png", ".webp", ".bmp"},
    "audio": {".wav", ".mp3", ".m4a", ".ogg", ".flac"},
    "video": {".mp4", ".avi", ".mov", ".mkv", ".webm"},
}

MAX_FILE_SIZE = 25 * 1024 * 1024


async def save_upload(upload: UploadFile, destination: Path, kind: str):
    extension = Path(upload.filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS[kind]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported {kind} file format: {extension}",
        )

    total_size = 0
    with destination.open("wb") as output:
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            total_size += len(chunk)
            if total_size > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail=f"{kind.capitalize()} file exceeds 25 MB.",
                )
            output.write(chunk)

    if total_size == 0:
        raise HTTPException(
            status_code=400,
            detail=f"The {kind} file is empty.",
        )


@app.get("/")
def home():
    html_file = Path(__file__).parent / "index.html"
    if html_file.exists():
        return FileResponse(html_file)
    return {"message": "index.html not found!"}


# -------------------------------------------------------------
# আপনার hero-baby.png ছবি সরাসরি ব্রাউজারে সার্ভ করার রুট
# -------------------------------------------------------------
@app.get("/hero-baby.png")
def get_hero_image():
    img_path = Path(__file__).parent / "hero-baby.png"
    if img_path.exists():
        return FileResponse(img_path)
    raise HTTPException(status_code=404, detail="hero-baby.png not found")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "device": str(model.device),
        "checkpoint": "late_fusion_autism_model.pth",
    }


@app.post("/predict")
async def predict(
    image: UploadFile = File(...),
    audio: UploadFile = File(...),
    video: UploadFile = File(...),
):
    try:
        with TemporaryDirectory(prefix="mindtrace_") as temp_dir:
            folder = Path(temp_dir)

            img_ext = Path(image.filename or "").suffix.lower()
            aud_ext = Path(audio.filename or "").suffix.lower()
            vid_ext = Path(video.filename or "").suffix.lower()

            image_path = folder / f"input_image{img_ext}"
            audio_path = folder / f"input_audio{aud_ext}"
            video_path = folder / f"input_video{vid_ext}"

            await save_upload(image, image_path, "image")
            await save_upload(audio, audio_path, "audio")
            await save_upload(video, video_path, "video")

            result = model.predict(
                str(image_path),
                str(audio_path),
                str(video_path),
            )

            return {
                "success": True,
                "result": result,
                "notice": "Research prototype only. Not a clinical diagnosis.",
            }

    except HTTPException:
        raise
    except Exception as exc:
        print(f"Prediction error: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Prediction error: {str(exc)}",
        ) from exc
    finally:
        await image.close()
        await audio.close()
        await video.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)