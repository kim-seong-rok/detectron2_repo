import numpy as np
from PIL import Image
from feature_extractor import FeatureExtractor
from datetime import datetime
from flask import Flask, request, render_template
from flask_cors import CORS
from flask_restful import Api
import flask
import base64
import cv2
from data_list import load_img_list
from img_crawling import naver_crawling
import schedule
import time
import running
import json

### 원본 코드 ###
# app = Flask(__name__)

# # Reading img features
# fe = FeatureExtractor()
# features = []
# img_paths = []

# for feature_path in Path("./static/feature").glob("*.npy"):
#     features.append(np.load(feature_path))
#     img_paths.append(Path("./static/img") / (feature_path.stem + ".jpg"))
# features = np.array(features)

# @app.route("/", methods=["GET", "POST"])
# def index():
#     if request.method == "POST":
#         file = request.files["query_img"]
        
#         # Save query img
#         img = Image.open(file.stream) # PIL image
#         uploaded_img_path = "static/uploaded/" + datetime.now().isoformat().replace(":", ".") + "_" + file.filename
#         img.save(uploaded_img_path)
        
#         # Run Search
#         query = fe.extract(img)
#         dists = np.linalg.norm(features - query, axis=1) # L2 distance to the features
#         ids = np.argsort(dists)[:30]    # Top 30 results
#         scores = [(dists[id], img_paths[id]) for id in ids]
        
#         print(scores)
        
#         return render_template("index.html", query_path=uploaded_img_path, scores=scores)
#     else:
#         return render_template("index.html")

# if __name__=="__main__":
#     app.run()
     
### 여기까지 ###




app = Flask(__name__)
CORS(app, supports_credentials=True) # 다른 포트번호에 대한 보안 제거
api = Api(app)

# Reading img features
fe = FeatureExtractor()

features_top, features_bottom, df_top, df_bottom = load_img_list()

@app.route("/upload", methods=["POST"])
def upload():
    if request.method == "POST":
        file = request.get_json()["file"].split(",")[1]
        
        decoded_file = base64.b64decode(file)
        
        img_np = np.fromstring(decoded_file, dtype=np.uint8)
        
        img = cv2.imdecode(img_np, flags=cv2.IMREAD_COLOR)
        
        # img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # img = Image.fromarray(img.astype('uint8'))
        
        # img.show() 
        
        # image_parsing {"outer" : [np.array, ...], "shortsleeve" : [np.array, ...], }
        array_top, array_bottom = running.cloth_seg(img)
        dict_top = {}
        dict_bottom = {}
        
        if array_top:
            for key in array_top.keys():
                img_top = Image.fromarray(array_top.get(key).astype('uint8'))
                
                # Run Search
                query_top = fe.extract(img_top)
                dists_top = np.linalg.norm(features_top - query_top, axis=1)
                ids_top = np.argsort(dists_top)[:100] # top result sort
                
                result_img_path_top = [df_top.iloc[id]['path_url'] for id in ids_top]
                result_img_link_top = [df_top.iloc[id]['url'] for id in ids_top]
                result_img_score_top = [float(dists_top[id]) for id in ids_top] # float32 타입으로 되어 있는 것을 float 타입으로 바꿔주어야지 json으로 변경 가능. 리스트에 있어도 마찬가지
                
                dict_top[key] = {"result_img_path_top" : result_img_path_top,
                                "result_img_link_top" : result_img_link_top,
                                "result_img_score_top" : result_img_score_top}
        
            
        if array_bottom:
            for key in array_bottom.keys():
                img_bottom = Image.fromarray(array_bottom.get(key).astype('uint8'))
            
                # Run Search
                query_bottom = fe.extract(img_bottom)
                dists_bottom = np.linalg.norm(features_bottom - query_bottom, axis=1)
                ids_bottom = np.argsort(dists_bottom)[:100] # top result sort
                
                result_img_path_bottom = [df_bottom.iloc[id]['path_url'] for id in ids_bottom]
                result_img_link_bottom = [df_bottom.iloc[id]['url'] for id in ids_bottom]
                result_img_score_bottom = [float(dists_bottom[id]) for id in ids_bottom] # float32 타입으로 되어 있는 것을 float 타입으로 바꿔주어야지 json으로 변경 가능. 리스트에 있어도 마찬가지
                
                dict_bottom[key] = {"result_img_path_bottom" : result_img_path_bottom,
                                                "result_img_link_bottom" : result_img_link_bottom,
                                                "result_img_score_bottom" : result_img_score_bottom}
        
        
        return flask.jsonify({"result" : "true",
                              "number_of_top_category" : str(len(array_top)),
                              "top" : dict_top,
                              "number_of_bottom_category" : str(len(array_bottom)),
                              "bottom" : dict_bottom})
    else:
        return flask.jsonify({"result" : "false"})
    

if __name__=="__main__":
    # app.run(host=0.0.0.0, port=5000) 모든 호스트로 접속 가능.
    app.run()
    
    # # 크롤링 자동화
    # schedule.every().wednesday.at("15:06").do(naver_crawling)
    # while True:
    #     schedule.run_pending()
    #     time.sleep(1)
