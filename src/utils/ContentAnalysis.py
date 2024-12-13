import pandas as pd
import jieba
import jieba.posseg as pseg
import os
from tqdm import tqdm

jieba_path = os.path.dirname(jieba.__file__)
dict_path = os.path.join(jieba_path, 'dict.txt.big')

if os.path.exists(dict_path):
    jieba.set_dictionary(dict_path)
    print("成功設置繁體字典")
else:
    print(f"錯誤：在 {dict_path} 找不到字典文件")

current_dir = os.path.dirname(os.path.abspath(__file__))  # 獲取當前文件的目錄
user_dict_path = os.path.join(current_dir, "stock_dict.txt")  # 拼接 stock_dict.txt 的完整路徑

if os.path.exists(user_dict_path):
    jieba.load_userdict(user_dict_path)
    print("自訂字典載入成功")
else:
    print(f"錯誤：找不到自訂字典，預期路徑為 {user_dict_path}")

def extract_companies(text):
    words = pseg.cut(text)
    companies = [word for word, flag in words if flag == 'stock']  # 'stock' 表示股票名稱
    companies = pd.unique(companies)
    return companies

def extract_keywords(text):
    words = pseg.cut(text)
    companies = [word for word, flag in words if flag == 'trend']  # 'stock' 表示股票名稱
    companies = pd.unique(companies)
    return companies

def analysis() :
    pass

# 讀取 CSV 文件
csv_path = os.path.join(current_dir, "technews_articles_content_copy.csv")
if os.path.exists(csv_path):
    df = pd.read_csv(csv_path)
else:
    print(f"錯誤：找不到 CSV 檔案，預期路徑為 {csv_path}")

# 使用 progress_apply 來顯示進度條
tqdm.pandas(desc="Processing")
df['Companies_Content'] = df['Content'].iloc[0:10].progress_apply(extract_companies)
df['Trend'] = df['Content'].iloc[0:10].progress_apply(extract_keywords)

print( df['Companies_Content'].iloc[0:10] )
print( df['Trend'].iloc[0:10] )
print("處理完成！")