from sklearn.metrics.pairwise import cosine_similarity
import cv2
import numpy as np

def artwork_similarity(img1, img2):
    """
    Computes visual similarity percentage between two images.
    Resizes both images to 128x128 to ensure shape alignment before flattening.
    
    Parameters:
    - img1: numpy array representing first image
    - img2: numpy array representing second image
    
    Returns:
    - similarity_score: float value (0.0 to 100.0)
    """
    # Convert BGR to Grayscale for structural detail comparison
    if len(img1.shape) == 3:
        if img1.shape[2] == 4:
            img1 = img1[:, :, :3]
        g1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    else:
        g1 = img1
        
    if len(img2.shape) == 3:
        if img2.shape[2] == 4:
            img2 = img2[:, :, :3]
        g2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    else:
        g2 = img2

    # Resize to standard size
    g1_resized = cv2.resize(g1, (128, 128))
    g2_resized = cv2.resize(g2, (128, 128))

    f1 = g1_resized.flatten().astype(float)
    f2 = g2_resized.flatten().astype(float)

    similarity = cosine_similarity([f1], [f2])[0][0]

    # Convert cosine range [-1, 1] to [0, 100]
    similarity_percentage = (similarity + 1.0) / 2.0 * 100.0

    return round(similarity_percentage, 2)