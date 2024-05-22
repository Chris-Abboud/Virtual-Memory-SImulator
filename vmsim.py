from collections import deque
from collections import OrderedDict
import math
import time
import random
import sys


"""
VMSIM For Python

Input Syntax:
$ python vmsim.py -n <numframes> -a <opt|rand|clock|nru> [-r <refresh>] <tracefile>
"""
class Page():
    def __init__(self, page_id, dirty = False, referenced = False, modified = False):
        self.page_id = page_id
        self.dirty = dirty
        self.referenced = referenced
        self.modified  = modified
    
    def __str__(self):
        print("Page ID:\t{}".format(self.page_id))
        print("Dirty:\t\t{}".format(self.dirty))
        print("Referenced:\t{}".format(self.referenced))
        print("Modified:\t{}".format(self.modified))
        return "-------"

class PageTable():
    writeCount = 0
    pageFaultCount = 0
    memAccessCount = 0
    clock = 0
    activeFrames = OrderedDict()

    def __init__(self, numFrames, evictMode, evictModeStr, refreshRate, debugMode):
        self.TOTAL_FRAMES = numFrames
        self.evictMode = evictMode
        self.debugMode = debugMode
        self.evictModeStr = evictModeStr
        self.refreshRate = refreshRate
        if self.debugMode: print("DEBUG MODE {}".format(self.debugMode))
    def lookup(self, frame):
        self.incMemAccessCount()
        if self.activeFrames.has_key(frame):
            # Meaning We Hit
            if self.debugMode: print("Hit")
            if self.debugMode: print(self)

            # Set Referenced Bit To True
            self.activeFrames[frame].referenced = True
            self.lastKey = frame
            return [frame, "Hit"]
        else:
            # Didn't Already Exist In Memory
            self.incPageFaultCount()

            if self.debugMode: print("Comparison: {}".format(len(self.activeFrames) < self.TOTAL_FRAMES))

            # Check if we have enough space in cache to add the frame
            if len(self.activeFrames) < self.TOTAL_FRAMES:
                newFrame = Page(frame)
                if self.debugMode: print("Frame Added: {}".format(frame))
                self.activeFrames[frame] = newFrame

                if self.debugMode: print(self)
                return [frame, "page fault - no eviction"]
            else:
                # If we don't have enough space, we must first choose a frame to evict
                removedFrame = self.evictMode.evict(self.activeFrames)
                if self.evictModeStr == "clock": self.activeFrames = self.evictMode.activeFrames

                if self.debugMode: print("Evicting Frame: {}".format(removedFrame))

                status = "page fault - evict clean"
                # if Dirty, must be re-written to disk
                if self.activeFrames[removedFrame].dirty:
                    status = "page fault - evict dirty"
                    #print("ABOUTA INCREMENT WRITE COUNT")
                    self.incWriteCount()
                    #print("DONT ICNREMENTING")
                    #print(self.writeCount)

                self.replaceKeyDict(removedFrame, frame)
                
                # Remove Frame From Dictionary
                #self.activeFrames.pop(removedFrame, None)
                # Then Add New Frame To Dictionary
                #newFrame = Page(frame)
                #self.activeFrames[frame] = newFrame

                if self.debugMode: print(self)
                return [frame, status]
    
    def replaceKeyDict(self, oldKey, frame):
        temp = list(self.activeFrames)
        temp[temp.index(oldKey)] = frame

        newDict = OrderedDict()
        
        for key in self.activeFrames:
            if key == oldKey:
                newDict[frame] = Page(frame)
            else:
                newDict[key] = self.activeFrames[key]
        
        self.activeFrames = newDict
            

        
        newFrame = Page(frame)
        self.activeFrames[frame] = newFrame

    def setDirty(self, frame):
        self.activeFrames[frame].dirty = True
        self.activeFrames[frame].modified = True

    def incWriteCount(self):
        self.writeCount +=1 
    
    def incPageFaultCount(self):
        self.pageFaultCount +=1 
    
    def incMemAccessCount(self):
        self.memAccessCount +=1 

    def I(self, pageLocation, hexVal):
        returnVal = self.lookup(pageLocation)
        frame = returnVal[0]
        self.activeFrames[frame].referenced = True
        status = returnVal[1]
        print(hexVal +"\t"+ status)

        # Evict Frame after every instruction in opt
        if self.evictModeStr == "opt": self.evictMode.dict[frame].popleft()

        self.clock+=1
        if self.evictModeStr == "nru":
            if self.clock % self.refreshRate == 0:
                self.evictMode.reset(self.activeFrames)



    def S(self, pageLocation, hexVal, temp = False):
        returnVal = self.lookup(pageLocation)
        frame = returnVal[0]
        self.activeFrames[frame].referenced = True
        status = returnVal[1]
        self.setDirty(frame)
        print(hexVal +"\t"+ status)

        # For S instructions -> So we dont deque twice
        if not temp:
            if self.evictModeStr == "opt": self.evictMode.dict[frame].popleft()
            self.clock+=1

        if self.evictModeStr == "nru":
            if self.clock % self.refreshRate == 0:
                self.evictMode.reset(self.activeFrames)

    


    def L(self, pageLocation, hexVal):
        returnVal = self.lookup(pageLocation)
        frame = returnVal[0]
        self.activeFrames[frame].referenced = True
        status = returnVal[1]
        print(hexVal + "\t" + status)

        # Evict Frame after every instruction in opt
        if self.evictModeStr == "opt": 
            self.evictMode.dict[frame].popleft()
            self.clock+=1
        
        if self.evictModeStr == "nru":
            if self.clock % self.refreshRate == 0:
                self.evictMode.reset(self.activeFrames)



    def M(self, pageLocation, hexVal):
        self.L(pageLocation, hexVal)
        self.S(pageLocation, hexVal, True)

    def __str__(self):
        print("------------")
        print("Length: {} / {}".format(len(self.activeFrames), self.TOTAL_FRAMES))
        for key in self.activeFrames:
            print(self.activeFrames[key])
        
        return "--------------"


class setInputs():
    # Get Arguments Ready
    def __init__(self, args):
        # Check if -r Refresh Flag
        self.numFrames = int(args[2])

        if self.numFrames == 0:
            print("The Minimum Amount of Frames is 1, try again.")
            sys.exit(0)
            
        self.refreshMode = False
        self.refreshTimer = 0
        self.mode = args[4]
        self.traceFile = args[5]
        
        if (len(args) == 8):
            self.refreshMode = True
            self.refreshTimer = int(args[6])
            self.traceFile = args[7]
            
        self.input = self.openFile()

    def openFile(self):
        temp = []

        file = open(self.traceFile, "r")
        allLines = file.readlines()[6:]

        for line in allLines:
            line = line.replace(",", " ")
            line = line.split()

            if len(line) == 3:
                temp.append(line)
        """
        [[ "I", "958132", "15"],
        [ "I", "958132", "15"],
        [ "I", "958132", "15"]]
        """
        return temp

class opt():
    """ 
    Data Structure:

    {
        Address: [Location1 -> Location 2 -> Location3]
        Address2: [Location 1 -> Location 2 -> Location3]
    }

    """
    def __init__(self, data, debugMode):
        self.dict = {}
        self.debugMode = debugMode
        count = 0
        # Preprocess Data
        for i in range(len(data)):
            operation = data[i]
            address = math.floor(int(operation[1], 16) / (2 ** 11))

            #If Does exist, add its next appearance
            if address in self.dict:
                self.dict[address].append(i)
            # If Doesnt exist, make
            else:
                temp = deque()
                temp.append(i)
                self.dict[address] = temp

        if self.debugMode: print(self.dict)

    # Chooses a frame to evict
    def evict(self, activeFrames):
        currMax = 0
        maxFrame = 0

        if self.debugMode:
            for frame in activeFrames:
                print(frame)
        for frame in activeFrames:
            # Meaning it does not appear again - remove it
            if not self.dict[frame]:
                return frame
            else:
                # Check which has the largest value
                if self.debugMode: print("Frame: {} TOP: {}".format(frame, self.dict[frame][0]))
                if self.dict[frame][0] > currMax:
                    currMax = self.dict[frame][0]
                    maxFrame = frame


        if self.debugMode: print("Before {}".format(self.dict))
        if self.debugMode: print("Decided Frame To Remove {}".format(maxFrame))


        #self.dict[maxFrame].popleft()
        if self.debugMode: print("After {}".format(self.dict))
        if self.debugMode: print(self.dict)

        return maxFrame

class rand():
    def evict(self, activeFrames):
        return random.choice(list(activeFrames))

class clock():
    """
    Better implementation of second chance algorithm
    """
    def __init__(self, debugMode = False):
        self.startIndex = 0
        self.debugMode = debugMode

    def setStartIndex(self, index):
        self.startIndex = index


    def evict(self, activeFrames):
        listDict = list(activeFrames)
        startIndex = self.startIndex

        if self.debugMode:
            print("STARTING FRAME: {}".format(listDict[startIndex]))
            print("Active Frames Before")
            for key in activeFrames:
                print(activeFrames[key])

        for i in range(len(listDict)):
            # Check if the frame is not referenced
            if not activeFrames[listDict[startIndex]].referenced:
                # Return the key of the one we want to evict

                self.activeFrames = activeFrames
               
                if self.debugMode:
                    print("Active Frames After")
                    for key in activeFrames:
                        print(activeFrames[key])

                self.setStartIndex(startIndex)
                return listDict[startIndex]

            # If the frame is referenced, set to not referenced
            if activeFrames[listDict[startIndex]].referenced:
                activeFrames[listDict[startIndex]].referenced = False

            startIndex+=1
            if startIndex >= len(listDict):
                startIndex = 0

        #ALl Unreferenced. Just return Original
        self.activeFrames = activeFrames
        self.setStartIndex(startIndex)
        
        if self.debugMode:
            print("Active Frames After")
            for key in activeFrames:
                print(activeFrames[key])
        return listDict[self.startIndex]

        # Go From Start Frame, go rightwards. If currently referenced, change to not referenced.
        # Once we hit a not referenced, we kick out and return that frame to then be replaced.



class nru():
    def reset(self, activeFrames):
        for address in activeFrames:
            activeFrames[address].referenced = False
    
    def evict(self, activeFrames):

        for frame in activeFrames:
            currFrame = activeFrames[frame]
            if not currFrame.referenced and not currFrame.modified:
                return frame
        
        for frame in activeFrames:
            currFrame = activeFrames[frame]
            if not currFrame.referenced and currFrame.modified:
                return frame
        
        for frame in activeFrames:
            currFrame = activeFrames[frame]
            if currFrame.referenced and not currFrame.modified:
                return frame
        
        for frame in activeFrames:
            currFrame = activeFrames[frame]
            if currFrame.referenced and currFrame.modified:
                return frame

    
def main():
    startTime = time.time()
    print("Pre-Processing Data")
    inputParams = setInputs(sys.argv)
    print("Finished Pre-Processing Data")
    if inputParams.mode == "opt":
        evictMode = opt(inputParams.input, debugMode = False )

    if inputParams.mode == "rand":
        evictMode = rand()

    if inputParams.mode == "clock":
        evictMode = clock(debugMode = False)

    if inputParams.mode == "nru":
        evictMode = nru()

    pageTableDebug = False
    pageTable = PageTable(inputParams.numFrames, evictMode, inputParams.mode, inputParams.refreshTimer, debugMode = pageTableDebug)

    for operation in inputParams.input:
        #print(operation)
        #Input: [Mode, Location, Size]
        if pageTableDebug: input("Step: ")
        mode = operation[0] # R / W
        hexVal = operation[1]

        pageLocation = math.floor(int(hexVal, 16) / (2 ** 11))# Get Page #

        if mode == "I":
            pageTable.I(pageLocation, hexVal)

        if mode == "S":
            pageTable.S(pageLocation, hexVal)

        if mode == "L":
            pageTable.L(pageLocation, hexVal)

        if mode == "M":
            pageTable.M(pageLocation, hexVal)

    print("Algorithm: {}".format(inputParams.mode))
    print("Number of frames:\t{}".format(inputParams.numFrames))
    print("Total memory accesses:\t{}".format(pageTable.memAccessCount))
    print("Total page faults:\t{}".format(pageTable.pageFaultCount))
    print("Total writes to disk:\t{}".format(pageTable.writeCount))
    
    print("Time: {} Seconds".format(round(time.time() - startTime, 2)))
    #print(evictMode.dict)

if __name__ == '__main__':
    main()