from detectron2.engine import DefaultPredictor
from detectron2.data import MetadataCatalog
from detectron2.config import get_cfg
#from google.colab.patches import cv2_imshow
import os
import cv2
import numpy as np

from skimage import io

from re import I
from PIL import Image

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

#predict from your pic

def cloth_seg(image):
  i = io.imread(image)
  i = cv2.resize(i, dsize=(300, 450), interpolation=cv2.INTER_AREA)
  
  out = predictor(i)
  
  # crop img
  masks = np.asarray(out["instances"].pred_masks.to("cpu"))
  
  top_dict = {}
  bot_dict = {}

  for j in range(masks.shape[0]):
    item_mask = masks[j]
  
    segmentation = np.where(item_mask == True)
    x_min = int(np.min(segmentation[1]))
    x_max = int(np.max(segmentation[1]))
    y_min = int(np.min(segmentation[0]))
    y_max = int(np.max(segmentation[0]))
    # print(x_min, y_min,x_max, y_max)
  
    cropped = Image.fromarray(i[y_min:y_max, x_min:x_max, :], 
    mode='RGB')
  
    mask = Image.fromarray((item_mask * 255).astype('uint8'))
  
  
    cropped_mask = mask.crop((x_min, y_min, x_max, y_max))
    bg = np.full((450, 300, 3), 255, np.uint8)
    # bg = np.zeros((450, 300, 3), np.uint8)
    background = Image.fromarray(bg, mode='RGB')
    paste_position = (100,150)
  
    new_fg_image = Image.new('RGB', background.size)
    new_fg_image.paste(cropped, paste_position)
  
    new_alpha_mask = Image.new("L", background.size, color = 0)
    new_alpha_mask.paste(cropped_mask, paste_position)
  
    composite = Image.composite(new_fg_image, background,     
    new_alpha_mask)


    #cv2.imshow(np.array(composite))
    item_num = out['instances'].pred_classes[j].item()
    if item_num == 4 or item_num == 5 or item_num == 8 or item_num == 9:     # 4:outer, 5:dress, 8: top, 9: shorts
      if item_num == 4:
        top_dict["outer"] = np.array(composite)[:,:,::-1]
      elif item_num == 5:
        top_dict["dress"] = np.array(composite)[:,:,::-1]
      elif item_num == 8:
        top_dict["top"] = np.array(composite)[:,:,::-1]      
      else:
        top_dict["shorts"] = np.array(composite)[:,:,::-1]
      #cv2.imwrite(f"data/images_output/top/top{j}.jpg",   
    #np.array(composite)[:,:,::-1])
      #print(f"data/images_output/top/top{j}.jpg")
    elif item_num == 7 or item_num == 10:     #   
      if item_num == 7:
        bot_dict["pants"] = np.array(composite)[:,:,::-1]
      else:
        bot_dict["skirt"] = np.array(composite)[:,:,::-1]
    #   cv2.imwrite(f"data/images_output/bottom/bottom{j}.jpg", 
    # np.array(composite)[:,:,::-1])
    #   print(f"data/images_output/bottom/bottom{j}.jpg")
  return top_dict, bot_dict

