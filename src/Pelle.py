from breezyslam.vehicles import WheeledVehicle
import time

class Pelle(WheeledVehicle):
    def __init__(self):
        WheeledVehicle.__init__(self, 51, 90)
        
        self.ticks_per_cycle = 1248
                        
    def __str__(self):
        
        return '<%s ticks_per_cycle=%d>' % (WheeledVehicle.__str__(self), self.ticks_per_cycle)
        
    def computePoseChange(self, left_wheel, right_wheel):
        
        return WheeledVehicle.computePoseChange(self, time.time(), left_wheel, right_wheel)

    def extractOdometry(self, timestamp, leftWheel, rightWheel):
                
        # Convert microseconds to seconds, ticks to angles        
        return timestamp, \
               self._ticks_to_degrees(leftWheel), \
               self._ticks_to_degrees(rightWheel)
               
    def odometryStr(self, odometry):
        
        return '<timestamp=%d usec leftWheelTicks=%d rightWheelTicks=%d>' % \
               (odometry[0], odometry[1], odometry[2])
               
    def _ticks_to_degrees(self, ticks):
        
        return ticks * (360. / self.ticks_per_cycle)
        