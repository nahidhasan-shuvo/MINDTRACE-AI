
import random
from pathlib import Path

import cv2
import librosa
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torchvision import models, transforms
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
    roc_curve,
    ConfusionMatrixDisplay
)
from PIL import Image


# =========================================================
# 1. SETTINGS
# =========================================================

SEED = 42
BATCH_SIZE = 4
EPOCHS = 30
LR = 1e-4

IMG_SIZE = 224
VIDEO_SIZE = 112
VIDEO_FRAMES = 8

AUDIO_SR = 16000
N_MFCC = 40
AUDIO_FRAMES = 128

ROOT_DIR = Path("/Users/nahidhasan/Desktop/dataset_Autism")

OUTPUT_DIR = Path("/Users/nahidhasan/Autism_combine/results")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DEVICE = torch.device(
    "mps" if torch.backends.mps.is_available()
    else "cuda" if torch.cuda.is_available()
    else "cpu"
)

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)

print("Device:", DEVICE)
print("Dataset:", ROOT_DIR)


# =========================================================
# 2. MATCH IMAGE, AUDIO AND VIDEO BY SUBJECT
# =========================================================

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
AUDIO_EXTS = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}
VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}


def index_files(folder, extensions):
    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder}")

    indexed = {}

    for file in folder.iterdir():
        if file.is_file() and file.suffix.lower() in extensions:
            key = file.stem.lower()

            if key in indexed:
                raise ValueError(
                    f"Duplicate filename stem in {folder}: {key}"
                )

            indexed[key] = file

    return indexed


def build_records():
    records = []

    classes = [
        ("Non_Autistic", 0),
        ("Autistic", 1)
    ]

    for class_name, label in classes:

        image_map = index_files(
            ROOT_DIR / "Image2" / class_name,
            IMAGE_EXTS
        )

        audio_map = index_files(
            ROOT_DIR / "Voice2" / class_name,
            AUDIO_EXTS
        )

        video_map = index_files(
            ROOT_DIR / "Video2" / class_name,
            VIDEO_EXTS
        )

        common_keys = (
            set(image_map) & set(audio_map) & set(video_map)
        )

        missing = (
            set(image_map) | set(audio_map) | set(video_map)
        ) - common_keys

        if missing:
            print(
                f"Warning: {len(missing)} unmatched files "
                f"for {class_name}; these subjects are excluded."
            )

        for key in sorted(common_keys):
            records.append({
                "subject": f"{class_name}_{key}",
                "image": str(image_map[key]),
                "audio": str(audio_map[key]),
                "video": str(video_map[key]),
                "label": label
            })

    df = pd.DataFrame(records)

    if df.empty:
        raise ValueError(
            "No matched subjects found. Check folder names, "
            "extensions and filenames."
        )

    if df["subject"].duplicated().any():
        raise ValueError("Duplicate subject IDs found.")

    print("\nMatched subjects:", len(df))
    print(df["label"].value_counts().rename(
        index={0: "Control", 1: "Autistic"}
    ))

    return df


# =========================================================
# 3. SPLIT: 80% TRAIN / 20% TEST
#    NO VALIDATION SET
# =========================================================

df = build_records()

train_df, test_df = train_test_split(
    df,
    test_size=0.20,
    random_state=SEED,
    stratify=df["label"]
)

train_df = train_df.reset_index(drop=True)
test_df = test_df.reset_index(drop=True)

print("\nTraining subjects:", len(train_df))
print("Testing subjects:", len(test_df))
print("Validation subjects: 0")

train_df.to_csv(OUTPUT_DIR / "train_subjects.csv", index=False)
test_df.to_csv(OUTPUT_DIR / "test_subjects.csv", index=False)


# =========================================================
# 4. IMAGE TRANSFORM
# =========================================================

image_transform = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


# =========================================================
# 5. LOAD AUDIO AS MFCC
# =========================================================

def load_audio(path):
    audio, sr = librosa.load(
        path,
        sr=AUDIO_SR,
        mono=True
    )

    if len(audio) == 0:
        raise ValueError(f"Empty audio file: {path}")

    mfcc = librosa.feature.mfcc(
        y=audio,
        sr=sr,
        n_mfcc=N_MFCC
    )

    # Fixed number of time frames
    if mfcc.shape[1] < AUDIO_FRAMES:
        mfcc = np.pad(
            mfcc,
            ((0, 0), (0, AUDIO_FRAMES - mfcc.shape[1])),
            mode="constant"
        )
    else:
        mfcc = mfcc[:, :AUDIO_FRAMES]

    # Normalize each audio sample
    mean = mfcc.mean()
    std = mfcc.std()

    mfcc = (mfcc - mean) / (std + 1e-6)

    return torch.tensor(
        mfcc, dtype=torch.float32
    ).unsqueeze(0)


# =========================================================
# 6. LOAD VIDEO FRAMES
# =========================================================

def load_video(path):
    cap = cv2.VideoCapture(path)

    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if total_frames <= 0:
        cap.release()
        raise ValueError(f"Video contains no readable frames: {path}")

    indices = np.linspace(
        0, total_frames - 1, VIDEO_FRAMES
    ).astype(int)

    frames = []

    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(idx))
        ok, frame = cap.read()

        if not ok:
            cap.release()
            raise ValueError(
                f"Could not read frame {idx} from {path}"
            )

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = cv2.resize(
            frame, (VIDEO_SIZE, VIDEO_SIZE)
        )

        frame = frame.astype(np.float32) / 255.0

        # Normalize image channels to approximately [-1, 1]
        frame = (frame - 0.5) / 0.5
        frames.append(frame)

    cap.release()

    # T,H,W,C -> C,T,H,W
    frames = np.stack(frames, axis=0)
    frames = np.transpose(frames, (3, 0, 1, 2))

    return torch.tensor(frames, dtype=torch.float32)


# =========================================================
# 7. DATASET
# =========================================================

class AutismDataset(Dataset):

    def __init__(self, dataframe):
        self.df = dataframe.reset_index(drop=True)

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]

        image = Image.open(row["image"]).convert("RGB")
        image = image_transform(image)

        audio = load_audio(row["audio"])
        video = load_video(row["video"])

        label = torch.tensor(
            int(row["label"]), dtype=torch.long
        )

        return image, audio, video, label


train_dataset = AutismDataset(train_df)
test_dataset = AutismDataset(test_df)

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=0
)

test_loader = DataLoader(
    test_dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0
)


# =========================================================
# 8. IMAGE ENCODER: RESNET18
# =========================================================

class ImageEncoder(nn.Module):

    def __init__(self):
        super().__init__()

        try:
            backbone = models.resnet18(
                weights=models.ResNet18_Weights.DEFAULT
            )
            print("ResNet18 ImageNet weights loaded.")

        except Exception as exc:
            print("Pretrained weights unavailable:", exc)
            print("Using randomly initialized ResNet18.")

            backbone = models.resnet18(weights=None)

        backbone.fc = nn.Identity()
        self.backbone = backbone

        self.classifier = nn.Linear(512, 2)

    def forward(self, x):
        features = self.backbone(x)
        logits = self.classifier(features)
        return logits


# =========================================================
# 9. AUDIO ENCODER: MFCC + CNN
# =========================================================

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


# =========================================================
# 10. VIDEO ENCODER: 3D CNN
# =========================================================

class VideoEncoder(nn.Module):

    def __init__(self):
        super().__init__()

        self.features = nn.Sequential(
            nn.Conv3d(
                3, 16, kernel_size=3, padding=1
            ),
            nn.BatchNorm3d(16),
            nn.ReLU(),
            nn.MaxPool3d(2),

            nn.Conv3d(
                16, 32, kernel_size=3, padding=1
            ),
            nn.BatchNorm3d(32),
            nn.ReLU(),
            nn.MaxPool3d(2),

            nn.Conv3d(
                32, 64, kernel_size=3, padding=1
            ),
            nn.BatchNorm3d(64),
            nn.ReLU(),

            nn.AdaptiveAvgPool3d((1, 1, 1)),
            nn.Flatten()
        )

        self.classifier = nn.Linear(64, 2)

    def forward(self, x):
        features = self.features(x)
        return self.classifier(features)


# =========================================================
# 11. LATE FUSION MODEL
# =========================================================

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

        # Equal-weight late fusion of all three predictions
        fused_logits = (
            image_logits + audio_logits + video_logits
        ) / 3.0

        return fused_logits


model = LateFusionModel().to(DEVICE)

criterion = nn.CrossEntropyLoss()

optimizer = torch.optim.AdamW(
    model.parameters(),
    lr=LR,
    weight_decay=1e-3
)


# =========================================================
# 12. TRAINING
#    NO VALIDATION / NO TESTING DURING TRAINING
# =========================================================

train_losses = []
train_accuracies = []

for epoch in range(EPOCHS):

    model.train()

    total_loss = 0.0
    correct = 0
    total = 0

    for images, audios, videos, labels in train_loader:

        images = images.to(DEVICE)
        audios = audios.to(DEVICE)
        videos = videos.to(DEVICE)
        labels = labels.to(DEVICE)

        optimizer.zero_grad()

        logits = model(images, audios, videos)
        loss = criterion(logits, labels)

        loss.backward()
        optimizer.step()

        batch_size = labels.size(0)

        total_loss += loss.item() * batch_size

        predictions = logits.argmax(dim=1)
        correct += (predictions == labels).sum().item()
        total += batch_size

    epoch_loss = total_loss / total
    epoch_accuracy = correct / total

    train_losses.append(epoch_loss)
    train_accuracies.append(epoch_accuracy)

    print(
        f"Epoch {epoch + 1:02d}/{EPOCHS} | "
        f"Train Loss: {epoch_loss:.4f} | "
        f"Train Accuracy: {epoch_accuracy:.4f}"
    )


# =========================================================
# 13. SAVE TRAINED MODEL
# =========================================================

model_path = OUTPUT_DIR / "late_fusion_autism_model.pth"

torch.save({
    "model_state_dict": model.state_dict(),
    "seed": SEED,
    "image_size": IMG_SIZE,
    "video_size": VIDEO_SIZE,
    "video_frames": VIDEO_FRAMES,
    "audio_sr": AUDIO_SR,
    "n_mfcc": N_MFCC,
    "audio_frames": AUDIO_FRAMES,
    "classes": {
        "Control": 0,
        "Autistic": 1
    }
}, model_path)

print("\nSaved model:", model_path)


# =========================================================
# 14. TRAINING CURVES
# =========================================================

fig, axes = plt.subplots(1, 2, figsize=(12, 4))

axes[0].plot(
    range(1, EPOCHS + 1), train_losses, marker="o"
)
axes[0].set_title("Training Loss")
axes[0].set_xlabel("Epoch")
axes[0].set_ylabel("Loss")
axes[0].grid(True)

axes[1].plot(
    range(1, EPOCHS + 1),
    train_accuracies,
    marker="o"
)
axes[1].set_title("Training Accuracy")
axes[1].set_xlabel("Epoch")
axes[1].set_ylabel("Accuracy")
axes[1].grid(True)

plt.tight_layout()
plt.savefig(
    OUTPUT_DIR / "training_curves.png",
    dpi=300,
    bbox_inches="tight"
)
plt.show()
plt.close()


# =========================================================
# 15. FINAL EVALUATION ON THE UNSEEN 20% TEST DATA
# =========================================================

model.eval()

y_true = []
y_prob = []
y_pred = []

with torch.no_grad():

    for images, audios, videos, labels in test_loader:

        images = images.to(DEVICE)
        audios = audios.to(DEVICE)
        videos = videos.to(DEVICE)

        logits = model(images, audios, videos)

        probabilities = torch.softmax(logits, dim=1)[:, 1]

        # Standard probability threshold = 0.50
        predictions = (probabilities >= 0.50).long()

        y_true.extend(labels.numpy().tolist())
        y_prob.extend(probabilities.cpu().numpy().tolist())
        y_pred.extend(predictions.cpu().numpy().tolist())


y_true = np.array(y_true)
y_prob = np.array(y_prob)
y_pred = np.array(y_pred)

accuracy = accuracy_score(y_true, y_pred)
precision = precision_score(
    y_true, y_pred, zero_division=0
)
sensitivity = recall_score(
    y_true, y_pred, zero_division=0
)
f1 = f1_score(y_true, y_pred, zero_division=0)

cm = confusion_matrix(y_true, y_pred, labels=[0, 1])

tn, fp, fn, tp = cm.ravel()

specificity = tn / (tn + fp) if (tn + fp) else 0.0

if len(np.unique(y_true)) == 2:
    roc_auc = roc_auc_score(y_true, y_prob)
else:
    roc_auc = float("nan")

print("\n========== FINAL TEST RESULTS ==========")
print(f"Test subjects: {len(y_true)}")
print(f"Accuracy:     {accuracy:.4f}")
print(f"Precision:    {precision:.4f}")
print(f"Sensitivity:  {sensitivity:.4f}")
print(f"Specificity:  {specificity:.4f}")
print(f"F1-score:     {f1:.4f}")
print(f"ROC-AUC:      {roc_auc:.4f}")
print(f"TN={tn}, FP={fp}, FN={fn}, TP={tp}")

print("\nClassification Report:")
print(classification_report(
    y_true,
    y_pred,
    labels=[0, 1],
    target_names=["Control", "Autistic"],
    zero_division=0
))


# =========================================================
# 16. TEST CONFUSION MATRIX
# =========================================================

disp = ConfusionMatrixDisplay(
    confusion_matrix=cm,
    display_labels=["Control", "Autistic"]
)

disp.plot(cmap="Blues", values_format="d")
plt.title("Test Confusion Matrix - Late Fusion")
plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "test_confusion_matrix.png",
    dpi=300,
    bbox_inches="tight"
)
plt.show()
plt.close()


# =========================================================
# 17. TEST ROC CURVE
# =========================================================

if len(np.unique(y_true)) == 2:

    fpr, tpr, thresholds = roc_curve(y_true, y_prob)

    plt.figure(figsize=(7, 6))

    plt.plot(
        fpr,
        tpr,
        linewidth=2,
        label=f"Late Fusion (AUC = {roc_auc:.3f})"
    )

    plt.plot(
        [0, 1], [0, 1],
        linestyle="--",
        label="Random Classifier"
    )

    plt.xlabel("False Positive Rate")
    plt.ylabel("True Positive Rate")
    plt.title("ROC Curve - Unseen Test Data")
    plt.legend(loc="lower right")
    plt.grid(True)
    plt.tight_layout()

    plt.savefig(
        OUTPUT_DIR / "test_roc_curve.png",
        dpi=300,
        bbox_inches="tight"
    )

    plt.show()
    plt.close()

else:
    print(
        "ROC curve cannot be calculated because the test set "
        "contains only one class."
    )


# =========================================================
# 18. SAVE TEST METRICS AND PREDICTIONS
# =========================================================

metrics = pd.DataFrame([{
    "Test_Samples": len(y_true),
    "Accuracy": accuracy,
    "Precision": precision,
    "Sensitivity": sensitivity,
    "Specificity": specificity,
    "F1_Score": f1,
    "ROC_AUC": roc_auc,
    "TN": tn,
    "FP": fp,
    "FN": fn,
    "TP": tp
}])

metrics.to_csv(
    OUTPUT_DIR / "test_metrics.csv",
    index=False
)

predictions_df = test_df.copy()

predictions_df["Actual_Label"] = y_true
predictions_df["Autistic_Probability"] = y_prob
predictions_df["Predicted_Label"] = y_pred

predictions_df["Actual_Class"] = predictions_df[
    "Actual_Label"
].map({0: "Control", 1: "Autistic"})

predictions_df["Predicted_Class"] = predictions_df[
    "Predicted_Label"
].map({0: "Control", 1: "Autistic"})

predictions_df.to_csv(
    OUTPUT_DIR / "test_predictions.csv",
    index=False
)

print("\nAll outputs saved to:")
print(OUTPUT_DIR)

print("\nFiles generated:")
print("- late_fusion_autism_model.pth")
print("- training_curves.png")
print("- test_confusion_matrix.png")
print("- test_roc_curve.png")
print("- test_metrics.csv")
print("- test_predictions.csv")
print("- train_subjects.csv")
print("- test_subjects.csv")

print("\nTraining and test evaluation completed.")
