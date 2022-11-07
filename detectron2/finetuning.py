# You may need to restart your runtime prior to this, to let your installation take effect
# Some basic setup
# Setup detectron2 logger
import detectron2
from detectron2.utils.logger import setup_logger
setup_logger()

# import some common libraries
import matplotlib.pyplot as plt
import numpy as np
import cv2
from google.colab.patches import cv2_imshow

# import some common detectron2 utilities
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2.utils.visualizer import Visualizer
from detectron2.data import MetadataCatalog, DatasetCatalog

# coco 데이터셋에 cloth 객체instance를 추가해준다.
from detectron2.data.datasets import register_coco_instances
register_coco_instances("cloth", {}, "./data/trainval.json", "./data/images")
cloth_metadata = MetadataCatalog.get("cloth")
dataset_dicts = DatasetCatalog.get("cloth")

# Now, let's fine-tune a coco-pretrained R50-FPN Mask R-CNN model on the cloth dataset. It takes ~6 minutes to train 300 iterations on Colab's K80 GPU.
from detectron2.engine import DefaultTrainer
from detectron2.config import get_cfg
import os

cfg = get_cfg()
# cfg.merge_from_file("./detectron2_repo/configs/COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml")
cfg.merge_from_file("./detectron2_repo/configs/COCO-InstanceSegmentation/mask_rcnn_R_101_FPN_3x.yaml")
cfg.DATASETS.TRAIN = ("cloth",)
cfg.DATASETS.TEST = ()   # no metrics implemented for this dataset
cfg.DATALOADER.NUM_WORKERS = 2
# cfg.MODEL.WEIGHTS = "detectron2://COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x/137849600/model_final_f10217.pkl"  # initialize from model zoo
cfg.MODEL.WEIGHTS = "detectron2://COCO-InstanceSegmentation/mask_rcnn_R_101_FPN_3x/138205316/model_final_a3ec72.pkl"  # initialize from model zoo

cfg.SOLVER.IMS_PER_BATCH = 2
cfg.SOLVER.BASE_LR = 0.002
cfg.SOLVER.MAX_ITER = 300    # 300 iterations seems good enough, but you can certainly train longer
# cfg.MODEL.ROI_HEADS.BATCH_SIZE_PER_IMAGE = 128   # faster, and good enough for this toy dataset
cfg.MODEL.ROI_HEADS.BATCH_SIZE_PER_IMAGE = 640 
cfg.MODEL.ROI_HEADS.NUM_CLASSES = 13  # 13 classes (cloth)

os.makedirs(cfg.OUTPUT_DIR, exist_ok=True)
trainer = DefaultTrainer(cfg)
#trainer.resume_or_load(resume=False)
trainer.resume_or_load(resume=True)
trainer.train()

#Now, we perform inference with the trained model on the cloth dataset. First, let's create a predictor using the model we just trained:
cfg.MODEL.WEIGHTS = os.path.join(cfg.OUTPUT_DIR, "model_final.pth")
cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5 # set the testing threshold for this model
cfg.DATASETS.TEST = ("cloth", )
predictor = DefaultPredictor(cfg)

#predict from url
from skimage import io

# insert your url
i = io.imread('https://img1.daumcdn.net/thumb/R720x0/?fname=https://t1.daumcdn.net/news/201803/20/SpoHankook/20180320023600919jqsb.jpg')
i = cv2.resize(i, dsize=(300, 450), interpolation=cv2.INTER_AREA)

out = predictor(i)
v = Visualizer(i[:, :, ::-1],
                metadata=cloth_metadata, 
                scale=0.8
                # instance_mode=ColorMode.IMAGE_BW   # remove the colors of unsegmented pixels
    )
v = v.draw_instance_predictions(out["instances"].to("cpu"))
cv2_imshow(v.get_image()[:, :, ::])


# crop img
from re import I
from PIL import Image

masks = np.asarray(out["instances"].pred_masks.to("cpu"))

for j in range(masks.shape[0]):
  item_mask = masks[j]

  segmentation = np.where(item_mask == True)
  x_min = int(np.min(segmentation[1]))
  x_max = int(np.max(segmentation[1]))
  y_min = int(np.min(segmentation[0]))
  y_max = int(np.max(segmentation[0]))
  # print(x_min, y_min,x_max, y_max)

  cropped = Image.fromarray(i[y_min:y_max, x_min:x_max, :], mode='RGB')

  mask = Image.fromarray((item_mask * 255).astype('uint8'))


  cropped_mask = mask.crop((x_min, y_min, x_max, y_max))
  bg = np.full((450, 300, 3), 255, np.uint8) # 흰색배경
  # bg = np.zeros((450, 300, 3), np.uint8) # 검정색 배경
  background = Image.fromarray(bg, mode='RGB')
  paste_position = (100,150)

  new_fg_image = Image.new('RGB', background.size)
  new_fg_image.paste(cropped, paste_position)

  new_alpha_mask = Image.new("L", background.size, color = 0)
  new_alpha_mask.paste(cropped_mask, paste_position)

  composite = Image.composite(new_fg_image, background, new_alpha_mask)


  composite_array = np.array(composite)
  nonzero_composite_array = np.nonzero(composite_array)
  np_av = np.average(nonzero_composite_array)
  print(np_av)
 


  cv2_imshow(np.array(composite))
  item_num = out['instances'].pred_classes[j].item()
  if item_num == 4 or item_num == 5 or item_num == 8 or item_num == 9:
    cv2.imwrite(f"data/images_output/top/top{j}.png", np.array(composite))
  elif item_num == 7 or item_num == 10:
    cv2.imwrite(f"data/images_output/bottom/bottom{j}.png", np.array(composite))
  else:
    cv2.imwrite(f"data/images_output/others/others{j}.png", np.array(composite))
