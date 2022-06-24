from flask import Flask, render_template, request, Response
from flask_mysqldb import MySQL
import tensorflow as tf
import datetime, time
import os, sys
import numpy as np
import cv2 as cv
from threading import Thread
from tensorflow import keras
from tensorflow.keras.models import load_model
from tensorflow.keras import layers
import tensorflow_hub as hub
import predict_code

# from predict import chilli_logic
# from webcamvideostream import WebcamVideoStream
# from flask_basicauth import BasicAuth



app = Flask(__name__)

# Configure db
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'agrow_app'

# app.config['BASIC_AUTH_USERNAME'] = 'pi'
# app.config['BASIC_AUTH_PASSWORD'] = 'pi'
# app.config['BASIC_AUTH_FORCE'] = True

# basic_auth = BasicAuth(app)
# last_epoch = 0

mysql = MySQL(app)


global capture,rec_frame, grey, switch, neg, face, rec, out 
capture=0
grey=0
neg=0
face=0
switch=1
rec=0





#make shots directory to save pics
try:
    os.mkdir('./shots')
except OSError as error:
    pass


camera = cv.VideoCapture(0)

def record(out):
    global rec_frame
    while(rec):
        time.sleep(0.05)
        out.write(rec_frame)
 

def gen_frames():  # generate frame by frame from camera
    global out, capture,rec_frame
    while True:
        success, frame = camera.read() 
        if success:
            if(grey):
                frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
            if(neg):
                frame=cv.bitwise_not(frame)    
            if(capture):
                capture=0
                now = datetime.datetime.now()
                p = os.path.sep.join(['shots', "shot_{}.png".format(str(now).replace(":",''))])
                cv.imwrite(p, frame)
            
            if(rec):
                rec_frame=frame
                frame= cv.putText(cv.flip(frame,1),"Recording...", (0,25), cv.FONT_HERSHEY_SIMPLEX, 1, (0,0,255),4)
                frame=cv.flip(frame,1)
            
                
            try:
                ret, buffer = cv.imencode('.jpg', cv.flip(frame,1))
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            except Exception as e:
                pass
                
        else:
            pass
        

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/requests',methods=['POST','GET'])
def tasks():
    global switch,camera
    if request.method == 'POST':
        if request.form.get('click') == 'Capture':
            global capture
            capture=1
        elif  request.form.get('grey') == 'Grey':
            global grey
            grey=not grey
        elif  request.form.get('neg') == 'Negative':
            global neg
            neg=not neg
        elif  request.form.get('stop') == 'Stop/Start':
            
            if(switch==1):
                switch=0
                camera.release()
                cv.destroyAllWindows()
                
            else:
                camera = cv.VideoCapture(0)
                switch=1
        elif  request.form.get('rec') == 'Start/Stop Recording':
            global rec, out
            rec= not rec
            if(rec):
                now=datetime.datetime.now() 
                fourcc = cv.VideoWriter_fourcc(*'XVID')
                out = cv.VideoWriter('vid_{}.avi'.format(str(now).replace(":",'')), fourcc, 20.0, (640, 480))
                #Start new thread for recording the video
                thread = Thread(target = record, args=[out,])
                thread.start()
            elif(rec==False):
                out.release()              
    elif request.method=='GET':
        return render_template('livecamera.html')
    return render_template('livecamera.html')



@app.route("/") 
def home():
    return render_template('signup.html')


@app.route("/signin") 
def signin():
    return render_template('signin.html')


@app.route("/signin_data", methods=['POST'])
def signin_data():
    # Fetch form data
    email = request.form.get('email')
    password = request.form.get('password')
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM login_info WHERE email_id = '"+email+"' and user_password = '"+password+"'")
    r = cur.fetchall()
    count = cur.rowcount
    if count == 1:
        return render_template('dashboard.html')
    else:
        return render_template('signin.html')
    mysql.connection.commit()
    cur.close()
    
    

@app.route("/dashboard")
def dashboard():
    return render_template('dashboard.html')


@app.route("/livecamera")
def livecamera():
    return render_template('livecamera.html')


@app.route("/livediseasechilli")
def livediseasechilli():
    return render_template('livediseasechilli.html')


@app.route("/livediseasebrinjal")
def livediseasebrinjal():
    return render_template('livediseasebrinjal.html')


@app.route('/captureimage')
def captureimage():
    return render_template('captureimage.html')


@app.route("/signup_data", methods=['POST'])
def signup_data():
    # Fetch form data
    name = request.form.get('name')
    email = request.form.get('email')
    ph_no = request.form.get('phnumber')
    password = request.form.get('password')
    
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO user_info(name, email_id, ph_no) VALUES(%s, %s, %s)",(name, email, ph_no))
    mysql.connection.commit()
    cur.close()
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO login_info(email_id, user_password) VALUES(%s, %s)",(email, password))
    mysql.connection.commit()
    cur.close()
    return render_template('dashboard.html')





@app.route('/captureimagedata', methods=["POST"])
def predict():
    # getting image from folder
    imagefile = request.files['imagefile']
    image_path = "static/model_images/"+imagefile.filename
    imagefile.save(image_path)

    # prepare image
    IMG_SIZE = 224
    img_array = cv.imread(image_path)
    resized_img_array = cv.resize(img_array, (IMG_SIZE, IMG_SIZE))
    resized_scaled_img_array = resized_img_array/255.0
    # plt.imshow(resized_scaled_img_array)
    resized_scaled_img_array = resized_scaled_img_array.reshape(
        -1, IMG_SIZE, IMG_SIZE, 3)

    prediction = model.predict([resized_scaled_img_array])
    brinjal = prediction[0][0]
    chilli = prediction[0][1]
    if max(brinjal, chilli) < 0.95:
        prediction = "Invalid Input"
    else:
            if brinjal > chilli :
                prediction = "It is a Brinjal Plant with confidence : "+ str( brinjal*100)
            if brinjal < chilli : 
                prediction = "It is a Chilli Plant with confidence : "+ str(chilli*100)   
                aa = chilli_model.predict([resized_scaled_img_array])
                print(aa)
                final_output = "Observations : " + str(predict_code.chilli_logic(aa))
    return render_template('captureimage.html',prediction = prediction,final_output=final_output,image_path = image_path)


if __name__ == "__main__":
    model = load_model("model/")
    chilli_model = keras.models.load_model('chilli-model/res_net_goodnight.h5',custom_objects={'KerasLayer':hub.KerasLayer})
    # brinjal_model = keras.models.load_model('brinjal-model/res_net_brinjal.h5')
    app.run(debug=True)
    
    
camera.release()
cv.destroyAllWindows()  