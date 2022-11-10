from feature_extractor import FeatureExtractor
import pymysql as pysql
from pathlib import Path

import numpy as np
import pandas as pd


# Reading img features
def load_img_list():
    '''
    local에 저장된 .npy 디렉토리에서 특징들을 뽑아와 numpy array로,
    DB에 담긴 image path와 하이퍼링크를 가져와 dataframe 형태로 반환해주는 함수
    [return]
    features_top : numpy.array -> .npy에서 읽어온 top부분 특징
    features_bottom : numpy.array -> .npy에서 읽어온 bottom부분 특징
    result : numpy.array -> DB에서 읽어온 image path와 하이퍼링크 주소. dataframe 형태
    '''
    
    # 추출된 특징들을 pandas에 담아서 정리
    features_top = []
    features_bottom = []
    
    for feature_path in sorted(Path("./static/feature_top").glob("*.npy")):
        features_top.append(np.load(feature_path))
    features_top = np.array(features_top)

    for feature_path in sorted(Path("./static/feature_bottom").glob("*.npy")):
        features_bottom.append(np.load(feature_path))
    features_bottom = np.array(features_bottom)
    
    # DB에서 table 가져와서 pandas에 담기
    sql_top = "select * from imgs_top"
    sql_bottom = "select * from imgs_bottom"
    
    conn = pysql.connect(host="db-3team-project.ckirsmdzwudh.ap-northeast-2.rds.amazonaws.com",
                        port=3306,
                        user="admin",
                        password="rladbdbsDL!",
                        db="security",
                        charset="utf8")
    
    result_top = pd.read_sql_query(sql_top, conn)    
    result_bottom = pd.read_sql_query(sql_bottom, conn)    

    result_top['path_url'] = "https://image-storage01.s3.ap-northeast-2.amazonaws.com/" + result_top['name']
    result_bottom['path_url'] = "https://image-storage01.s3.ap-northeast-2.amazonaws.com/" + result_bottom['name']

    result_top = result_top.sort_values('name')
    result_bottom = result_bottom.sort_values('name')

    return features_top, features_bottom, result_top, result_bottom
    
load_img_list()
