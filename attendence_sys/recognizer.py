# import cv2
# import numpy as np
# from facenet_pytorch import MTCNN, InceptionResnetV1
# import torch
# from sklearn.preprocessing import LabelEncoder
# import os

# def Recognizer(details):
#     # Initialize MTCNN (for face detection) and InceptionResnetV1 (for face recognition)
#     mtcnn = MTCNN(margin=20, keep_all=True)
#     model = InceptionResnetV1(pretrained='vggface2').eval()

#     # Initialize LabelEncoder for face identification
#     label_encoder = LabelEncoder()

#     # Load pre-encoded known faces and labels
#     known_face_encodings = []
#     known_face_labels = []

#     base_dir = os.path.dirname(os.path.abspath(__file__))
#     base_dir = os.getcwd()
#     image_dir = os.path.join(base_dir, r"static\images\Student_Images\{}\{}\{}".format(details['branch'], details['year'], details['section']))

#     for filename in os.listdir(image_dir):
#         img_path = os.path.join(image_dir, filename)
#         img = cv2.imread(img_path)
#         if img is None:
#             print(f"Error: Unable to read image {img_path}")
#             continue
#         faces = mtcnn(img)
#         if faces is not None:
#             for face in faces:
#                 face_embedding = model(face.unsqueeze(0))
#                 known_face_encodings.append(face_embedding.detach().cpu().numpy())
#                 known_face_labels.append(filename.split('.')[0])

#     label_encoder.fit(known_face_labels)

#     video = cv2.VideoCapture(0)
#     recognition_threshold = 0.8

#     # Initialize a set to keep track of recognized students
#     recognized_students = set()

#     while True:
#         ret, frame = video.read()
#         if not ret:
#             break

#         boxes, probs = mtcnn.detect(frame)
#         if boxes is not None:
#             faces = mtcnn(frame)
#             face_names = []

#             for i, face in enumerate(faces):
#                 embedding = model(face.unsqueeze(0))
#                 distances = [np.linalg.norm(embedding.detach().cpu().numpy() - known_face) for known_face in known_face_encodings]
#                 if distances:
#                     min_distance_index = np.argmin(distances)
#                     min_distance = distances[min_distance_index]
#                     if min_distance < recognition_threshold:
#                         label = known_face_labels[min_distance_index]
#                         recognized_students.add(label)  # Add recognized student to the set
#                         face_names.append(label)
#                     else:
#                         label = "Unknown"
#                         face_names.append(label)

#                     x1, y1, x2, y2 = boxes[i]
#                     cv2.putText(frame, label, (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
#                     cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)

#         cv2.imshow("Face Recognition Panel", frame)
#         if cv2.waitKey(1) == ord('q'):
#             break

#     video.release()
#     cv2.destroyAllWindows()

#     return list(recognized_students)

import cv2
import numpy as np
import torch
import os
from facenet_pytorch import MTCNN, InceptionResnetV1
from sklearn.preprocessing import LabelEncoder
from src.anti_spoof_predict import AntiSpoofPredict
from src.generate_patches import CropImage
from src.utility import parse_model_name
import time

class Recognizer:
    def __init__(self, details):
        # Store the details
        self.details = details
        
        # Initialize MTCNN for face detection and InceptionResnetV1 for recognition
        self.mtcnn = MTCNN(margin=20, keep_all=True)
        self.model = InceptionResnetV1(pretrained='vggface2').eval()

        # Initialize Anti-Spoofing Model
        device_id = 0
        model_dir = "./resources/anti_spoof_models"
        self.spoof_model = AntiSpoofPredict(device_id)
        self.image_cropper = CropImage()
        self.models = [os.path.join(model_dir, model) for model in os.listdir(model_dir)]

        # Load Label Encoder
        self.label_encoder = LabelEncoder()

        # Load known faces
        self.known_face_encodings = []
        self.known_face_labels = []

        base_dir = os.getcwd()
        image_dir = os.path.join(base_dir, r"static\images\Student_Images\{}\{}\{}".format(details['branch'], details['year'], details['section']))

        for filename in os.listdir(image_dir):
            img_path = os.path.join(image_dir, filename)
            img = cv2.imread(img_path)
            if img is None:
                print(f"Error: Unable to read image {img_path}")
                continue
            faces = self.mtcnn(img)
            if faces is not None:
                for face in faces:
                    face_embedding = self.model(face.unsqueeze(0))
                    self.known_face_encodings.append(face_embedding.detach().cpu().numpy())
                    self.known_face_labels.append(filename.split('.')[0])

        self.label_encoder.fit(self.known_face_labels)
        self.recognition_threshold = 0.8
        self.recognized_students = set()

    def process_frame(self, frame, details=None):
        # Use stored details if none provided
        details = details or self.details
        
        boxes, probs = self.mtcnn.detect(frame)
        if boxes is not None:
            faces = self.mtcnn(frame)
            face_names = []

            for i, face in enumerate(faces):
                x1, y1, x2, y2 = map(int, boxes[i])

                # Anti-Spoofing Check
                prediction = np.zeros((1, 3))
                for model_path in self.models:
                    h_input, w_input, model_type, scale = parse_model_name(os.path.basename(model_path))
                    param = {"org_img": frame, "bbox": [x1, y1, x2 - x1, y2 - y1], "scale": scale, "out_w": w_input, "out_h": h_input}
                    img = self.image_cropper.crop(**param)
                    prediction += self.spoof_model.predict(img, model_path)

                label_spoof = np.argmax(prediction)

                if label_spoof == 1:  # Real Face
                    embedding = self.model(face.unsqueeze(0))
                    distances = [np.linalg.norm(embedding.detach().cpu().numpy() - known_face) for known_face in self.known_face_encodings]

                    if distances:
                        min_distance_index = np.argmin(distances)
                        min_distance = distances[min_distance_index]

                        if min_distance < self.recognition_threshold:
                            label = self.known_face_labels[min_distance_index]
                            self.recognized_students.add(label)  # Add to recognized students
                            face_names.append(label)
                        else:
                            label = "Unknown"
                            face_names.append(label)

                        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                else:  # Fake Face Detected
                    cv2.putText(frame, "Fake Face", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)

        return frame

    def get_recognized_students(self):
        return list(self.recognized_students)

    def get_details(self):
        return self.details


