import pathmagic

import sys

import torch
import torch.nn as nn
import numpy as np
import pandas as pd
import torch.cuda as cuda
import torch.optim as optim

from torch.utils.data import DataLoader

from tqdm import tqdm

from modules.dataset import SSegmDataset

from modules.loss import JetLoss
from modules.metrics import compute_mIoU
from modules.utils import (
    get_path, color_map, mask_to_rgb, batch_binary_mask, binary_mask,
    get_results
)

assert pathmagic


def build_loss_fn(loss_name, pixels_per_class=None, dataset="camvid"):

    if loss_name.lower() == 'bce':
        loss_fn = nn.BCELoss()
    elif loss_name.lower() == 'nll':
        loss_fn = nn.NLLLoss()
    elif loss_name.lower() == 'cross':
        loss_fn = nn.CrossEntropyLoss()
    elif loss_name.lower() == 'jet' and pixels_per_class is not None:
        if (dataset.lower() == "mastr1325" or dataset.lower() == "mastr1325_modified"):
            # Ignore pixel gets treated as background 
            loss_fn = JetLoss(background_idx=3, n_classes=4, pixels_per_class=pixels_per_class)
        else:
            loss_fn = JetLoss(pixels_per_class=pixels_per_class)
    else:
        raise ValueError(f"{loss_name} doesn't exists")

    return loss_fn


def build_optimizer(optimizer_name, model, lr=1e-4, wd=1e-4):

    if optimizer_name.lower() == 'adam':
        optimizer = optim.Adam(model.parameters(), lr=lr)

    elif optimizer_name.lower() == 'adamw':
        optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=wd)
    else:
        raise ValueError(f"{optimizer_name} doesn't exists")

    return optimizer


def load_dataset(dataset_name, num_classes):

    # Getting data workspace
    data_path = get_path('data')

    # Getting dataset path
    data_path += dataset_name.lower() + "/"

    if dataset_name.lower() == 'cityscapes':
        pass

    elif dataset_name.lower() == 'mastr1325':
        #code2id, id2code, name2id, id2name = color_map(color_dict)
        color_maps = {
            "code2id": {(0, 0, 0): 0, (1, 1, 1): 1, (2, 2, 2): 2, (3, 3, 3): 3},
            "id2code": {0: (0, 0, 0), 1: (1, 1, 1), 2: (2, 2, 2), 3: (3, 3, 3)},
            "name2id": {"obstacle": 0, "water": 1, "sky": 2, "ignore": 3},
            "id2name": {0: "obstacle", 1: "water", 2: "sky", 3: "ignore"}
        }

        train = SSegmDataset(dataset_name=dataset_name.lower(),
                            num_classes=num_classes,
                            root_path=data_path, mode="train",
                            color_map=color_maps)

        test = SSegmDataset(dataset_name=dataset_name.lower(),
                            root_path=data_path, mode="test",
                            num_classes=num_classes,
                            color_map=color_maps)

        valid = SSegmDataset(dataset_name=dataset_name.lower(),
                            root_path=data_path, mode="val",
                            num_classes=num_classes,
                            color_map=color_maps)

        dataset = {}
        dataset["train"] = train
        dataset["test"] = test
        dataset["valid"] = valid

        return dataset

    elif dataset_name.lower() == 'mastr1325_modified':
        #code2id, id2code, name2id, id2name = color_map(color_dict)
        color_maps = {
            "code2id": {(180, 30, 35): 0, (45, 100, 170): 1, (70, 200, 200): 2, (255, 255, 255): 3},
            "id2code": {0: (180, 30, 35), 1: (45, 100, 170), 2: (70, 200, 200), 3: (255, 255, 255)},
            "name2id": {"obstacle": 0, "water": 1, "sky": 2, "ignore": 3},
            "id2name": {0: "obstacle", 1: "water", 2: "sky", 3: "ignore"}
        }

        train = SSegmDataset(dataset_name=dataset_name.lower(),
                            num_classes=num_classes,
                            root_path=data_path, mode="train",
                            color_map=color_maps)

        test = SSegmDataset(dataset_name=dataset_name.lower(),
                            root_path=data_path, mode="test",
                            num_classes=num_classes,
                            color_map=color_maps)

        valid = SSegmDataset(dataset_name=dataset_name.lower(),
                            root_path=data_path, mode="val",
                            num_classes=num_classes,
                            color_map=color_maps)

        dataset = {}
        dataset["train"] = train
        dataset["test"] = test
        dataset["valid"] = valid

        return dataset

    elif dataset_name.lower() == 'camvid':

        # Getting color map codification
        color_dict = data_path + 'class_dict.csv'
        code2id, id2code, name2id, id2name = color_map(color_dict)
        print("code2id")
        print(code2id)
        print("id2code")
        print(id2code)
        print("name2id")
        print(name2id)
        print("id2name")
        print(id2name)

        color_maps = {
            "code2id": code2id,
            "id2code": id2code,
            "name2id": name2id,
            "id2name": id2name,
        }

        train = SSegmDataset(dataset_name=dataset_name.lower(),
                             num_classes=num_classes,
                             root_path=data_path, mode="train",
                             color_map=color_maps)

        test = SSegmDataset(dataset_name=dataset_name.lower(),
                            root_path=data_path, mode="test",
                            num_classes=num_classes,
                            color_map=color_maps)

        valid = SSegmDataset(dataset_name=dataset_name.lower(),
                             root_path=data_path, mode="val",
                             num_classes=num_classes,
                             color_map=color_maps)

        dataset = {}
        dataset["train"] = train
        dataset["test"] = test
        dataset["valid"] = valid

        return dataset

    else:
        raise ValueError(f"The dataset {dataset_name} doesn't exists")

    return dataset


def load_dataloaders(dataset, batch_size, num_workers=4):

    train_dataloader = DataLoader(
        dataset=dataset["train"],
        batch_size=batch_size,
        num_workers=num_workers,
        drop_last=False,
        shuffle=True,
    )

    valid_dataloader = DataLoader(
        dataset=dataset["valid"],
        batch_size=batch_size,
        num_workers=num_workers,
        drop_last=False,
        shuffle=True,
    )

    test_dataloader = DataLoader(
        dataset=dataset["test"],
        batch_size=batch_size,
        num_workers=num_workers,
        drop_last=False,
        shuffle=True,
    )

    dataloaders = {}
    dataloaders["train"] = train_dataloader
    dataloaders["valid"] = valid_dataloader
    dataloaders["test"] = test_dataloader

    return dataloaders


def one_epoch(params, mode):

    num_classes = params["num_classes"]
    stop = params["early_stop"]
    dataloader = params["dataloader"]
    model = params["model"]
    device = params["device"]
    loss_fn = params["loss_fn"]

    batch_loss = 0.0
    epoch_loss = 0.0

    miou = 0.0

    # Train
    if mode:

        optimizer = params["optimizer"]
        scheduler = params["scheduler"]

        # Creating the loop
        loop = tqdm(dataloader, leave=True, desc="Train")

        # Setting train mode
        model.train()

        # Train loop
        for batch_idx, data in enumerate(loop):

            # Getting data
            (x, y, z) = data

            # Casting
            x = x.float()
            y = y.float()

            # Clean gradient
            optimizer.zero_grad()

            # Sending data to cuda
            x = x.to(device)
            y = y.to(device)

            # Model Logits output
            logits = model(x)

            # Compute loss
            loss = loss_fn(logits, y)

            # Backward
            loss.backward()
            optimizer.step()

            # Getting batch loss
            batch_loss += loss.item() * x.size(0)

            # Convert predictions to class labels
            pred = logits.argmax(dim=1).unsqueeze(1).expand(-1, logits.shape[1], -1, -1).reshape(logits.shape)

            # Get binary mask prediction of the model
            pred_mask = batch_binary_mask(x.cpu().numpy(),
                                          pred.cpu().numpy(),
                                          num_classes).cuda()

            # Compute IoU
            miou += compute_mIoU(pred_mask, y, num_classes)

        # Getting lr epoch
        lr_epoch = optimizer.param_groups[0]["lr"]

        if stop:
            print(f'[INFO] LR epoch: {lr_epoch}')

        # Apply scheduler step
        if scheduler:
            scheduler.step()

        # Calculate epoch loss
        epoch_loss = batch_loss / len(dataloader.dataset)

        # Calculate mean of IoU
        miou = miou / len(dataloader)

        return model, epoch_loss, miou

    else:

        # Creating the loop
        loop = tqdm(dataloader, leave=True, desc="Val/Test")

        # Setting evaluation mode
        model.eval()

        # Val/Test loop
        for batch_idx, data in enumerate(loop):

            # Extracting data
            (x, y, z) = data

            # Casting
            x = x.float()
            y = y.float()

            # Send data to cuda
            x, y = x.to(device), y.to(device)

            with torch.no_grad():

                # Model Logits output
                logits = model(x)

                # Compute loss
                loss = loss_fn(logits, y)

                # Getting batch loss
                batch_loss += loss.item() * x.size(0)

                # Convert predictions to class labels
                pred = logits.argmax(dim=1).unsqueeze(1).expand(-1, logits.shape[1], -1, -1).reshape(logits.shape)

                # Get binary mask prediction of the model
                pred_mask = batch_binary_mask(x.cpu().numpy(),
                                              pred.cpu().numpy(),
                                              num_classes).cuda()

                # Compute IoU
                miou += compute_mIoU(pred_mask, y, num_classes)

        # Calculate epoch loss
        epoch_loss = batch_loss / len(dataloader.dataset)

        # Calculate mean of IoU
        miou = miou / len(dataloader)

        return epoch_loss, miou


def training(params):

    # Getting dataset name
    model_name = params["model_name"]

    cols = ['epoch', 'epoch time', 'train loss', 'valid loss']

    df = pd.DataFrame(columns=cols)

    # Create csv file
    csv_name = model_name + "-global-losses.csv"
    csv_file = params["model_path"] + csv_name

    # Write csv file
    df.to_csv(csv_file, index=False)

    model = params["model"]
    num_epochs = params["num_epochs"]

    dataloaders = params["dataloaders"]
    train_loader = dataloaders["train"]
    valid_loader = dataloaders["valid"]

    # Create list metrics
    train_losses = []
    train_mious = []
    val_losses = []
    val_mious = []

    # Training and evaluation model
    for epoch in range(num_epochs):

        epoch += 1

        # Create CUDA Events to estimate training time
        start_train = cuda.Event(enable_timing=True)
        end_train = cuda.Event(enable_timing=True)

        # Getting train losses
        params["dataloader"] = train_loader

        # Start training
        model.train()
        start_train.record()
        model, train_loss, train_miou = one_epoch(params, True)
        end_train.record()

        # Waits for everything to finish running
        cuda.synchronize()

        # Calculate total time per epoch
        epoch_time = start_train.elapsed_time(end_train)

        # Rounding with four precision
        epoch_time = round(epoch_time, 4)

        # Getting valid losses
        model.eval()
        params["dataloader"] = valid_loader
        val_loss, val_miou = one_epoch(params, False)

        # Adding losses
        train_losses.append(train_loss)
        val_losses.append(val_loss)

        # Adding mious
        train_miou = train_miou.item() if isinstance(train_miou, torch.Tensor) else train_miou
        val_miou = val_miou.item() if isinstance(val_miou, torch.Tensor) else val_miou

        train_mious.append(train_miou)
        val_mious.append(val_miou)

        # Create new df and add data
        df = pd.DataFrame([[epoch, epoch_time,
                            train_loss, val_loss]], columns=cols)

        # Write to csv file
        df.to_csv(csv_file, mode='a', header=False, index=False)

        train_loss = round(train_loss, 4)

        # Range of mIoU (0-100%)
        train_miou = train_miou * 100
        train_miou = round(train_miou, 1)

        val_loss = round(val_loss, 4)

        # Range of mIoU (0-100%)
        val_miou = val_miou * 100
        val_miou = round(val_miou, 1)

        print(f'|Epoch {epoch} | Val loss {val_loss} | Val mIoU {val_miou}')
        print(f'|Epoch {epoch} | Train loss {train_loss} | Train mIoU {train_miou}')
        print()

    dict_losses = {}
    dict_losses["train_losses"] = train_losses
    dict_losses["train_mious"] = train_mious
    dict_losses["val_losses"] = val_losses
    dict_losses["val_mious"] = val_mious

    return dict_losses


def testing(params, val=False):

    dataloaders = params["dataloaders"]

    if val:
        params["dataloader"] = dataloaders["valid"]
    else:
        params["dataloader"] = dataloaders["test"]

    # Getting epoch metrics
    loss, miou = one_epoch(params, False)

    if torch.is_tensor(loss):
        loss = torch.max(loss)
    else:
        loss = round(loss, 4)

    if torch.is_tensor(miou):
        miou *= 100
        miou = torch.max(miou)
    else:
        miou *= 100
        miou = round(miou, 1)

    if val:
        print(f'| Val Loss {loss}, mIoU {miou}\n')
    else:
        print(f'| Test Loss {loss}, mIoU {miou}\n')

    return loss, miou


def semantic_inference(output, color_code):
    print('[DEBUG] Semantic Inference (function)')
    print(output.shape)
    sys.exit()

    # Removing batch size
    output = output.squeeze()

    # Sending results to CPU
    output = output.detach().cpu().numpy()

    # Applying transpose
    output = output.transpose((2, 1, 0))

    # Applying mask to rgb
    output = mask_to_rgb(output, color_code)

    # Applying transpose
    output = output.transpose((2, 1, 0))

    # # Convert to numpy array and denormalize
    # output = output * 255.0
    # output = output.transpose(1, 2, 0)

    # # Convert back to tensor and change data type
    # output = torch.from_numpy(output)
    # output = output.permute(2, 0, 1)
    # output = output.to(torch.uint8)

    return output


def inference_evaluation(img, color_code, model, device):

    # Adding dummy batch 1 size
    img = img.unsqueeze(dim=0)

    # Send to device
    img = img.to(device)

    # Casting
    img = img.float()

    # Send model to device
    model = model.to(device)

    # Inference
    out = model(img)

    # Getting semantic inference of the model
    out = semantic_inference(out, color_code)

    return out


def evaluation(dataloader, model, color_code, num_classes=32):

    # First we need to valid if is a DataLoader PyTorch Object
    if not isinstance(dataloader, torch.utils.data.DataLoader):
        raise ValueError("[ERROR] The data have to be a DataLoader object")

    # Check if dataloader batch size is 1
    if dataloader.batch_size != 1:
        raise ValueError("[ERROR] The batch size of the DataLoader \
                         have to be 1")

    # Creating the loop
    loop = tqdm(dataloader, leave=True,
                desc="[INFO] Semantic Segmentation Inferences")

    # Get the number of classes of the dataset
    # ????

    # Setting test mode
    model.eval()

    # Inference loop
    semantic_results = []

    for batch_idx, data in enumerate(loop):

        # Extract data
        img, gt, mask = data

        # Save original imgs and masks
        results = [img.numpy().squeeze().transpose(1, 2, 0),
                   mask.numpy().squeeze().transpose(1, 2, 0)]

        # Send img to device
        img = img.to("cuda")

        # Casting
        img = img.float()

        # Send gt to device
        gt = gt.to("cuda")

        # Model Logits output
        logits = model(img)

        # Convert predictions to class labels
        pred = logits.argmax(dim=1).unsqueeze(1).expand(-1, logits.shape[1], -1, -1).reshape(logits.shape)

        # Get binary mask prediction of the model
        pred_mask = batch_binary_mask(img.cpu().numpy(),
                                      pred.cpu().numpy(), num_classes)

        # Compute mIoU
        miou = compute_mIoU(pred_mask.cuda(), gt.cuda(), num_classes)

        # Convert classes output to rgb output
        pred_mask = mask_to_rgb(pred_mask.numpy().squeeze(), color_code)

        # Save mIoU
        results.extend([miou])

        # Save model prediction
        results.extend([pred_mask.squeeze()])

        # Save complete results
        semantic_results.append(results)

    return semantic_results


def map_results(results, n_results=4):

    # Extract all mious in order to map the results
    mious = [result[-2] for result in results]

    # Map inference results based on its mIoU
    best_idxs = get_results(mious,
                            results_type="best", n_results=n_results)
    best_res = [results[i] for i in best_idxs]

    worst_idxs = get_results(mious,
                             results_type="worst", n_results=n_results)
    worst_res = [results[i] for i in worst_idxs]

    random_idxs = get_results(mious,
                              results_type="random", n_results=n_results)
    random_res = [results[i] for i in random_idxs]

    return {"best": best_res, "worst": worst_res, "random": random_res}


def load_ckp(ckp_cfg, mode, strict=True):

    # getting all stuff
    model = ckp_cfg["model"]
    model_ckp = ckp_cfg["model_ckp"]

    # Train mode
    if mode:

        optimizer = ckp_cfg["optimizer"]

        # Freeze parameters
        for param in model.parameters():
            param.requires_grad = True

        # Loading model checkpoint
        model_ckp = torch.load(model_ckp, map_location="cpu")

        # Loading class to idx
        # TODO: Check this shit
        # model.class_id_to_name = model_ckp['class_id_to_name']

        # Getting state model dict
        weights_model = model_ckp["model_state_dict"]
        model.load_state_dict(weights_model, strict=strict)
        model.train()

        # Getting optimizer state
        optimizer.load_state_dict(model_ckp["optimizer_state_dict"])

        # Getting loss function
        loss_fn = model_ckp["loss_fn"]

        return model, optimizer, loss_fn

    else:
        # Freeze parameters
        for param in model.parameters():
            param.requires_grad = False

        # Loading model checkpoint
        model_ckp = torch.load(model_ckp, map_location="cpu")

        # Getting state model dict
        weights_model = model_ckp["model_state_dict"]
        model.load_state_dict(weights_model, strict=strict)
        model.eval()

        return model


def get_lr_decay_factor(init_lr, final_lr, num_epochs):
    return (final_lr / init_lr) ** (1 / num_epochs)
