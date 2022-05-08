import cv2
import tcod

mapp = cv2.imread("test.png", cv2.IMREAD_GRAYSCALE) #Maybe needs to be of uin16(?) to accomodate for cost
mapp[mapp<240] = 0

cv2.imshow('image',mapp)
cv2.waitKey(0)

graph = tcod.path.SimpleGraph(cost=mapp, cardinal=1, diagonal=0)
pf = tcod.path.AStar(mapp, 0)

p = pf.get_path(60, 60, 65, 65)

for x, y in p:
    mapp[x, y] = 127

cv2.imwrite("astar.png", mapp)



oietnhaoin = 5