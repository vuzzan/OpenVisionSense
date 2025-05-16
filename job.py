import time
import torch
from db import query_db
import os,shutil
import logging
from pathlib import Path
import random
from torchvision import datasets, transforms, models
from torch import nn, optim
from torch.utils.data import DataLoader
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
import sqlite3
import shutil

# Configure logger for module1
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
fh1 = logging.FileHandler('logs/jobs.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh1.setFormatter(formatter)
logger.addHandler(fh1)
logger.addHandler(logging.StreamHandler())
job_id = 0

data_dir = "D:/anomaly_dectection/OpenVisionSense-main/data"

if not os.path.exists("./data"):
    os.makedirs("./data")

# Triet lam ==========================
# Paths
torch.manual_seed(42)
random.seed(42)
# Detect and use CUDA if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")
# Prepare dataset folders
def prepare_data(project):
    print("Preparing data... start")
    data_root = Path("data/project_"+str(project["project_id"]))
    output_root = Path("data/project_"+str(project["project_id"])+"/dataset")
    output_root.mkdir(parents=True, exist_ok=True)

    train_dir = Path("data/project_"+str(project["project_id"])+"/dataset" + "/train")
    # Create directories
    train_dir.mkdir(parents=True, exist_ok=True)
    val_dir = Path("data/project_"+str(project["project_id"])+"/dataset" +"/val")
    val_dir.mkdir(parents=True, exist_ok=True)

    classes = []
    for cls in project["classes"]:
        classes.append("class_" + str(cls["class_id"]))
    print(classes)
    # Copy images to train and val directories

    val_ratio = 0.2

    for cls in classes:
        img_dir = data_root / cls
        all_imgs = list(img_dir.glob("*.jpg"))
        random.shuffle(all_imgs)

        split_idx = int(len(all_imgs) * (1 - val_ratio))
        train_imgs = all_imgs[:split_idx]
        val_imgs = all_imgs[split_idx:]

        for split, imgs in zip([train_dir, val_dir], [train_imgs, val_imgs]):
            split_cls_dir = split / cls
            split_cls_dir.mkdir(parents=True, exist_ok=True)
            for img in imgs:
                shutil.copy(img, split_cls_dir / img.name)
    print("Preparing data... done")
    print("Train dir: ", train_dir)
    print("Val dir: ", val_dir)
    print("Preparing data... done")
    return train_dir, val_dir
#print("Preparing data... Triet lam ")
#prepare_data()



def start_training(project):
    print("Starting training... Triet lam")
    print(project)
    #Preepare data
    [train_dir, val_dir] = prepare_data(project)
    # Load datasets
        # Data transforms
    train_tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.RandomAffine(degrees=0, translate=(0.1, 0.1)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    val_tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    print("Loading datasets... Triet lam")
    # Load datasets
    train_ds = datasets.ImageFolder(train_dir, transform=train_tf)
    val_ds = datasets.ImageFolder(val_dir, transform=val_tf)
    train_loader = DataLoader(train_ds, batch_size=16, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=16)

    # Training setup
    base_model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
    # Freeze base model (optional based on experimentation)
    for param in base_model.parameters():
        param.requires_grad = True
        # Modify classifier to have 8-layer structure (approximate)
    base_model.fc = nn.Sequential(
        nn.Linear(base_model.fc.in_features, 512),  # Layer 6
        nn.ReLU(),                                  # Layer 7
        nn.Dropout(0.5),
        nn.Linear(512, 2)                           # Layer 8 (output)
    )
    model = base_model.to(device)
    # Print model summary
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    train_losses, val_losses, val_accuracies = [], [], []


    for epoch in range(25):
        model.train()
        total_loss = 0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            out = model(x)
            loss = criterion(out, y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        train_losses.append(total_loss / len(train_loader))

        # Validation
        model.eval()
        val_loss, correct, total = 0, 0, 0
        all_preds, all_labels = [], []
        with torch.no_grad():
            for x, y in val_loader:
                x, y = x.to(device), y.to(device)
                out = model(x)
                loss = criterion(out, y)
                val_loss += loss.item()
                preds = out.argmax(1)
                correct += (preds == y).sum().item()
                total += y.size(0)
                all_preds.extend(preds.cpu().numpy())
                all_labels.extend(y.cpu().numpy())

        val_losses.append(val_loss / len(val_loader))
        acc = correct / total
        val_accuracies.append(acc)
        print(f"Epoch {epoch+1}: Train Loss={train_losses[-1]:.4f}, Val Loss={val_losses[-1]:.4f}, Acc={acc:.4f}")
    
    if epoch == 24:
        # Save model
        model_file = "model.pth"
        torch.save(model.state_dict(), "data/project_"+str(project["project_id"]) + "/" + model_file)
        shutil.rmtree("data/project_"+str(project["project_id"]) + "/dataset")
        print(f"Model saved to {model_file}")
        return model_file
    return ""

# Class labels
# class_names = train_ds.classes
# print(f"Class names: {class_names}")

def predict_single_image(project,model_file, image_path):
    print(f"Predicting image:")
    print(image_path)
    print(model_file)
    print("Preparing image... Triet lam")
    class_names = []
    for cls in project["classes"]:
        class_names.append(str(cls["class_name"]))
    print(class_names)
    # Load model
    # model_file = "project_model_V1_training_test.pth"
    val_tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
     # Training setup
    base_model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
    # Freeze base model (optional based on experimentation)
    for param in base_model.parameters():
        param.requires_grad = True
        # Modify classifier to have 8-layer structure (approximate)
    base_model.fc = nn.Sequential(
        nn.Linear(base_model.fc.in_features, 512),  # Layer 6
        nn.ReLU(),                                  # Layer 7
        nn.Dropout(0.5),
        nn.Linear(512, 2)                           # Layer 8 (output)
    )
    model = base_model.to(device)
    #
    ckpoints = torch.load(model_file)
    model.load_state_dict(ckpoints)
    print("Loading model... Triet lam")
    model.eval()
    img = Image.open(image_path).convert("RGB")
    img_tensor = val_tf(img).unsqueeze(0).to(device)
    output = model(img_tensor)

    # Tính xác suất dự đoán
    probs = torch.softmax(output, dim=1).cpu().detach().numpy()[0]
    pred_class_idx = output.argmax(1).item()
    pred_label = class_names[pred_class_idx]

    result= {}
    result["result_file_path"] = ""
    result["job_class"] = pred_label
    result["job_result"] = ""
    return result

    # # Lấy true label từ tên thư mục cha
    # true_label = Path(image_path).parent.name

    # # Hiển thị ảnh + label
    # confidence = probs[pred_class_idx] * 100
    # title = f"Pred: {pred_label} ({confidence:.1f}%) | True: {true_label}"

    # plt.imshow(img)
    # plt.title(title)
    # plt.axis('off')
    # plt.show()

    # # Biểu đồ xác suất
    # plt.figure(figsize=(4, 2))
    # plt.bar(class_names, probs, color=['skyblue', 'salmon'])
    # plt.title("Prediction Probabilities")
    # plt.ylabel("Confidence")
    # plt.ylim(0, 1)
    # plt.grid(True, axis='y', linestyle='--', alpha=0.5)
    # plt.tight_layout()
    # plt.show()
    
# End Triet lam ==========================

def start_job_training(project):
    logger.info("start_job_training projects StartTraining")
    logger.info(project)
    sql = "update projects set project_status='StartTraining' where project_id=?"
    query_db(sql, (project["project_id"], ), False)
    # Do training --
    # traing Triet lam
    print("Start training... Triet lam start_job_training")
    model = start_training(project)
    # End training Triet lam
    project_model = model
    project_status = "Training Done"        # Or training fail
    if project_model == "":
        project_status = "Training Fail"        # Or training fail    

    # Training done
    sql = "update projects set project_status=?,project_model=? where project_id=?"
    query_db(sql, (project_status, project_model, project["project_id"]), False)
    logger.info("start_job projects StartTraining")


def start_job_run_model(job):
    logger.info("start_job_run_model queue_jobs ")
    logger.info(job)
    sql = "update queue_jobs set job_status='Start Job' where job_id=?"
    query_db(sql, (job["job_id"], ), False)
    # process job here
    sql = "select * from projects where project_id=?"
    project = query_db(sql, (job["project_id"], ), True)
    print(project)
    project["classes"] = query_db("select * from project_classes where project_id=" + str(project["project_id"]), ())
    # Process with model
    model_file = data_dir + "/project_"+str(job["project_id"])+"/"+project["project_model"]
    source_file_path =  data_dir + job["source_file_path"]
    print(model_file)
    print(source_file_path)
    # do predict
    result = predict_single_image(project,model_file, source_file_path)
    print(result)

    result_file_path = result["result_file_path"]
    job_class =  result["job_class"]
    job_result = result["job_result"]

    # End competed
    sql = "update queue_jobs set job_result=?, result_file_path=?, job_class=?, job_status='Done' where job_id=?"
    query_db(sql, (job_result, result_file_path, job_class, job["job_id"]), False)
    logger.info("start_job2 queue_jobs done")


def schedule_task_training():
    global job_id
    sql = "select * from projects where project_status='QueueTraining'"
    project_list = query_db(sql, ())
    if len(project_list)==0:
        # Unit test job running
        # job_id = job_id + 1
        my_id = job_id
        # logger.info("#" + str(my_id) + " Start QueueTraining...")
        # time.sleep(10)
        #logger.info("#" + str(my_id) + " Job QueueTraining...END ")

    for project in project_list:
        project["classes"] = query_db("select * from project_classes where project_id=" + str(project["project_id"]), ())
        start_job_training(project)


def schedule_task_run_model():
    global job_id

    # Job list
    sql = "select * from queue_jobs where job_status='Wait Run'"
    #print(sql)
    job_list2 = query_db(sql, ())
    for job2 in job_list2:
        start_job_run_model(job2)
