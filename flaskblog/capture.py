import cv2
import datetime, time
from pathlib import Path
from flaskblog import db
from flaskblog.models import Photo

def capture_and_save(id, im):
    s = im.shape

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
    if lp.exists() and lp.is_file():
        lastPath = direc + "/img_" + str(m) + ".png"
        print("lastPath 1", lastPath)
        np = Path(lastPath)
        np.write_bytes(lp.read_bytes())
    else:
        lastPath = direc + "/last.png"
        print("lastPath 2", lastPath)
    photo = Photo(user_id=id, path=lastPath)
    db.session.add(photo)
    db.session.commit()
    cv2.imwrite(direc + "/last.png",im)

    return lastPath

if __name__=="__main__":
    capture_and_save()
    print("done")