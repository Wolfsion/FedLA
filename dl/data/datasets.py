import sys
import os
from os.path import join
from PIL import Image
import torchvision.datasets
import urllib.request
import zipfile
from torch.utils.data import Dataset
from torchvision import transforms

from dl.data.transform import init_transform, init_target_transform, init_tiny_imagenet_transform
from env.static_env import CIFAR10_MEAN, CIFAR10_STD, CIFAR10_CLASSES, \
    CIFAR100_MEAN, CIFAR100_STD, CIFAR100_CLASSES, FMNIST_CLASSES, TinyImageNet_CLASSES, EMNIST_CLASSES
from env.support_config import VDataSet
from env.running_env import global_file_repo


class TinyImageNet(Dataset):
    def __init__(self, root, train=True,
                 transform=None, target_transform=None):
        self.Train = train
        self.root_dir = os.path.expanduser(root)
        self.transform = transform
        self.target_transform = target_transform
        self.train_dir = os.path.join(self.root_dir, "train")
        self.val_dir = os.path.join(self.root_dir, "val")

        if self.Train:
            self._create_class_idx_dict_train()
        else:
            self._create_class_idx_dict_val()

        self._make_dataset(self.Train)

        words_file = os.path.join(self.root_dir, "words.txt")
        wnids_file = os.path.join(self.root_dir, "wnids.txt")

        self.set_nids = set()

        with open(wnids_file, 'r') as fo:
            data = fo.readlines()
            for entry in data:
                self.set_nids.add(entry.strip("\n"))

        self.class_to_label = {}
        with open(words_file, 'r') as fo:
            data = fo.readlines()
            for entry in data:
                words = entry.split("\t")
                if words[0] in self.set_nids:
                    self.class_to_label[words[0]] = (words[1].strip("\n").split(","))[0]

        self.targets = [item[1] for item in self.images]

    def _create_class_idx_dict_train(self):
        if sys.version_info >= (3, 5):
            classes = [d.name for d in os.scandir(self.train_dir) if d.is_dir()]
        else:
            classes = [d for d in os.listdir(self.train_dir) if os.path.isdir(os.path.join(self.train_dir, d))]
        classes = sorted(classes)
        num_images = 0
        for root, dirs, files in os.walk(self.train_dir):
            for f in files:
                if f.endswith(".JPEG"):
                    num_images = num_images + 1

        self.len_dataset = num_images

        self.tgt_idx_to_class = {i: classes[i] for i in range(len(classes))}
        self.class_to_tgt_idx = {classes[i]: i for i in range(len(classes))}

    def _create_class_idx_dict_val(self):
        val_image_dir = os.path.join(self.val_dir, "images")
        if sys.version_info >= (3, 5):
            images = [d.name for d in os.scandir(val_image_dir) if d.is_file()]
        else:
            images = [d for d in os.listdir(val_image_dir) if os.path.isfile(os.path.join(self.train_dir, d))]
        val_annotations_file = os.path.join(self.val_dir, "val_annotations.txt")
        self.val_img_to_class = {}
        set_of_classes = set()
        with open(val_annotations_file, 'r') as fo:
            entry = fo.readlines()
            for data in entry:
                words = data.split("\t")
                self.val_img_to_class[words[0]] = words[1]
                set_of_classes.add(words[1])

        self.len_dataset = len(list(self.val_img_to_class.keys()))
        classes = sorted(list(set_of_classes))
        # self.idx_to_class = {i:self.val_img_to_class[images[i]] for i in range(len(images))}
        self.class_to_tgt_idx = {classes[i]: i for i in range(len(classes))}
        self.tgt_idx_to_class = {i: classes[i] for i in range(len(classes))}

    def _make_dataset(self, Train=True):
        self.images = []
        if Train:
            img_root_dir = self.train_dir
            list_of_dirs = [target for target in self.class_to_tgt_idx.keys()]
        else:
            img_root_dir = self.val_dir
            list_of_dirs = ["images"]

        for tgt in list_of_dirs:
            dirs = os.path.join(img_root_dir, tgt)
            if not os.path.isdir(dirs):
                continue

            for root, _, files in sorted(os.walk(dirs)):
                for fname in sorted(files):
                    if fname.endswith(".JPEG"):
                        path = os.path.join(root, fname)
                        if Train:
                            item = (path, self.class_to_tgt_idx[tgt])
                        else:
                            item = (path, self.class_to_tgt_idx[self.val_img_to_class[fname]])
                        self.images.append(item)

    def return_label(self, idx):
        return [self.class_to_label[self.tgt_idx_to_class[i.item()]] for i in idx]

    def __len__(self):
        return self.len_dataset

    def __getitem__(self, idx):
        img_path, tgt = self.images[idx]
        with open(img_path, 'rb') as f:
            sample = Image.open(img_path)
            sample = sample.convert('RGB')
        if self.transform is not None:
            sample = self.transform(sample)
        if self.target_transform is not None:
            tgt = self.target_transform(tgt)
        return sample, tgt


def get_data(dataset: VDataSet, data_type, transform=None, target_transform=None):
    if dataset == VDataSet.CIFAR10:
        assert data_type in ["train", "test"]
        if transform is None:
            transform = init_transform(data_type, CIFAR10_MEAN, CIFAR10_STD)
        if target_transform is None:
            target_transform = init_target_transform(CIFAR10_CLASSES)
        return torchvision.datasets.CIFAR10(root=join(global_file_repo.dataset_path, "CIFAR10"),
                                            train=data_type == "train", download=True,
                                            transform=transform,
                                            target_transform=target_transform)
    elif dataset == VDataSet.CIFAR100:
        assert data_type in ["train", "test"]
        if transform is None:
            transform = init_transform(data_type, CIFAR100_MEAN, CIFAR100_STD)
        if target_transform is None:
            target_transform = init_target_transform(CIFAR100_CLASSES)
        return torchvision.datasets.CIFAR100(root=join(global_file_repo.dataset_path, "CIFAR100"),
                                             train=data_type == "train", download=True,
                                             transform=transform,
                                             target_transform=target_transform)
    elif dataset == VDataSet.FMNIST:
        assert data_type in ["train", "test"]
        if transform is None:
            transform = transforms.Compose([
                transforms.ToTensor(),
                transforms.Normalize(mean=0.5, std=0.5)])
        if target_transform is None:
            target_transform = init_target_transform(FMNIST_CLASSES)
        return torchvision.datasets.FashionMNIST(root=join(global_file_repo.dataset_path, "FMNIST"),
                                                 train=data_type == "train",
                                                 transform=transform, target_transform=target_transform,
                                                 download=True)
    elif dataset == VDataSet.TinyImageNet:
        assert data_type in ["train", "test", "val"]
        if transform is None:
            transform = init_tiny_imagenet_transform()
        if target_transform is None:
            target_transform = init_target_transform(TinyImageNet_CLASSES)
        # r"C:\\Users\<your_name>\la\datasets\tiny-imagenet-200"
        return TinyImageNet(root=join(global_file_repo.dataset_path, "tiny-imagenet-200"),
                            train=data_type == "train",
                            transform=transform,
                            target_transform=target_transform)
    elif dataset == VDataSet.EMNIST:
        assert data_type in ["train", "test"]
        if transform is None:
            transform = transforms.Compose([
                transforms.ToTensor(),
                transforms.Normalize(mean=0.5, std=0.5)])
        if target_transform is None:
            target_transform = init_target_transform(EMNIST_CLASSES)
        return torchvision.datasets.EMNIST(root=join(global_file_repo.dataset_path, "EMNIST"),
                                           split='byclass', download=True, train=data_type == "train",
                                           transform=transform, target_transform=target_transform)
    else:
        raise ValueError("{} dataset is not supported.".format(dataset))


def download_datasets():
    torchvision.datasets.CIFAR10(root='~/la/datasets/CIFAR10',
                                 train=True, download=True)
    torchvision.datasets.FashionMNIST(root="~/la/datasets/FMNIST", train=True,
                                      download=True)
    torchvision.datasets.CIFAR100(root="~/la/datasets/CIFAR100", train=True,
                                  download=True)
    torchvision.datasets.EMNIST(root="~/la/datasets/EMNIST", train=True, split='byclass',
                                download=True)

    # tiny imagenet
    # http://cs231n.stanford.edu/tiny-imagenet-200.zip

    url = "http://cs231n.stanford.edu/tiny-imagenet-200.zip"
    file_name = "tinyimagenet.zip"
    urllib.request.urlretrieve(url, file_name)

    extract_dir = "~/la/datasets"
    with zipfile.ZipFile(file_name, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)


def test_emnist():
    emnist_data = torchvision.datasets.EMNIST(
        root="~/la/datasets/EMNIST",
        split='byclass',
        train=True, download=True, transform=torchvision.transforms.ToTensor())
