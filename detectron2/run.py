from detectron2.engine import DefaultPredictor
from detectron2.data import MetadataCatalog
from detectron2.config import get_cfg
from google.colab.patches import cv2_imshow
import os
import cv2
import numpy as np

cloth_metadata = MetadataCatalog.get("cloth")
# dataset_dicts = DatasetCatalog.get("cloth")
cfg = get_cfg()

cfg.merge_from_file("./detectron2_repo/configs/COCO-InstanceSegmentation/mask_rcnn_R_101_FPN_3x.yaml")
# cfg.MODEL.WEIGHTS = "detectron2://COCO-InstanceSegmentation/mask_rcnn_R_101_FPN_3x/138205316/model_final_a3ec72.pkl"  # initialize from model zoo

cfg.MODEL.WEIGHTS = os.path.join(cfg.OUTPUT_DIR, "model_final.pth")

cfg.MODEL.ROI_HEADS.BATCH_SIZE_PER_IMAGE = 640 
cfg.MODEL.ROI_HEADS.NUM_CLASSES = 13  # 13 classes (cloth)

cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5 # set the testing threshold for this model
# cfg.DATASETS.TEST = ("cloth", )
predictor = DefaultPredictor(cfg)

#predict from url
from skimage import io

url = input("해당 사진의 url을 입력하시오 :")
i = io.imread(url)
i = cv2.resize(i, dsize=(300, 450), interpolation=cv2.INTER_AREA)

out = predictor(i)


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
    cv2.imwrite(f"data/images_output/top/top{j}.png", np.array(composite)[:,:,::-1])
    print(f"data/images_output/top/top{j}.png")
  elif item_num == 7 or item_num == 10:
    cv2.imwrite(f"data/images_output/bottom/bottom{j}.png", np.array(composite)[:,:,::-1])
    print(f"data/images_output/bottom/bottom{j}.png")
  else:
    cv2.imwrite(f"data/images_output/others/others{j}.png", np.array(composite)[:,:,::-1])
    print(f"data/images_output/others/others{j}.png")
