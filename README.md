# Virtual Memory Simulator

A useful way of testing various page replacement algorithms that an Operating System uses. The program will take in an initial tracefile, which will mock real memory instructions sampled by a running OS. The program will then output the total memory accesses, page faults, and writes to disk.

## How To Run

`vmsim –n <numframes> -a <opt|rand|clock|nru> [-r <refresh>] <tracefile>`

> -   numframes: Integer
> -   `<opt|rand|clock|nru>`: String - Page Replacement Algorithm you'd like to test
> -   refresh: Integer, only used for NRU - This is the refresh timer, will refresh after certain # of memory accesses
> -   tracefile: Example tracefile to run, has instructions of real memory accesses and operations

### Example Trace File

> -   I 0023C790,2 # instruction fetch at 0x0023C790 of size 2
> -   S BE80199C,4 # data store at 0xBE80199C of size 4
> -   L BE801950,4 # data load at 0xBE801950 of size 4
> -   M 0025747C,1 # data modify at 0x0025747C of size 1

### Output

Algorithm Name: `STRING` <br>
Total Memory Accesses: `INTEGER`<br>
Total Page Faults: `INTEGER`<br>
Total Writes To Disk: `INTEGER`
