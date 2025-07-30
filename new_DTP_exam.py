# -*- coding: utf-8 -*-
# from flask import Flask, request, jsonify
import json
import sys
# import uuid
import pandas as pd
import datetime
import random
import streamlit as st
from multiprocessing import Pool
import os

# app = Flask(__name__)


# <------------------------------- api调用接口 ------------------------------------>

import json
import requests

#调用llm
def send_to_llm(prompt):
    # 定义要发送的数据
    data = {'prompt': prompt,'max_tokens':2048, 'temperature':0.7,'top_k':20,'top_n_tokens':5,'top_p':0.8,'truncate':None,'typical_p':0.95,'watermark':True,'repetition_penalty':1.05,'top':249}
    # 发送 POST 请求到 API
    response = requests.post("http://202.103.135.98:5003/", json=data)
    # 打印 API 响应的内容
    return response.text


import pymysql

def upload_sql(pid,q_json,time_stamp,points,sight_message, personal_message, personality, diagnose, evaluation, patient_number):
    q_json = json.dumps(q_json)
    # 连接 MySQL
    conn = pymysql.connect(host="localhost", user="root", password="!#M4GvknpJzl", database="chatzoc",charset='utf8mb4')
    cursor = conn.cursor()
    # SQL 语句：如果 pid 存在则更新，不存在则插入
    query = """
    INSERT INTO chatzoc_education (id,q,time_stamp,points,sight_message, personal_message, personality, diagnose, evaluation, patient_number)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE 
        q = VALUES(q),
        time_stamp = VALUES(time_stamp),
        points = VALUES(points),
        sight_message = VALUES(sight_message),
        personal_message = VALUES(personal_message),
        personality = VALUES(personality),
        diagnose = VALUES(diagnose),
        evaluation = VALUES(evaluation),
        patient_number = VALUES(patient_number);
    """
    data = (pid,q_json,time_stamp,points,sight_message, personal_message, personality, diagnose, evaluation, patient_number)
    # 执行 SQL
    cursor.execute(query, data)
    conn.commit()
    # print("数据插入或更新成功！")
    # 关闭连接
    cursor.close()
    conn.close()
    return "数据插入或更新成功！"


def download_sql(pid):
    """从 MySQL 数据库查询 pid 对应的 q，若不存在则返回 0"""
    # 连接 MySQL
    conn = pymysql.connect(host="localhost", user="root", password="!#M4GvknpJzl", database="chatzoc",charset='utf8mb4')
    cursor = conn.cursor()
    # 查询数据库
    query = "SELECT q,sight_message,personal_message,personality,diagnose,evaluation,patient_number FROM chatzoc_education WHERE id = %s"
    cursor.execute(query, (pid,))
    result = cursor.fetchone()  # 获取查询结果
    # 关闭连接
    cursor.close()
    conn.close()
    if result:
        return result  # 返回多个结果数据
    else:
        return '[]','','','','','',''  # 若 pid 不存在，则返回 0

def upload_evaluation(pid,student_diagnose,evaluation):
    # 连接 MySQL
    conn = pymysql.connect(host="localhost", user="root", password="!#M4GvknpJzl", database="chatzoc",charset='utf8mb4')
    cursor = conn.cursor()
    # SQL 语句：如果 pid 存在则更新，不存在则插入
    query = """
    INSERT INTO chatzoc_education (id,student_diagnose,evaluation)
    VALUES (%s, %s, %s)
    ON DUPLICATE KEY UPDATE 
        evaluation = VALUES(evaluation),
        student_diagnose = VALUES(student_diagnose);
    """
    data = (pid,student_diagnose,evaluation)
    # 执行 SQL
    cursor.execute(query, data)
    conn.commit()
    # print("数据插入或更新成功！")
    # 关闭连接
    cursor.close()
    conn.close()
    return "数据插入或更新成功！"



def convert_history(chat_list):
    history = ''
    for i,hist in enumerate(chat_list):
        if i > len(chat_list) - 10:
            if hist['role'] == 'ai':
                history += '患者（你）：' + hist['content'] + '\n'
            elif hist['role'] == 'user':
                history += '医生：' + hist['content'] + '\n'
            else:
                print('历史转换出错')
    return history

def convert_history_all(chat_list):
    history = ''
    for hist in chat_list:
        if hist['role'] == 'ai':
            history += '患者：' + hist['content'] + '\n'
        elif hist['role'] == 'user':
            history += '医生：' + hist['content'] + '\n'
        else:
            print('历史转换出错')
    return history


def diagnose_eval(student_diagnose,diagnose):
    prompt = f"""
##任务描述##
你是一个眼科医学问诊课的老师，请根据<标准诊断>给<学生诊断>结果打分。具体打分原则为：根据<标准诊断>中每个诊断对于患者治疗的重要性，对比<学生诊断>中的错漏部分，给出一个1-10分的打分，并给出详细解析。

<标准诊断>
{diagnose}

<学生诊断>
{student_diagnose}

##任务开始##
"""
    response = send_to_llm(prompt)

    return response  # 返回结果，以便在回调中使用

get_points_prompt_JBXX = """
基本信息
您叫什么名字-0.625
您今年几岁-0.625
您是男性还是女性-0.625
您来自哪里-0.625
您住在哪里-0.625
您的职业是什么-0.625
您的种族是什么-0.625
您结婚了吗-0.625"""

get_points_prompt_XBS = """
现病史
您感觉眼睛有什么不适-2.564
哪只眼睛受到影响-2.564
已经多久了-2.564
是突然发作还是逐渐发作-1.709
除此之外，您的眼睛还有其他不适吗-2.564
出现眼部症状之前是否有任何诱因-1.709
出现症状时您是否情绪不安-0.855
您最近是否出现过眼睛发红-1.709
您有眼睛疼痛吗-1.709
您感觉眼睛有什么类型的疼痛-0.855
您的眼睛疼痛是持续性的还是间歇性的-0.855
您的眼睛疼痛是否会随着症状而变化时间-0.855
您感到头晕吗-1.709
您头痛吗-1.709
您感到恶心吗-1.709
您呕吐过吗-1.709
您的眼睛对光敏感吗-1.709
您的眼睛会流泪吗-1.709
您觉得眼睛里有东西吗-1.709
您的眼睛会产生过多的分泌物吗-1.709
您觉得有什么东西挡住了您的视线吗-1.709
您的视力是否下降-1.709
您所说的看东西“不清楚”具体是怎么样的-0.855
您看东西有变暗吗-1.709
您看东西有扭曲吗-1.709
你看到阴影在哪个方位-0.855
你有没有看东西闪光-1.709
你以前去过其他医院吗-1.709
当地医院给你提供了什么治疗-1.709
发病以来你的精神状态如何-0.427
发病以来你的食欲如何-0.427
发病以来你的睡眠如何-0.427
发病以来排便和排尿有什么变化吗-0.427
发病以来你的体重有什么变化吗-0.427"""

get_points_prompt_JWBS = """
既往病史
您以前得过眼疾吗-2.564
您以前遇到过类似的情况吗-1.282
您以前戴过眼镜吗-1.282
您以前得过高血压吗-1.282
您患高血压多久了-0.641
记录的最高血压是多少-0.641
您定期服用降压药吗-0.641
服用降压药后您的血压控制得如何-0.641
您以前得过糖尿病吗-1.282
您患糖尿病多久了-0.641
您定期服用降糖药吗-0.641
服用降糖药后您的血糖控制得如何-0.641
您得过冠心病吗以前患过心脏病吗-1.282
您患冠心病多久了-0.641
您经常服用治疗冠心病的药物吗-0.641
您以前患过其他慢性全身性疾病吗-1.282
您以前得过肺结核吗-1.282
您以前得过乙肝吗-1.282
您以前得过其他传染病吗-1.282
您以前经历过重大创伤吗-1.282
您以前做过手术吗-1.282
您以前输过血吗-1.282
您以前按时接种过疫苗吗-1.282"""

get_points_prompt_QTWT = """
其他问题
您平时接触工业粉尘吗-0.952
您平时接触花粉吗-0.952
您以前接触过辐射吗-0.952
您经常吸烟吗-0.952
您经常喝酒吗-0.952
您得过性传播疾病吗-0.952
您最近去过疫区吗-0.952
您父母的健康状况如何-0.952
您家中是否有任何亲属出现过与您类似的症状-0.952
您家中是否有遗传或精神疾病-0.952
您的父母是否有近亲结婚-0.952
您有孩子吗-0.952
健康状况如何您孩子的健康状况如何-0.952
您配偶的健康状况如何-0.952
您第一次来月经的年龄是多少-0.952
您的月经周期规律吗-0.952
您什么时候绝经的-0.952
您以前有过药物过敏吗-1.905
您以前有过食物过敏吗-1.905"""


# 定义一个函数，用于提取打分结果
def generate_points(history,get_points_prompt):
    prompt = f"""
##任务描述##
你是一个眼科医学问诊课的老师，请根据<问诊标准问题>中提供的问题类别例子判断<医患对话记录>中的医生询问了其中多少个问题，并计算已问问题的得分总和。
注意，在<问诊标准问题>中，问题类别例子格式为“您以前得过眼疾吗-2.564”，“-”左边的是问题，右边的是得分。你的回复格式是：“已问：x；得分：x”。
举例：如果医生在<医患对话记录>中询问了<问诊标准问题>中的3个问题类别，其得分分别为1.1，2.5，3.0，则最终输出结果为：“已问：3；得分：6.6”。
相信你的判断，不需要给出额外的解释和备注

<问诊标准问题>
{get_points_prompt}

<医患对话记录>
{history}

##任务开始##
"""
    response = send_to_llm(prompt)

    # print(response)

    return response  # 返回结果，以便在回调中使用

def generate_eval(history,get_points_prompt):
#     prompt = f"""
# ##任务描述##
# 你是一个眼科医学问诊课的老师，请根据<问诊标准问题>中提供的问题类别例子判断<医患对话记录>中的医生尚未询问哪些问题，针对这些漏问内容给出后续问诊思路建议，并挑选其中分值较高的未询问问题作为例子。
# 注意，在<问诊标准问题>中，问题类别例子格式为“您以前得过眼疾吗-2.564”，“-”左边的是问题，右边的是得分。凡是你在回答中列出的例子，都不需要写出“-”以及其右边的得分。

# <问诊标准问题>
# {get_points_prompt}

# <医患对话记录>
# {history}

# ##任务开始##
# """

    prompt = f"""
##任务描述##
你是一个眼科医学问诊课的老师，请根据<医患对话记录>判断<问诊标准问题>中还有哪些问题是不知道答案，仍需要医生继续询问的，针对这些医生漏问内容给出后续问诊思路建议，并挑选其中分值较高的未询问问题作为例子。
注意，在<问诊标准问题>中，问题类别例子格式为“您以前得过眼疾吗-2.564”，“-”左边的是问题，右边的是得分。凡是你在回答中列出的例子，都不需要写出“-”以及其右边的得分。

<问诊标准问题>
{get_points_prompt}

<医患对话记录>
{history}

##任务开始##
"""

    response = send_to_llm(prompt)

    return response  # 返回结果，以便在回调中使用

def generate_eval_emotion(history,personality):
    prompt = f"""
##任务描述##
你是一个眼科医学问诊课的老师，请判断<医患对话记录>中的医生的问询态度对于一个性格为<患者性格>的患者来说是否得体，是否具有同理心，给出一个1-10分的打分，并给出评分理由。

<患者性格>
{personality}

<医患对话记录>
{history}

##任务开始##
"""
    response = send_to_llm(prompt)

    return response  # 返回结果，以便在回调中使用


def print_chat():
    print_container = st.container(border=True)
    for i,QA in enumerate(st.session_state.chat_list):
        if i > len(st.session_state.chat_list) - 50:
            with print_container.chat_message(QA['role']):
                st.write(QA['content']) 

def DTP_generate():
    df = pd.read_excel('病历表_exam.xlsx')
    random_index = random.randint(1, len(df)) -1
    random_sight_message = df['视力信息'][random_index]
    random_personal_message = df['相关信息'][random_index]
    random_diagnose = df['诊断结果'][random_index]
    random_person_number = df['no.'][random_index]
    random_check_photos = df['照片展示2'][random_index]
    # personalities = ["乐观", "悲观", "外向", "内向", "谨慎", "冲动", "理性", "感性", "幽默", "严肃", "急躁", "狂躁", "抑郁", "暴怒"]
    personalities = ["焦虑，恐慌"]
    random_personality = random.choice(personalities)
    return random_sight_message, random_personal_message, random_personality, random_diagnose, random_person_number, random_check_photos


def core_logic(personality,personal_message,doctor_q,history):

#     print(f"""{history}
# 医生：{doctor_q}
# 患者（你）：""")

    prompt = f"""##任务要求##
你需要扮演一个符合<个人性格>的眼病患者进行一个问诊，按照<个人背景>回答医生的问题，但注意患者扮演，不要说太多专业医学词汇，也不要一次性说太多医生没问到的内容。若医生问询的问题在<个人背景>中未提及，你可以根据自己的<个人性格>表述自己没有做过该类检查或不清楚或记不清。

<个人性格>
{personality}

<个人背景>
{personal_message}

##患者扮演开始##
{history}
医生：{doctor_q}
患者（你）：
"""

    response = send_to_llm(prompt)
    # print(response)

    return response

def input_on_change():
    st.session_state.finished = False



########### streamlit框架 ##############
if 'chat_list' not in st.session_state:
    st.session_state.chat_list = []

if 'query' not in st.session_state:
    st.session_state.query = ''

if 'sight_message' not in st.session_state:
    st.session_state.sight_message = ''

if 'personal_message' not in st.session_state:
    st.session_state.personal_message = ''

if 'personality' not in st.session_state:
    st.session_state.personality = ''

if 'diagnose' not in st.session_state:
    st.session_state.diagnose = ''

if 'evaluation' not in st.session_state:
    st.session_state.evaluation = ''

if 'finished' not in st.session_state:
    st.session_state.finished = False

if 'patient_number' not in st.session_state:
    st.session_state.patient_number = '0'

if 'which_check_' not in st.session_state:
    st.session_state.which_check_ = ''

if 'choosen' not in st.session_state:
    st.session_state.choosen = False

if 'random_check_photos' not in st.session_state:
    st.session_state.random_check_photos = ''

if 'JBXX_points' not in st.session_state:
    st.session_state.JBXX_points = 0

if 'XBS_points' not in st.session_state:
    st.session_state.XBS_points = 0

if 'JWBS_points' not in st.session_state:
    st.session_state.JWBS_points = 0

if 'QTWT_points' not in st.session_state:
    st.session_state.QTWT_points = 0

########### streamlit框架 ##############
import time
# st.title("LLMDTP数字患者问诊教学系统")
st.image('logo.png')

student_id = st.text_input('请输入您的编号', on_change = input_on_change)

chat_list,st.session_state.sight_message, st.session_state.personal_message, st.session_state.personality, st.session_state.diagnose, st.session_state.evaluation, st.session_state.patient_number = download_sql(student_id)
st.session_state.chat_list = json.loads(chat_list)

# print('st.session_state.evaluation:',st.session_state.evaluation)

if st.session_state.evaluation == '':

    if student_id != '':

        if st.session_state.personality == '':
            with st.spinner("数字患者生成中...", show_time=True):
                st.session_state.sight_message, st.session_state.personal_message, st.session_state.personality, st.session_state.diagnose, st.session_state.patient_number,st.session_state.random_check_photos = DTP_generate()

        st.write(f'患者视力眼压情况：{st.session_state.sight_message}')

        photo_path = f'photos/{st.session_state.patient_number}.png'
        if os.path.exists(photo_path):
            st.write('患者视力眼部状况：')
            st.image(photo_path)

        st.markdown('**现在你是接诊医生，需要对虚拟患者进行提问**')

        if st.session_state.finished == False:
            st.session_state.input_text = st.chat_input('请在此处输入您的问诊问题')
            if st.session_state.input_text:

                history = convert_history(st.session_state.chat_list)
                # print(history)
                with st.spinner("思考中...", show_time=True):
                    st.session_state.answer = core_logic(st.session_state.personality,st.session_state.personal_message,st.session_state.input_text,history)

                st.session_state.chat_list.append({'role':'user','content':st.session_state.input_text})
                st.session_state.chat_list.append({'role':'ai','content':st.session_state.answer})

        print_chat()

        if st.session_state.finished == False:
            with st.sidebar:
                
                if st.session_state.chat_list != []:
                    history = convert_history_all(st.session_state.chat_list)
                    # print('hist_all',history)
                    # st.rerun()
                    # 定义你的提示列表
                    # prompts = [get_points_prompt_JBXX, get_points_prompt_XBS, get_points_prompt_JWBS, get_points_prompt_QTWT]
                    # for prompt in prompts:

                    res_JBXX = generate_points(history,get_points_prompt_JBXX)
                    res_XBS = generate_points(history,get_points_prompt_XBS)
                    res_JWBS = generate_points(history,get_points_prompt_JWBS)
                    res_QTWT = generate_points(history,get_points_prompt_QTWT)

                    # print(res_JBXX,res_XBS,res_JWBS,res_QTWT)
                    # 已问：2；得分：1.25
                    JBXX_process = int(res_JBXX.split("；")[0].split('：')[1].split('\n')[0])
                    st.session_state.JBXX_points = float(res_JBXX.split("；")[1].split('：')[1].split('\n')[0])
                    XBS_process = int(res_XBS.split("；")[0].split('：')[1].split('\n')[0])
                    st.session_state.XBS_points = float(res_XBS.split("；")[1].split('：')[1].split('\n')[0])
                    JWBS_process = int(res_JWBS.split("；")[0].split('：')[1].split('\n')[0])
                    st.session_state.JWBS_points = float(res_JWBS.split("；")[1].split('：')[1].split('\n')[0])
                    QTWT_process = int(res_QTWT.split("；")[0].split('：')[1].split('\n')[0])
                    st.session_state.QTWT_points = float(res_QTWT.split("；")[1].split('：')[1].split('\n')[0])
                else:
                    JBXX_process = 0
                    st.session_state.JBXX_points = 0
                    XBS_process = 0
                    st.session_state.XBS_points = 0
                    JWBS_process = 0
                    st.session_state.JWBS_points = 0
                    QTWT_process = 0
                    st.session_state.QTWT_points = 0



                # # 创建一个进程池并映射函数到提示列表(有问题，streamlit和async不太兼容，会出现下一轮才能提取上一轮信息的问题，经过各种尝试无法解决)
                # if __name__ == '__main__':
                #     with Pool(4) as pool:  # 使用4个进程,4个维度同时打分
                #         results = [pool.apply_async(generate_points, args=(history,prompt,)) for prompt in prompts]
                #         pool.close()  # 关闭进程池，不再接受新的任务
                #         pool.join()  # 等待所有子进程完成
                #         extracted_results = [r.get() for r in results]
                #         print(extracted_results)
                #         # st.rerun()
                st.slider("基本信息询问进度", 0, 8, JBXX_process)
                st.slider("现病史询问进度", 0, 33, XBS_process)
                st.slider("既往病史询问进度", 0, 22, JWBS_process)
                st.slider("其他问题", 0, 18, QTWT_process)
                time_stamp = datetime.datetime.now()
                st.session_state.points = st.session_state.JBXX_points + st.session_state.XBS_points + st.session_state.JWBS_points + st.session_state.QTWT_points
                upload_sql(student_id,st.session_state.chat_list,time_stamp,st.session_state.points,st.session_state.sight_message, st.session_state.personal_message, st.session_state.personality, st.session_state.diagnose, st.session_state.evaluation, st.session_state.patient_number)
                
                # 学生点击结束
                if st.session_state.chat_list != []:
                    press_button = st.button('完成问诊')
                    if press_button:
                        st.session_state.finished = True
                        st.rerun()
        

        if st.session_state.finished:

            st.subheader('请完成下列问题')

            if not st.session_state.choosen:
                options_check = ["无", "眼轴测量", "角膜曲率测量", "角膜地形图检查", "角膜内皮镜检查", "眼球突出计检查", "UBM", "前段OCT", "B超", "眼底照相", "视野检查", "FFA", "ICGA", "OCT", "OCTA", "VEP", "ERG", "CT", "MRI", "其他"]
                check_list_ = st.pills("患者下一步应该进行哪些辅助检查【不定项】", options_check, selection_mode="multi",key="1")
                st.session_state.which_check_ = ''
                for check_ in check_list_:
                    st.session_state.which_check_ += '，'+check_
                if '其他' in check_list_:
                    other_check_ = st.text_input('请描述您认为需要的其他检查项')
                    st.session_state.which_check_ += '：'+other_check_
                upload = st.button('确认')
                if upload:
                    st.session_state.choosen = True
                    st.rerun()
            else:
                st.markdown(f"你选择的辅助检查项是：{st.session_state.which_check_}，下面是检查结果图")
                for photo_name in st.session_state.random_check_photos.split('\n'):
                    if photo_name != '':
                        st.markdown(f"**{photo_name.split('_')[0]}**")
                        st.image(f'photos/{photo_name}')

            if st.session_state.choosen:
                student_diagnose_1 = st.text_input('一、最可能的诊断')
                student_diagnose_2 = st.text_input('二、主要诊断依据？')
                student_diagnose_3 = st.text_input('三、请列出鉴别诊断及主要鉴别点')
                student_diagnose_4 = st.text_input('四、简述本病的治疗原则')

                student_diagnose = None
                if (st.session_state.which_check_ != '') and student_diagnose_1 and student_diagnose_2 and student_diagnose_3 and student_diagnose_4:       
                    
                    student_diagnose = f"""患者下一步应该进行的辅助检查
                    {st.session_state.which_check_}

                    一、最可能的诊断
                    {student_diagnose_1}

                    二、主要诊断依据？
                    {student_diagnose_2}

                    三、请列出鉴别诊断及主要鉴别点
                    {student_diagnose_3}

                    四、简述本病的治疗原则
                    {student_diagnose_4}"""

                upload_final = st.button('提交回答')
                if upload_final and student_diagnose:

                    history = convert_history_all(st.session_state.chat_list)
                    score = f"""基本信息询问：{st.session_state.JBXX_points}  
    现病史询问：{st.session_state.XBS_points}  
    既往病史询问：{st.session_state.JWBS_points}  
    其他问题询问：{st.session_state.QTWT_points}  

    总成绩：{st.session_state.points:.2f}"""
                    st.markdown(f"""
    **模拟问诊得分**  
    {score}  
      
    """)
                    with st.spinner("诊断评估结果生成中...", show_time=True):
                        eval_diagnose = diagnose_eval(student_diagnose,st.session_state.diagnose)
                        st.markdown(f"""
      
    ----------------------------------------  
    **诊断评估结果**  
    {eval_diagnose}  
    """)

                    with st.spinner("基本信息询问缺少问题生成中...", show_time=True):
                        eval_JBXX = generate_eval(history,get_points_prompt_JBXX)
                        st.markdown(f"""
      
    ----------------------------------------  
    **问诊详细评估结果**  
      
      
    ----------------------------------------  
    **基本信息询问缺少的问题：**  
    {eval_JBXX}  
    """)
                    with st.spinner("现病史询问缺少问题生成中...", show_time=True):
                        eval_XBS = generate_eval(history,get_points_prompt_XBS)
                        st.markdown(f"""
      
    ----------------------------------------  
    **现病史询问缺少的问题：**  
    {eval_XBS}  
    """)
                    with st.spinner("既往病史询问缺少问题生成中...", show_time=True):
                        eval_JWBS = generate_eval(history,get_points_prompt_JWBS)
                        st.markdown(f"""
      
    ----------------------------------------  
    **既往病史询问缺少的问题：**  
    {eval_JWBS}  
    """)
                    with st.spinner("其他问题询问缺少问题生成中...", show_time=True):
                        eval_QTWT = generate_eval(history,get_points_prompt_QTWT)
                        st.markdown(f"""
      
    ----------------------------------------  
    **其他问题询问缺少的问题：**  
    {eval_QTWT}  
    """)
                    with st.spinner("同理心程度评估生成中...", show_time=True):
                        eval_emotion = generate_eval_emotion(history,st.session_state.personality)
                        st.markdown(f"""
      
    ----------------------------------------  
    **同理心程度评估结果**  
    {eval_emotion}
    """)


                    evaluation = f"""
    **模拟问诊得分**  
    {score}  
      
       
    ----------------------------------------  
    **诊断评估结果**  
    {eval_diagnose}

    ----------------------------------------  
    **问诊详细评估结果**  
      
    ----------------------------------------  
    **基本信息询问缺少的问题：**  
    {eval_JBXX}  
      
    ----------------------------------------  
    **现病史询问缺少的问题：**  
    {eval_XBS}  
      
    ----------------------------------------  
    **既往病史询问缺少的问题：**  
    {eval_JWBS}  
      
    ----------------------------------------  
    **其他问题询问缺少的问题：**  
    {eval_QTWT}  
      
    ----------------------------------------  
    **同理心程度评估结果**  
    {eval_emotion}"""
                    upload_evaluation(student_id,student_diagnose,evaluation)
                    # st.rerun()
                else:
                    st.markdown(':red[请完成所有问题项填写再提交]')


else:
    st.write(f'患者视力眼压情况：{st.session_state.sight_message}')

    photo_path = f'photos/{st.session_state.patient_number}.png'
    if os.path.exists(photo_path):
        st.write('患者视力眼部状况：')
        st.image(photo_path)

    st.markdown('**现在你是接诊医生，需要对虚拟患者进行提问**')

    print_chat()

    st.markdown(st.session_state.evaluation)


