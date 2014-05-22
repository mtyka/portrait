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
import collections
from optparse import OptionParser

std_w=600
std_h=400


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
      print "Aspect: ", crop_img.width, crop_img.height, crop_img.width / crop_img.height
      std_img = cv.CreateImage((std_w, std_h) , cv.IPL_DEPTH_8U, img.nChannels)
      std_img2 = cv.CreateImage((std_w, std_h) , cv.IPL_DEPTH_8U, img.nChannels)
      cv.Resize(crop_img, std_img, cv.CV_INTER_LINEAR)
      cv.Resize(crop_img, std_img2, cv.CV_INTER_LINEAR)
      
      smooth = cv.CreateImage((std_w, std_h) , cv.IPL_DEPTH_8U, img.nChannels)
      final = cv.CreateImage((std_w, std_h) , cv.IPL_DEPTH_8U, img.nChannels)
      laplacian = cv.CreateImage((std_w, std_h) , cv.IPL_DEPTH_8U, img.nChannels)
      
      cv.Smooth(std_img, final, smoothtype=cv.CV_BILATERAL)
      cv.Smooth(final, std_img, smoothtype=cv.CV_BILATERAL)
      cv.Smooth(std_img, final, smoothtype=cv.CV_BILATERAL)
      cv.Smooth(final, std_img, smoothtype=cv.CV_BILATERAL)

      cv.Smooth(final, smooth, param1=5)
      cv.Laplace(final, laplacian, 5) 

      cv.AddWeighted(std_img, 3.0, smooth, -2.0, 0.0, final) 
      cv.AddWeighted(std_img, 1.0, laplacian, -0.15, 0.0, final) 
     
      stacked = cv.CreateImage((std_w, std_h*2) , cv.IPL_DEPTH_8U, img.nChannels)
      cv.SetImageROI( stacked, ( 0, 0, std_w, std_h) ) 
      cv.Copy(final, stacked)
      cv.ResetImageROI(stacked)
      cv.SetImageROI( stacked, ( 0, std_h, std_w, std_h) ) 
      cv.Copy(std_img2, stacked)
      cv.ResetImageROI(stacked)

      cv.ShowImage("result", stacked)
      processor(final)

  def find_eyes(self, img):
    t = cv.GetTickCount()
    eyes = cv.HaarDetectObjects(img, self.eye_cascade, cv.CreateMemStorage(0),
                   self.haar_scale, self.min_neighbors, self.haar_flags, self.min_size)
    t = cv.GetTickCount() - t
    print "eye detection time = %gms" % (t/(cv.GetTickFrequency()*1000.))
    for ((x, y, w, h), n) in eyes:
      print "found", x,y,w,h
      cv.Rectangle(img, (int(x), int(y)), (int(x+w), int(y+h)), cv.RGB(255, 0, 0), 3, 8, 0)

class Uploader():
  def __init__(self, url):
    self.url = url
    self.buf = collections.deque() 
    pass

  def CheckImageDiff(self, img):
    diff = cv.CreateImage((std_w, std_h), 8, 1) 
    gray = cv.CreateImage((std_w, std_h), 8, 1)
    cv.CvtColor(img, gray, cv.CV_BGR2GRAY );

    lowest = None
    for ref in self.buf:
      if not ref: continue
      cv.AbsDiff(ref, gray, diff);
      absdiff = cv.Sum(diff);
      if not lowest: lowest = absdiff
      else: lowest = min(lowest, absdiff)
    threshold = 3.0
    if lowest:
      print "Lowest diff: ", lowest[0]*1.0/std_w/std_h
    if not lowest or lowest[0] > threshold*std_h*std_w:
      self.buf.append(gray)
      if len(self.buf) > 40:
        self.buf.popleft()
      return True
    return False

  def UploadImage(self, img):
#    if not self.CheckImageDiff(img):
#      print "REJECT"
#      return

    jpegdata = base64.b64encode(cv.EncodeImage(".jpeg", img).tostring())
    params = {"img": jpegdata}
    request = urllib2.Request(self.url,  urllib.urlencode(params))
    request.add_header("Content-type", "application/x-www-form-urlencoded; charset=UTF-8")
    try:
      page = urllib2.urlopen(request)
    except urllib2.URLError as e:
      print "Error connecting to picture server: ", self.url
      print e


if __name__ == '__main__':

  parser = OptionParser(usage = "usage: %prog [options]")
  parser.add_option("-f", "--face", action="store", dest="face", type="str", help="Haar cascade file for faces")
  parser.add_option("-e", "--eye", action="store", dest="eye", type="str", help="Haar cascade file for eyes")
  parser.add_option("-c", "--camera", action="store", dest="camera", type="int", help="Camera index", default=0)
  parser.add_option("-u", "--url", action="store", dest="url", type="str", help="URL for uploader", default="http://localhost:5000")
  parser.add_option("", "--jpeg", action="store", dest="jpeg", type="str", help="Manual file upload") 
  (options, args) = parser.parse_args()
  
  uploader = Uploader(options.url)

  if options.jpeg:
    img = cv.LoadImage(options.jpeg)
    uploader.UploadImage(img) 
    sys.exit(0) 
  
  face_cascade = cv.Load(options.face)
  eye_cascade = cv.Load(options.eye)
  faceex = FaceExtractor(face_cascade, eye_cascade)
  
  capture = cv.CreateCameraCapture(int(options.camera))
 
  while True:
     frame = cv.QueryFrame(capture)
     if not frame:
       continue
     frame_copy = cv.CreateImage((frame.width,frame.height), cv.IPL_DEPTH_8U, frame.nChannels)
     cv.Copy(frame, frame_copy)

     faceex.find_faces(frame, uploader.UploadImage)
     if cv.WaitKey(100) == 27:
       break
    
