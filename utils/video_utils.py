import cv2
import numpy as np

def compute_histogram(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0, 1, 2], None, [8, 8, 8], [0, 180, 0, 256, 0, 256])
    cv2.normalize(hist, hist)
    return hist

def overlay_event_text(frame, text="EVENT"):
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 3
    thickness = 4
    color = (0, 255, 0)

    text_size, _ = cv2.getTextSize(text, font, font_scale, thickness)
    text_x = (frame.shape[1] - text_size[0]) // 2
    text_y = (frame.shape[0] + text_size[1]) // 2

    cv2.putText(frame, text, (text_x, text_y), font, font_scale, color, thickness, cv2.LINE_AA)
    return frame