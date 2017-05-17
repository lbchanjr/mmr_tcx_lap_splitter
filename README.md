# MapMyRun TCX Lap Splitter (mmrtcxlapsplitter.py) #

### What is this repository for? ###
MapMyRun allows you to export a workout in TCX format so that you may be able to import it to other fitness accounts such as Garmin Connect or Strava. The only caveat is that the exported tcx file will only contain a single-lap workout regardless of how many laps the workout was originally split into.

For example, a MapMyRun workout covering a total distance of 10 km and split into 1-km laps will still be exported as a tcx workout containing only a single 10-km lap.

This is a pain for users who would want their exported workouts split into specific lap distances so that metrics for each lap (lap pace, lap time, lap average HR, etc...) can still be viewed even for imported workouts.

This limitation of MapMyRun's export function is fixed by this tool by allowing you to split an exported MapMyRun tcx workout according to the lap distance that you want.

* Quick summary
A tool for converting a single-lap TCX file exported using MapMyRun into a TCX file containing multiple laps spit according to how the user would want the laps to be split.
* Version
v0.0.4-beta2

### How do I get set up? ###

* Summary of set up
1.) Requires Python 3
* Configuration
1.) Install Python 3 on your computer.
2.) Run script by typing 'python mmrtcxlapsplitter.py' on the command prompt.
3.) Specify the lap distance to split the workout into by moving the slide bar beside "Split every:".
4.) Select the exported MapMyRun tcx file by clicking on "Select File..."
5.) Choose the TCX file on the file open dialog box and click "Open"
6.) In the same directory where the selected file was contained, a new file name with the same filename+"-split".tcx will be created.
7.) This filename is the new TCX file that was split according to the lap distance that you specified and can now be imported to other fitness accounts such as Garmin Connect or Strava.

### Who do I talk to? ###

* Repo owner or admin
For any questions, bug reports or improvement suggestions you may email me at: lbchan525@gmail.com
