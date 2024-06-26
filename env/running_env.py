from env import yaml2args
from env.support_config import VModel
from utils.PathManager import PathManager
from utils.VContainer import VContainer
from utils.Vlogger import VLogger
from custom_path import *


# Args
args = yaml2args.ArgRepo(test_config)
args.activate()

### 
# Pre Default Env
###

# base static path
milestone_base = r'res/milestone'
image_base = r'res/images'
exp_base = r'res/exp'
non_iid_base = r'res/non_iid'
log_base = r'logs'

if args.model == VModel.VGG16:
    model_path = vgg16_model
elif args.model == VModel.ResNet56:
    model_path = resnet56_model
elif args.model == VModel.ResNet110:
    model_path = resnet110_model
elif args.model == VModel.MobileNetV2:
    model_path = mobilenetv2_model
elif args.model == VModel.Conv2:
    model_path = conv2_model
elif args.model == VModel.ShuffleNetV2:
    model_path = shufflenetv2_model
else:
    model_path = vgg16_model
    print('Not supported model type.')
    exit(1)

### 
# Dynamic Env
###

# Path
global_file_repo = PathManager(model_path, datasets_base, non_iid_base)
global_file_repo.derive_path(exp_base, image_base, milestone_base, log_base)


# Logger
# global_logger_PATH = "logs/hrankFL.log"
logger_path, _ = global_file_repo.new_log()
global_logger = VLogger(logger_path, True).logger

# Container
global_container = VContainer()
