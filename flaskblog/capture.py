import cv2
import numpy as np
from pathlib import Path
from flaskblog import db
from flaskblog.Model import predict_embedding
from flaskblog.models import Photo

def capture_and_save(id, im, gray):
    s = im.shape
    grayFaces = []

    m = 0
    direc = "images/" + str(id)
    Path(direc).mkdir(parents=True, exist_ok=True)
    p = Path(direc)
    for imp in p.iterdir():
        if imp.suffix == ".png" and imp.stem != "last":
            num = imp.stem.split("_")[1]
            try:
                num = int(num)
                if num>m:
                    m = num
            except:
                print("Error reading image number for",str(imp))
    m +=1
    lp = Path(direc + "/last.png")
    lpg = Path(direc + "/last_gray.png")
    le = Path(direc + "/last_Embedding.npy")
    if lp.exists() and lp.is_file() and lpg.exists() and lpg.is_file() and le.exists() and le.is_file():
        lastPath = direc + "/img_" + str(m) + ".png"
        lastPathGray = direc + "/img_" + str(m) + "_gray.png"
        lastEmbPath = direc + "/Embedding_" + str(m) + '.npy'
        nps = Path(lastPath)
        npg = Path(lastPathGray)
        npe = Path(lastEmbPath)

        nps.write_bytes(lp.read_bytes())
        npg.write_bytes(lpg.read_bytes())
        npe.write_bytes(le.read_bytes())
    else:
        lastPath = direc + "/last.png"
        lastPathGray = direc + "/last_gray.png"
        lastEmbPath = direc + "/last_Embedding.npy"
    
    grayFaces.append(gray)
    face_embedding = predict_embedding(grayFaces)

    np.save(lastEmbPath, face_embedding)
    photo = Photo(user_id=id, img_path=lastPath, emb_path=lastEmbPath)
    db.session.add(photo)
    db.session.commit()

    cv2.imwrite(direc + "/last.png",im)
    cv2.imwrite(direc + "/last_gray.png",gray)

    return lastPath, lastPathGray

if __name__=="__main__":
    capture_and_save()
    print("done")