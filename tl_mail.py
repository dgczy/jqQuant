
# -*- coding: utf-8 -*-

#引入包
import smtplib
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

#研究、策略中区别配置
try:
    #策略中必须导入kuanke.user_space_api包，用于支持read_file
    from kuanke.user_space_api import read_file
except:
    pass
    

def send_html_qqmail(subject,message):
    """
    发送html格式QQ邮件  
    subject：邮件主题
    message：邮件正文    
    """
    #发送的邮箱
    sender='DGCIdea<95217585@qq.com>' 
    #要接受的邮箱
    receiver='95217585@qq.com' 
    #smtp服务器
    smtpserver='smtp.qq.com' 
    #邮箱账号
    username='95217585@qq.com' 
    #邮箱授权码。一个16位字符串
    password='yjitmbhjartjbjba' 
    #中文需参数‘utf-8'，单字节字符不需要str(message)，纯文本为参数'plain'，html为参数'html'
    msg=MIMEText(message,'html','utf-8') 
    #邮件主题
    msg['Subject']=Header(subject,'utf-8') 
    #发送和接收都为自己
    msg['to']=receiver     
    msg['from']=sender     
    #启动
    server=smtplib.SMTP_SSL('smtp.qq.com')
    try:
        # ssl（弃用）
        #server.connect() 
        #登陆
        server.login(username,password) 
        #发送
        server.sendmail(sender,receiver,msg.as_string()) 
    except Exception as e:
        raise e
    #结束    
    server.quit()    
    

def send_image_qqmail(subject,message,image_list=[],file_root='./',file_ext='png'):
    """
    发送html含image格式QQ邮件  
    subject：邮件主题
    message：邮件正文
    image_list：图片列表
    file_root：图片所在目录
    file_ext：图片扩展名
    """
    #发送的邮箱
    sender='DGCIdea<95217585@qq.com>' 
    #要接受的邮箱
    receiver='95217585@qq.com' 
    #smtp服务器
    smtpserver='smtp.qq.com' 
    #邮箱账号
    username='95217585@qq.com' 
    #邮箱授权码。一个16位字符串
    password='yjitmbhjartjbjba' 
    #smtp
    server=smtplib.SMTP_SSL('smtp.qq.com')   
    #配置
    msgRoot=MIMEMultipart('related')
    #邮件主题
    msgRoot['Subject']=subject
    #发送和接收都为自己
    msgRoot['to']=receiver     
    msgRoot['from']=sender 
    #邮件文本信息
    #中文需参数‘utf-8'，单字节字符不需要str(message)，纯文本为参数'plain'，html为参数'html'
    msgText=MIMEText(message,'html','utf-8')
    msgRoot.attach(msgText)
    if len(image_list)!=0:
        #邮件图像信息
        for name in image_list:
            file_name=('%s%s.%s')%(file_root,name,file_ext)
            image_id=('<%s>')%(name)
            image_data=read_file(file_name)
            msgImage=MIMEImage(image_data)
            msgImage.add_header('Content-ID',image_id)
            msgRoot.attach(msgImage)    
    try:
        #ssl（弃用）
        #server.connect() 
        #登陆
        server.login(username,password) 
        #发送
        server.sendmail(sender,receiver,msgRoot.as_string()) 
    except Exception as e:  
        raise e  
    #结束    
    server.quit()   