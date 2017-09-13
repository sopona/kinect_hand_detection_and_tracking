from freenect import sync_get_depth as get_depth
import numpy as np
import cv2
import math
import pygame

BLACK = (0,0,0)
RED = (255,0,0)
GREEN = (0,255,0)
PURPLE = (255,0,255)
BLUE = (0,0,255)
WHITE = (255,255,255)
YELLOW = (255,255,0)

class BlobAnalysis:
    def __init__(self,contour):
        self.contour = contour
        self.contour_s = np.vstack(contour).squeeze()
    
    def contour_point(self):
        return np.array(self.contour_s).tolist()
    
    def area(self):
        return cv2.contourArea(self.contour)
    
    def centroid(self):
        m = cv2.moments(self.contour)
        cX = int(m['m10'] / m['m00'])
        cY = int(m['m01'] / m['m00'])
        return (cX, cY)
    
    def convex_hull(self):
        convexHull = cv2.convexHull(self.contour)
        epsilon = 0.015*cv2.arcLength(convexHull,True)
        approx = cv2.approxPolyDP(convexHull,epsilon,True)
        approx = np.vstack(approx).squeeze()
        return np.array(approx).tolist()
    
    def approx_hull_count(self):
        approx = self.convex_hull()
        return len(approx)
    
    def deflect_count(self,max_angle):
        count = 0
        if self.approx_hull_count() >= 3:
            hull = cv2.convexHull(self.contour_s,returnPoints = False)
            defects = cv2.convexityDefects(self.contour_s, hull)
            for i in range(defects.shape[0]):
                s,e,f,d = defects[i,0]
                start = self.contour_s[s]
                end = self.contour_s[e]
                far = self.contour_s[f]
                a = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
                b = math.sqrt((far[0] - start[0])**2 + (far[1] - start[1])**2)
                c = math.sqrt((end[0] - far[0])**2 + (end[1] - far[1])**2)
                angle = math.acos((b**2 + c**2 - a**2)/(2*b*c)) * 57
                if angle <= max_angle:
                    count += 1
        return count
    
    def isHand(self):
        if self.deflect_count(90) == 4 :
            return True
        else:
            return False

def get_contours():
    (depth,_) = get_depth()
    depth = depth.astype(np.float32)
    depth = cv2.flip(depth, 1)
    min_depth = 400
    min_hand_depth = np.amin(depth)
    hand_depth = 120
    max_hand_depth = min_hand_depth + hand_depth
    if max_hand_depth > 700 :
        max_hand_depth = 700
    depth = cv2.GaussianBlur(depth, (5,5), 0)
    depth = cv2.erode(depth, None, iterations=2)
    depth = cv2.dilate(depth, None, iterations=2)
    (_,BW) = cv2.threshold(depth, max_hand_depth, min_depth, cv2.THRESH_BINARY_INV)
    BW = cv2.convertScaleAbs(BW)
    cs,_ = cv2.findContours(BW,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    cs_f = []
    for i in range(len(cs)):
        if cv2.contourArea(cs[i]) > 2000:
            cs_f.append(cs[i])
    del depth,BW
    return cs_f

def pygame_init(xsize,ysize):
    pygame.init()
    global screen
    screen = pygame.display.set_mode((xsize,ysize),pygame.RESIZABLE)
    pygame.font.init()
    global font
    font = pygame.font.SysFont('Liberation Mono', 11)

def pygame_refresh():
    screen.fill(BLACK)
    blobs = []
    cs = get_contours()
    for i in range(len(cs)):
        blob = BlobAnalysis(cs[i])
        blobs.append(blob)
    for blob in blobs:
        pygame.draw.lines(screen,GREEN,True,blob.convex_hull(),3)
        pygame.draw.lines(screen,YELLOW,True,blob.contour_point(),3)
        pygame.draw.circle(screen,RED,blob.centroid(),10)
        for tips in blob.convex_hull():
                pygame.draw.circle(screen,PURPLE,tips,5)
        if blob.isHand():
            blob_status = "THIS IS HAND!!!"
        else:
            blob_status = "Hull: %d Deflect90: %d" % (blob.approx_hull_count(),blob.deflect_count(90))
        blob_status_render = font.render(blob_status, True, WHITE)
        screen.blit(blob_status_render, blob.centroid())
    pygame.display.set_caption('Kinect Tracking')
    pygame.display.flip()

def main():
    pygame_init(640,480)
    while True:
        pygame_refresh()

main()