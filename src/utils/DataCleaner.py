import pandas as pd
import re

def clean_text(text):
    if pd.isna(text):
        return text
    text = re.sub(r'\s+', ' ', text).strip()
    # 這裡可以添加其他文本清理步驟，例如移除特殊字符等
    return text

def clean_data( df ):

    # 替換爬蟲中的默認值
    df = df.replace({
        "標題未找到": pd.NA,
        "日期未找到": pd.NA,
        "作者未找到": pd.NA,
        "內容未找到": pd.NA
    })

    # 轉換日期格式
    df['Date'] = pd.to_datetime(df['Date'], format='%Y 年 %m 月 %d 日 %H:%M', errors='coerce')

    # 應用清理函數到 'Title' 和 'Content' 列
    df['Title'] = df['Title'].apply(clean_text)
    df['Content'] = df['Content'].apply(clean_text)

    # 規範化作者名稱
    df['Author'] = df['Author'].str.strip()

    return df