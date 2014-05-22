from flask import Flask, request, make_response,render_template
import base64
app = Flask(__name__)

class RingBuffer():
  def __init__(self, size): 
    self.size = size 
    self.store = [None]*self.size
    self.next_post = 0
    self.next_get = 0

  def put(self, data):
    self.store[self.next_post] = data 
    self.next_post += 1
    if self.next_post >= self.size:
      self.next_post = 0 

  def get(self):
    if not self.store[self.next_get]:
      self.next_get = 0
      return None 
    data = self.store[self.next_get] 
    self.next_get += 1
    if self.next_get >= self.size:
      self.next_get = 0 
    if not self.store[self.next_get]:
      self.next_get = 0
    return data

store = RingBuffer(10)

@app.route("/")
def display_canvas():
  return render_template('index.html')

@app.route("/raw")
def get_image():
  global store
  image_binary = store.get()
  if not image_binary:
    return ""
  response = make_response(image_binary)
  response.headers['Content-Type'] = 'image/jpeg'
  #response.headers['Content-Disposition'] = 'attachment; filename=img.jpg'
  return response

@app.route("/", methods=['POST'])
def post_image():
  global store 
  store.put(base64.b64decode(request.form['img'])) 
  return "" 

if __name__ == "__main__":
    app.run(debug=True)
