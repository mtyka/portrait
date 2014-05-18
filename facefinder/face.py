#!/usr/bin/python
"""
This program is demonstration for face and object detection using haar-like features.
The program finds faces in a camera image or video stream and displays a red box around them.

Original C implementation by:  ?
Python implementation by: Roman Stanchak, James Bowman
"""
import sys
import urllib
import urllib2
import base64
import cv2.cv as cv
import cv2
from optparse import OptionParser

picurl = "http://localhost:5000"
  
def force_aspect(w, h, aspect):
  if w > h*aspect:
    w = h*aspect
  else:
    h = w/aspect
  return w, h

def crop_img_with_margin(img, x, y, w, h, prescale=1.0, w_recanvas=1.0, h_recanvas=1.0):
  w_margin = w * (w_recanvas-1.0)/2.0
  h_margin = h * (h_recanvas-1.0)/2.0
  x1 = int((x-w_margin) * prescale) 
  x2 = int((x+w+w_margin) * prescale) 
  y1 = int((y-h_margin) * prescale) 
  y2 = int((y+h+h_margin) * prescale)
  if x1<0: return None
  if x2>=img.width: return None
  if y1<0: return None
  if y2>=img.height: return None
  #if x1<0: x1=0
  #if x2>=img.width: x2=img.width
  #if y1<0: y1=0
  #if y2>=img.height: y2=img.height
  return img[y1:y2, x1:x2]

class FaceExtractor():
  def __init__(self, face_cascade, eye_cascade):
    self.min_size = (20, 20)
    self.image_scale = 2
    self.haar_scale = 1.2
    self.min_neighbors = 3
    self.haar_flags = 0
    self.face_cascade = face_cascade
    self.eye_cascade = eye_cascade
    self.aspect = 1


  def find_faces(self, img, processor): 
    # allocate temporary images
    gray = cv.CreateImage((img.width,img.height), 8, 1)
    small_img = cv.CreateImage((cv.Round(img.width / self.image_scale),
                                cv.Round(img.height / self.image_scale)), 8, 1)
    cv.CvtColor(img, gray, cv.CV_BGR2GRAY) # convert color input image to grayscale
    cv.Resize(gray, small_img, cv.CV_INTER_LINEAR)
    cv.EqualizeHist(small_img, small_img)
    
    t = cv.GetTickCount()
    faces = cv.HaarDetectObjects(small_img, self.face_cascade, cv.CreateMemStorage(0),
                   self.haar_scale, self.min_neighbors, self.haar_flags, self.min_size)
    t = cv.GetTickCount() - t
    print "face detection time = %gms" % (t/(cv.GetTickFrequency()*1000.))
    for ((x, y, w, h), n) in faces:
      w, h = force_aspect(w, h, self.aspect)

      crop_img = crop_img_with_margin(img, x,y,w,h, self.image_scale, 3, 2)
      if not crop_img: continue

      scale = 400.0/crop_img.height
      std_w = crop_img.width*scale
      std_h = crop_img.height*scale
      std_img = cv.CreateImage((std_w, std_h) , cv.IPL_DEPTH_8U, img.nChannels)
      cv.Resize(crop_img, std_img, cv.CV_INTER_LINEAR)
      cv.ShowImage("result", std_img)
      processor(std_img)

  def find_eyes(self, img):
    t = cv.GetTickCount()
    eyes = cv.HaarDetectObjects(img, self.eye_cascade, cv.CreateMemStorage(0),
                   self.haar_scale, self.min_neighbors, self.haar_flags, self.min_size)
    t = cv.GetTickCount() - t
    print "eye detection time = %gms" % (t/(cv.GetTickFrequency()*1000.))
    for ((x, y, w, h), n) in eyes:
      print "found", x,y,w,h
      cv.Rectangle(img, (int(x), int(y)), (int(x+w), int(y+h)), cv.RGB(255, 0, 0), 3, 8, 0)


def UploadImage(img, url):
  jpegdata = base64.b64encode(cv.EncodeImage(".jpeg", img).tostring())
  params = {"img": jpegdata}
  request = urllib2.Request(url,  urllib.urlencode(params))
  request.add_header("Content-type", "application/x-www-form-urlencoded; charset=UTF-8")
  try:
    page = urllib2.urlopen(request)
  except urllib2.URLError as e:
    print "Error connecting to picture server: ", url
    print e


if __name__ == '__main__':

  parser = OptionParser(usage = "usage: %prog [options]")
  parser.add_option("-f", "--face", action="store", dest="face", type="str", help="Haar cascade file for faces")
  parser.add_option("-e", "--eye", action="store", dest="eye", type="str", help="Haar cascade file for eyes")
  parser.add_option("-c", "--camera", action="store", dest="camera", type="int", help="Camera index", default=0)
  (options, args) = parser.parse_args()
  face_cascade = cv.Load(options.face)
  eye_cascade = cv.Load(options.eye)
  faceex = FaceExtractor(face_cascade, eye_cascade)
  
  input_name = '0' 
  capture = cv.CreateCameraCapture(int(options.camera))
   
  while True:
     frame = cv.QueryFrame(capture)
     if not frame:
       continue
     frame_copy = cv.CreateImage((frame.width,frame.height), cv.IPL_DEPTH_8U, frame.nChannels)
     cv.Copy(frame, frame_copy)

     faceex.find_faces(frame, lambda img: UploadImage(img, picurl))
     if cv.WaitKey(5000) == 27:
       break
    

 
