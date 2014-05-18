float theta;   
int loopcount=0;
int N=2750;
int[] x = new int[N];
int[] y = new int[N];
int w;
int h;

void set_size() {
  w=window.innerWidth;
  h=window.innerHeight;
  size(w,h);
}

void setup() {
  set_size();
  for(int i=0;i<N;i++){  
  x[i]=int(random(width));
  y[i]=int(random(height));
  }
  background(0);
}

color get_color(int x, int y) {
  return get_pixel_color(x,y) 
}

void draw() {
  frameRate(30);
  init()  
  loopcount=loopcount+1;
  for(int i=0;i<N;i++){
   
    color pix = get_color(x[i],y[i]); 
    float grey = brightness(pix);
    float dev = 
      abs(grey-brightness(get_color(x[i],y[i]+1))) + 
      abs(grey-brightness(get_color(x[i]+1,y[i]))) + 
      abs(grey-brightness(get_color(x[i],y[i]-1))) + 
      abs(grey-brightness(get_color(x[i]-1,y[i]))) +
      
      abs(grey-brightness(get_color(x[i]+1,y[i]+1))) + 
      abs(grey-brightness(get_color(x[i]+1,y[i]-1))) + 
      abs(grey-brightness(get_color(x[i]-1,y[i]-1))) + 
      abs(grey-brightness(get_color(x[i]-1,y[i]+1))); 
    dev = dev / 8;
    
    boolean sharp = i%10 == 0;
    float stepsize;
    color stroke_c;
    if(sharp) {
      stepsize = 15/dev;
      if(stepsize<3) stepsize = 3;
      if(stepsize>30) stepsize = 30;
      stroke_c = color(red(pix)*1.1, green(pix)*1.0, blue(pix)*0.9, 75-stepsize*2);
    } else {
      boolean dark = i%2 == 0;
      if(dark) {
         grey = 255-grey; 
      }
      stepsize = grey/3;
      if(stepsize<3) stepsize = 3;
      if(stepsize>30) stepsize = 30;
      stroke_c = color(red(pix)+random(130)-60, green(pix)+random(130)-60, blue(pix)+random(130)-60, 75-stepsize*2);
    }
    
    stroke(stroke_c);  
   
    float dx=random(stepsize*2+1)-(stepsize);
    float dy=random(stepsize*2+1)-(stepsize);
    float newx = x[i] + dx;
    float newy = y[i] + dy;
    if(newx>=width) newx=width;
    if(newx<0) newx=0;
    if(newy>=height) newy=height;
    if(newy<0) newy=0;
    line(x[i],y[i],newx,y[i]);
    line(newx,y[i],newx,newy);
    x[i] = int(newx);
    y[i] = int(newy);
  }
}


