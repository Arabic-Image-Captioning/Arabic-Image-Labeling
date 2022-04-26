import streamlit as st
import pandas as pd
import numpy as np
import glob
import os
import requests
from io import BytesIO
from PIL import Image
from streamlit import image
from cairosvg import svg2png
from pathlib import Path

#

st.set_page_config(
    initial_sidebar_state="expanded",
    page_title="AIT Labeling"
)

st.title('AIT Labeling')

#url_gs = 'https://storage.googleapis.com'


def load_data_pd(path,split='train',data_type='csv'):
    data = pd.read_csv(path)
    # remove columns
    org_columns = data.columns
    data=data.drop(set(org_columns) - {'Image_name', 'Caption'}, axis=1)

    return data


def load_image(url,image_index):

    # download image from url and show it in streamlit
    if '.svg' in image_index:
        png = svg2png(url=url)
        image = Image.open(BytesIO(png)).convert('RGBA')
    else:
        image = Image.open(BytesIO(requests.get(url).content))


    return image

def filter_by_length(data,length):
    # filter data by length
    data = data[data['Caption'].str.len() < length].reset_index(level=None, drop=False, inplace=False, col_level=0, col_fill='')
    return data

def drop_arabic(data):
    # drop arabic text
    data = data[data['Caption'].str.contains('[أ-ي]') == False].reset_index(level=None, drop=False, inplace=False, col_level=0, col_fill='')
    return data



path = "./labels/"
dataset_list = os.listdir('./labels/')
dataset_key = st.sidebar.selectbox(
    "Dataset",
    dataset_list,
    key="dataset_select",
    index=0,
    help="Select the dataset to work on.",
)

if dataset_key is not None:
    subset_list = os.listdir(path+dataset_key)
    if len(subset_list) > 0:
        subset_key = st.sidebar.selectbox(
            "Subset",
            subset_list,
            key="subset_select",
            index=0,
            help="Select the subset to work on.",
        )
        path = f'./labels/{dataset_key}/{subset_key}/*.csv'
        url_gs = f'./labels/{dataset_key}/{subset_key}/'
    else:
        path = f'./labels/{dataset_key}/*.csv'
        url_gs = f'./labels/{dataset_key}/'

dataset = load_data_pd(glob.glob(path)[0])

dataset_org = dataset
if st.sidebar.checkbox('non-arabic text',key='non-arabic'):
    dataset = drop_arabic(dataset)

if st.sidebar.checkbox('text length',key='text_length'):
    input = st.sidebar.number_input('text length',min_value=0,max_value=10000,value=0,key='text_length_input')
    dataset = filter_by_length(dataset,input)


step=0
example_index = st.sidebar.number_input(
                f"Select the example index (Size = {len(dataset)})",
                min_value=0,
                max_value=len(dataset) - step,
                value=0,
                step=step,
                key="example_index_number_input",
                help="Offset = 50.",
            )

# Load image name and its caption

image_index = dataset.iloc[[example_index]]['Image_name'][example_index]
caption_index = dataset.iloc[[example_index]]['Caption'][example_index]




# Load image
#with open(f'{url_gs}url.txt', 'rb') as f:
#    url = f.readlines()

# Load image
url=Path(f'{url_gs}url.txt').read_text().replace('\n', '')
image = load_image(url+image_index,image_index)
st.image(image,width=300)


# Show image metadata 
st.sidebar.write("## Metadata:\n", dataset.iloc[[example_index]].to_dict() )

# Update image caption
st.markdown("## Caption Editor")
updated_caption_name = st.text_input("Caption",
                                    help= "Write a proper description of the image",
                                    value=caption_index)


if 'index' in dataset.columns:

    example_index = dataset.iloc[[example_index]]['index'][example_index]

if st.button("Update Caption"):
    dataset_org.loc[example_index,'Caption'] = updated_caption_name
    dataset_org.to_csv(glob.glob(path)[0],index=False)
    st.write("## Updated Caption:\n", updated_caption_name )
