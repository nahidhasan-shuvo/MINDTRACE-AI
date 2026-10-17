from pathlib import Path
import cv2
import librosa
import numpy as np
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image


# ----------------- MODEL DEFINITION -----------------

class ImageEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        backbone = models.resnet18(weights=None)
        backbone.fc = nn.Identity()
        self.backbone = backbone
        self.classifier = nn.Linear(512, 2)

    def forward(self, x):
        features = self.backbone(x)
        return self.classifier(features)


class AudioEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(1, 16, kernel_size=3, padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(16, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1)),
            nn.Flatten()
        )
        self.classifier = nn.Linear(64, 2)

    def forward(self, x):
        features = self.features(x)
        return self.classifier(features)


class VideoEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv3d(3, 16, kernel_size=3, padding=1),
            nn.BatchNorm3d(16),
            nn.ReLU(),
            nn.MaxPool3d(2),
            nn.Conv3d(16, 32, kernel_size=3, padding=1),
            nn.BatchNorm3d(32),
            nn.ReLU(),
            nn.MaxPool3d(2),
            nn.Conv3d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm3d(64),
            nn.ReLU(),
            nn.AdaptiveAvgPool3d((1, 1, 1)),
            nn.Flatten()
        )
        self.classifier = nn.Linear(64, 2)

    def forward(self, x):
        features = self.features(x)
        return self.classifier(features)


class LateFusionModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.image_encoder = ImageEncoder()
        self.audio_encoder = AudioEncoder()
        self.video_encoder = VideoEncoder()

    def forward(self, image, audio, video):
        image_logits = self.image_encoder(image)
        audio_logits = self.audio_encoder(audio)
        video_logits = self.video_encoder(video)
        return (image_logits + audio_logits + video_logits) / 3.0


# ----------------- INFERENCE CLASS -----------------

class AutismInference:
    def __init__(self, checkpoint_path="results/late_fusion_autism_model.pth"):
        self.device = torch.device(
            "mps" if torch.backends.mps.is_available()
            else "cuda" if torch.cuda.is_available()
            else "cpu"
        )
        self.model = LateFusionModel().to(self.device)

        # মডেল ওয়েট লোড করা
        ckpt_file = Path(checkpoint_path)
        if not ckpt_file.exists():
            # রুট ফোল্ডারে থাকলে চেক করবে
            ckpt_file = Path("late_fusion_autism_model.pth")

        if ckpt_file.exists():
            checkpoint = torch.load(ckpt_file, map_location=self.device)
            self.model.load_state_dict(checkpoint["model_state_dict"])
            print(f"Loaded weights from {ckpt_file}")
        else:
            print(f"Warning: Checkpoint not found at {ckpt_file}. Using untrained weights.")

        self.model.eval()

        self.image_transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    def preprocess_image(self, path):
        img = Image.open(path).convert("RGB")
        return self.image_transform(img).unsqueeze(0).to(self.device)

    def preprocess_audio(self, path):
        audio, sr = librosa.load(path, sr=16000, mono=True)
        mfcc = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=40)
        if mfcc.shape[1] < 128:
            mfcc = np.pad(mfcc, ((0, 0), (0, 128 - mfcc.shape[1])), mode="constant")
        else:
            mfcc = mfcc[:, :128]
        mfcc = (mfcc - mfcc.mean()) / (mfcc.std() + 1e-6)
        tensor = torch.tensor(mfcc, dtype=torch.float32).unsqueeze(0).unsqueeze(0)
        return tensor.to(self.device)

    def preprocess_video(self, path):
        cap = cv2.VideoCapture(path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            raise ValueError(f"Cannot read video: {path}")

        indices = np.linspace(0, total_frames - 1, 8).astype(int)
        frames = []
        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
            ok, frame = cap.read()
            if not ok:
                break
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame = cv2.resize(frame, (112, 112)).astype(np.float32) / 255.0
            frame = (frame - 0.5) / 0.5
            frames.append(frame)
        cap.release()

        # প্যাডিং যদি কোনো কারণে ৮ ফ্রেম না পাওয়া যায়
        while len(frames) < 8:
            frames.append(np.zeros((112, 112, 3), dtype=np.float32))

        frames = np.stack(frames[:8], axis=0)  # T, H, W, C
        frames = np.transpose(frames, (3, 0, 1, 2))  # C, T, H, W
        tensor = torch.tensor(frames, dtype=torch.float32).unsqueeze(0)
        return tensor.to(self.device)

    def predict(self, image_path, audio_path, video_path):
        with torch.no_grad():
            img_t = self.preprocess_image(image_path)
            aud_t = self.preprocess_audio(audio_path)
            vid_t = self.preprocess_video(video_path)

            logits = self.model(img_t, aud_t, vid_t)
            probs = torch.softmax(logits, dim=1).cpu().numpy()[0]

            control_prob = float(probs[0])
            autistic_prob = float(probs[1])

            predicted_label = 1 if autistic_prob >= 0.50 else 0
            predicted_class = "Autistic" if predicted_label == 1 else "Control"
            confidence = autistic_prob if predicted_label == 1 else control_prob

            return {
                "predicted_class": predicted_class,
                "label": predicted_label,
                "confidence": round(confidence * 100, 2),
                "control_probability": round(control_prob * 100, 2),
                "autistic_probability": round(autistic_prob * 100, 2)
            }