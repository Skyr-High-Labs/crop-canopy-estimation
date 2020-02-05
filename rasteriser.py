import numpy as np
import matplotlib.pyplot as plt
import cv2

# rotate point cloud
def rotateByDeg(latDeg, lonDeg, latRot, lonRot):
    lat = np.radians(latDeg)
    lon = np.radians(lonDeg)
    latRot = np.radians(latRot)
    lonRot = np.radians(lonRot)
    x = np.cos(lon)*np.cos(lat)
    y = np.sin(lon)*np.cos(lat)
    z = np.sin(lat)
    Rz = np.array((
        ( np.cos(lonRot),np.sin(lonRot)),
        (-np.sin(lonRot),np.cos(lonRot)) ))
    Ry = np.array((
        ( np.cos(latRot),np.sin(latRot)),
        (-np.sin(latRot),np.cos(latRot)) ))
    x,y = Rz @ (x,y)
    x,z = Ry @ (x,z)
    lat = np.arcsin(z)
    lon = np.arctan2(y,x)
    return np.degrees(lat), np.degrees(lon)

def getRasteriserFunction(lat, lon):
    #get mean coordinates
    latm, lonm = np.mean(lat), np.mean(lon)

    #rotate to origin
    lat, lon = rotateByDeg(lat, lon, latm, lonm)

    minLat = np.min(lat)
    maxLat = np.max(lat)
    minLon = np.min(lon)
    maxLon = np.max(lon)

    scale = 10/(6371000*np.pi/180) #10m in degrees : 10m / degree arc length -> earth radius * pi / 180 degrees 
    imageSize = ((maxLat-minLat)/scale,(maxLon-minLon)/scale)
    imageSize = np.int_(np.floor(imageSize)+1)

    def coordToPixel(lat, lon):
        return tuple(np.int_(np.floor(((lat - minLat)/scale, (lon - minLon)/scale))))

    def rasteriseImage(lat, lon, data):
        image = np.zeros(imageSize)
        imageSampled = np.zeros(imageSize)

        # rasterise point cloud
        for i in range(0, len(data)):
            px = coordToPixel(lat[i], lon[i])
            alpha = imageSampled[px] / (imageSampled[px]+1)
            imageSampled[px] += imageSampled[px] + 1
            image[px] = alpha*image[px] + (1-alpha)*data[i]

        # get mask for geometry and inpaint undersampled pixels
        kernel = np.ones((5,5), np.uint8)
        roiMask = cv2.erode(cv2.dilate(np.uint8(imageSampled>0), kernel), kernel)
        inpainted = cv2.inpaint(np.float32(image),np.uint8(imageSampled==0),3,cv2.INPAINT_NS)
        image = inpainted*roiMask

        return image, roiMask

    return rasteriseImage

def rasteriseImages(lat, lon, data, label):
    rasteriser = getRasteriserFunction(
        [i for series in lat for i in series], 
        [i for series in lon for i in series])
    rasterised = [rasteriser(lat[i],lon[i],data[i]) for i in range(len(data))]
    roiMask = np.median(np.array([image[1] for image in rasterised]),0)

    kernel = np.ones((3,3), np.uint8)
    roiMask = cv2.erode(roiMask, kernel)
    images = []
    for i in range(len(rasterised)):
        if not np.any(roiMask * np.logical_not(rasterised[i][1])):
            # image covers roi
            images.append((roiMask * rasterised[i][0], label[i]))
    return images, roiMask