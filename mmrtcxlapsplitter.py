#!/usr/bin/python3
# mmrtcxlapsplitter.py by Louise Chan Jr.
# Opens a tcx file exported from the MapMyRun app and
# rebuilds the file to contain more than 1 lap.
# Copyright 2017 ChanSoft, LLC

import threading
import queue

from tkinter import *
from tkinter import ttk
from tkinter import filedialog

from datetime import datetime

entry = ''
lap_header = []


class TcxSplitSingleLap:
    # def __init__(self, filename, splitresKM=1.0):
    #     self._filename = filename
    #     self._splitresKM = splitresKM

    def __init__(self, **kwargs):
        self._filename = kwargs.get('file')
        if self._filename is None:
            raise Exception("Specify a filename to process using "
                            "the 'file=<filename>' option.")

        self._splitresKM = kwargs.get('split_res_KM', 1.0)
        self._progress = kwargs.get('progbar')
        self._pbarlabel = kwargs.get('pbarlabel')

    def getlinecount(self):
        _f = open(self._filename, 'rb')
        _fgen = make_gen(_f.raw.read)
        count = sum(_buf.count(b'\n') for _buf in _fgen)
        _f.close()
        return count

    def parseline(self):
        if self._progress is None:
            ParseLineInFile(self._filename, self._splitresKM)
        else:
            self.maxval = float(self.getlinecount())
            self.progbarpercent = IntVar()
            self.progbarpercent.set(0)
            self._progress.config(variable=self.progbarpercent)

            if self._pbarlabel is None:
                pass
            else:
                global label_percent
                label_percent = StringVar()
                label_percent.set("0%")
                self._pbarlabel.config(textvariable=label_percent)

            self.secondary_thread = threading.Thread(
                target=self._callparseline)
            self.secondary_thread.start()
            # check the Queue in 1ms
            global root
            root.after(1, self._check_que)

    def _check_que(self):
        while True:
            global que
            try:
                progbar_per, actual_per = que.get_nowait()
            except queue.Empty:
                if self.secondary_thread.is_alive() is True:
                    # if queue is empty, wait for another 1ms.
                    global root
                    root.after(1, self._check_que)
#                   print("Empty queue.. waiting another 50ms")
                break
            else:  # continue from the try suite

                self.progbarpercent.set(progbar_per)
                label_percent.set('{}%'.format(progbar_per))
#                print(actual_per)

#                print("DEQUEUED! {}".format(self.progbarpercent.get()))
                # if x == 4:
                #     self.b_start['state'] = 'normal'
                #     break

    def _callparseline(self):
        ParseLineInFile(self._filename, self._splitresKM,
                        self.progbarpercent, self.maxval)
        # ParseLineInFile(_f, self._splitresKM)

def make_gen(reader):
    b = reader(1024 * 1024)
    while b:
        yield b
        b = reader(1024 * 1024)

# arg[0] = line count, arg[1] = max lines in file
def ParseLineInFile(file, splitresKM, *args):

    file_obj = open(file)

    # make a copy of the line count for the file
    max_lines = args[1]

    # Generate filename to use for the output file using the input file.
    outf = file.split('.')
    if len(outf) == 1:
        raise Exception("Not a .tcx file.")
    else:
        outf[len(outf) - 2] = outf[len(outf) - 2] + '-split'
        outfilename = '.'.join(outf)

    # Test if TCX file has newlines or is one big chunk
    # of test.
    bufstr = file_obj.read(50)
    file_obj.seek(0)        # reset file pointer to the beginning of file
    if bufstr.find('\x0a') < 0:
        # file has no newline character, convert it to a
        # file that is delimited by newline for each tag and value
        bufstr = file_obj.read()
        bufstr = bufstr.replace('>', '>\x0a')
        cur_index = 0
        while cur_index >= 0:
            cur_index = bufstr.find('</', cur_index)
            if cur_index >= 0:
                if bufstr[cur_index - 1].isdigit() is True:
                    bufstr = bufstr[:cur_index] + '\x0a' + bufstr[cur_index:]
                    cur_index += 2
                else:
                    cur_index += 1

        file_obj.close()

        # Write buffer to temp file that will be worked on
        outf = outfilename.split('-split')
        outf[len(outf) - 2] = outf[len(outf) - 2] + '-linesep'
        newfilename = outf[len(outf) - 2] + '.tcx'
        outfile_obj = open(newfilename, mode='w', newline='\n')
        outfile_obj.write(bufstr)
        outfile_obj.close()

        outfile_obj = open(newfilename, 'rb')
        fgen = make_gen(outfile_obj.raw.read)
        max_lines = sum(buf.count(b'\n') for buf in fgen)
        outfile_obj.close()

        #print(max_lines)

        # setup file object to read based on the newly created file
        file_obj = open(newfilename)

#        print(file_obj)
    # open output file
    outfile_obj = open(outfilename, mode='w', newline='\n')
#    print(outfilename, outfile_obj)

    # LAP VARIABLES
#    LapTotalTimeSeconds = 0.0
    LapDistanceMeters = 0.0
    LapString = ''
    LapHRList = []

    # PARSE FLAGS
    found_lap = False
    found_track = False
    found_lap_time = False

    found_something = False
    found_time = False
    found_heartrate = False
    found_distance = False
    search_dist_endtrackpt = False

    # Distance variables
    last_distance = 0.0
    excess_distance = 0.0
    excess_time = 0.0
    splitres_meters = splitresKM * 1000
    dtobj_list = []

    # # TEST WRITE FLAGS
    # foundDistance = False
    # track = False
    # lapcount = 1

    # PROGRESS BAR VARIABLES
    # tracks if the same percent integer value has been calculated
    lastpercent = 0
    linetracker = 0   # tracks the number of lines within the file

    global que

    for line in file_obj:
        # Perform enclosed operations only if progress bar is present
        if len(args):
            linetracker += 1
            percent = (linetracker / max_lines) * 100

            # Update queue only if the integer percent value has changed
            if lastpercent != int(percent):
                lastpercent = int(percent)
                que.put((lastpercent, percent))

        # Check if a Lap tag has been found.
        if found_lap is False:
            if line.find('<Lap StartTime') >= 0:
                found_lap = True
            else:
                print(line.strip(), end="", file=outfile_obj)
        else:
            if found_track is False:
                if line.find('<Track>') >= 0:
                    found_track = True
                else:
                    continue
            else:
                # check if track end tag has been found
                if line.find('</Track>') >= 0:
                    if found_lap_time is True:
                        # Simulate a lap so that lap header will be written
                        # to the output file
                        found_distance = True
                        found_something = True
                        search_dist_endtrackpt = True
                    else:
                        LapString += '</Activity>'
                        LapString += '</Activities>'
                        LapString += '</TrainingCenterDatabase>'
                        break

                if found_something is False:
                    if line.find('<Time>') >= 0:
                        found_time = True
                        found_something = True
                    elif line.find('<Value>') >= 0:
                        found_heartrate = True
                        found_something = True
                    elif line.find('<DistanceMeters>') >= 0:
                        found_distance = True
                        found_something = True
                    else:
                        pass
                else:
                    if found_time:
                        found_time = False
                        if found_lap_time is False:
                            laptimelist = line.strip().split('.')
                            # Print Lap tag to file
                            print('<Lap StartTime="{}+00:00">'.format(
                                laptimelist[0]), end="", file=outfile_obj)

                            # Get lap start time and save as a datetime obj
                            dt_obj = line.strip().split('+')
                            if dt_obj[0].find('.') < 0:
                                dt_obj[0] += '.000000'
                                line = '+'.join(dt_obj)
                            starttime_dtobj = datetime.strptime(
                                dt_obj[0], '%Y-%m-%dT%H:%M:%S.%f')

                            found_lap_time = True
                        else:
                            # For any other occurences of the Time tag, just
                            # save its datetime obj equivalent
                            dt_obj = line.strip().split('+')
                            if dt_obj[0].find('.') < 0:
                                dt_obj[0] += '.000000'
                                line = '+'.join(dt_obj)
                        currenttime_dtobj = datetime.strptime(
                            dt_obj[0], '%Y-%m-%dT%H:%M:%S.%f')
                    #   line = currenttime_dtobj.isoformat(
                    #       timespec='seconds') + 'Z'
                    elif found_heartrate:
                        found_heartrate = False
                        LapHRList.append(int(line.strip()))

                    elif found_distance:
                        if search_dist_endtrackpt is False:
                            current_distance = float(line.strip())

                            distance_offset = (
                                current_distance - last_distance)
                            LapDistanceMeters += distance_offset
                            # LapDistanceMeters += (
                            #     current_distance - last_distance)
                            last_distance = current_distance

                            if current_distance == 0.0:
                                # try:
                                #     dtobj_list = [currenttime_dtobj]
                                # except Exception as e:
                                #     print(e)
                                #     #print('line = {}'.format(linetracker))

                                #     #print(currenttime_dtobj)
                                #     print('foundlap = {}  foundtrack = {} foundtime = {} foundlaptime = {}'.format(
                                #         found_lap, found_track, found_time, found_lap_time))
                                # else:
                                #     pass
                                dtobj_list = [currenttime_dtobj]
                            else:
                                dtobj_list.append(currenttime_dtobj)

                            if LapDistanceMeters >= splitres_meters:
                                search_dist_endtrackpt = True

                                delta_distance = (
                                    LapDistanceMeters - splitres_meters)
                                excess_distance += delta_distance
                                # excess_distance += (
                                #     LapDistanceMeters - splitres_meters)
                                LapDistanceMeters = splitres_meters

                                tdelta = currenttime_dtobj - dtobj_list[len(
                                    dtobj_list) - 2]
                                tdelta_secs = tdelta.total_seconds()
                                delta_pace = tdelta_secs / distance_offset

                                delta_time = delta_pace * delta_distance
                                excess_time += delta_time

                            else:
                                found_distance = False
                        else:
                            if (line.find('</Trackpoint>') >= 0) or (
                               line.find('</Track>') >= 0):
                                # Calculate Lap start time and current time
                                # delta and convert to seconds
                                timedelta = currenttime_dtobj - starttime_dtobj
                                if line.find('</Track>') >= 0:
                                    LapTotalTimeSeconds = (
                                        timedelta.total_seconds() + (
                                            excess_time))
                                else:
                                    LapTotalTimeSeconds = (
                                        timedelta.total_seconds() - (
                                            delta_time))
                                # Get max HR for the lap
                                LapMaximumHR = float(max(LapHRList))
                                # Compute average HR for the lap
                                LapAverageHR = float(sum(LapHRList)) / max(
                                    len(LapHRList), 1)

                                # APPEND LAP SUMMARY DATA TO FILE

                                # Append lap total time
                                print('<TotalTimeSeconds>', end='',
                                      file=outfile_obj)
                                print('{:.1f}'.format(
                                    LapTotalTimeSeconds), end='',
                                    file=outfile_obj)
                                print('</TotalTimeSeconds>', end='',
                                      file=outfile_obj)

                                # Compensate for excess distance by adding it
                                # to the final lap.
                                if line.find('</Track>') >= 0:
                                    LapDistanceMeters += excess_distance

                                # Append lap distance
                                print('<DistanceMeters>', end='',
                                      file=outfile_obj)
                                print('{:.1f}'.format(LapDistanceMeters),
                                      end='', file=outfile_obj)
                                print('</DistanceMeters>', end='',
                                      file=outfile_obj)

                                # Append dummy calorie data (value = 0)
                                print('<Calories>', end='',
                                      file=outfile_obj)
                                print('0', end='', file=outfile_obj)
                                print('</Calories>', end='',
                                      file=outfile_obj)

                                # Write track tag to file
                                print('<Track>', end='', file=outfile_obj)

                                time_only_idx = LapString.find(
                                    '</Time></Trackpoint>')
                                left_strlen = len(
                                    '<Trackpoint><Time>2017-03-05T22:49:43.545000+00:00')
                                right_strlen = len('</Time></Trackpoint>')

                                while time_only_idx >= 0:
#                                    print('time index = {}   Left = {}   Right = {}'.format(time_only_idx, LapString[time_only_idx-left_strlen-1], LapString[time_only_idx + right_strlen]))
                                    LapString = LapString[:(time_only_idx - left_strlen)] + LapString[(
                                        time_only_idx + right_strlen):]
                                    time_only_idx = LapString.find('</Time></Trackpoint>')

                                print(LapString, end='', file=outfile_obj)
                                #print(LapString, end='\n**************************\n')
                                print(line.strip(), end='', file=outfile_obj)

                                if line.find('</Track>') < 0:
                                    print('</Track>', end='', file=outfile_obj)

                                # Append lap average HR tag
                                # print('\t\t\t\t\t<AverageHeartRateBpm xsi'
                                #       ':type="HeartRateInBeatsPerMinute_t">',
                                #       file=outfile_obj)
                                print('<AverageHeartRateBpm>', end='',
                                      file=outfile_obj)

                                print('<Value>', end='', file=outfile_obj)
                                print('{}'.format(int(LapAverageHR)), end='',
                                      file=outfile_obj)
                                print('</Value>', end='', file=outfile_obj)
                                print('</AverageHeartRateBpm>', end='',
                                      file=outfile_obj)

                                # Append lap maximum HR tag
                                # print('\t\t\t\t\t<MaximumHeartRateBpm xsi'
                                #       ':type="HeartRateInBeatsPerMinute_t">',
                                #       file=outfile_obj)
                                print('<MaximumHeartRateBpm>', end='',
                                      file=outfile_obj)
                                print('<Value>', end='', file=outfile_obj)
                                print('{}'.format(int(LapMaximumHR)), end='',
                                      file=outfile_obj)
                                print('</Value>', end='', file=outfile_obj)
                                print('</MaximumHeartRateBpm>', end='',
                                      file=outfile_obj)

                                # Append lap end tags
                                if line.find('</Track>') < 0:
                                    print('</Lap>', end='', file=outfile_obj)

                                # Reset lap flags and variables
                                LapString = ""
                                LapDistanceMeters = 0.0
                                LapHRList = []
                                dtobj_list = []

                                found_lap_time = False
                                found_something = False
                                found_time = False
                                found_heartrate = False
                                found_distance = False
                                search_dist_endtrackpt = False
                                continue
                    else:
                        pass

                    if search_dist_endtrackpt is False:
                        found_something = False

                LapString += line.strip()
    if len(LapString) > 0:
        print(LapString.strip(), end="", file=outfile_obj)
        # print('Exit Loop Lap String: \n\t', end='')
        # print(LapString)

#         # TEST FILE WRITE CODE
#         if(foundDistance):
#             line = line.strip()
#
#             if(float(line) >= float(lapcount) * (splitresKM * 1000)):
#                 lapcount += 1
#                 # **Prints to file
# #                print('Lap {} -->'.format(
#                       lapcount), end=" ", file=outfile_obj)
#
#             if len(args):
#                 # **Prints to file
# #               print(line.strip(), end=" ", file=outfile_obj)
# #               print("progress = {}% actual progress = {:.1f}%".format(
# #                   args[0].get(), percent), file=outfile_obj)
#                 pass
#             else:
#                 print(line.strip())
#             foundDistance = False
#
#         if(line.find('<Track>') >= 0):
#             track = True
#
#         if(line.find('<DistanceMeters>') >= 0 and track):
#             foundDistance = True

    que.put((int(percent), percent))
#    print("loop done... line count={} queue={} percent ={}%".format(
#        linetracker, que, percent))

    file_obj.close()
    outfile_obj.close()


def EntryAfterIdleCallback():
        global entry
        entry.xview_moveto(1)


def SelectFile():
        # Setup options to use for the file dialog box
        options = {'filetypes': (('TCX files', '.tcx'), ('all files', '.*')),
                   'title': 'Select TCX file to process'}
        # Open file dialog box
        filename = filedialog.askopenfilename(**options)

        if filename != '':
            # Update Entry widget with opened filename.
            global entry
            entry.config(state='normal')
            entry.delete(0, END)
            entry.insert(0, filename)
            # Adjust view so that Entry text is displayed right-justified.
            # Note: Have to use after_idle callback since xview_moveto does
            #       not work if called directly.
            entry.after_idle(EntryAfterIdleCallback)
            entry.config(state='readonly')

            global progressbar
            global lap_res
            global pbar_label
            mmrSplit = TcxSplitSingleLap(file=filename,
                                         split_res_KM=lap_res.get(),
                                         progbar=progressbar,
                                         pbarlabel=pbar_label)
            # mmrSplit = TcxSplitSingleLap(file=filename,
            #                              split_res_KM=lap_res.get())

            # linecount = mmrSplit.getlinecount()
            # print(linecount)
            mmrSplit.parseline()


def UpdateLapRes(horiz_var):
    rndval = round(float(horiz_var), 1)
    global lap_res
    lap_res.set(rndval)
    global kmLabel
    kmLabel.config(text='{:2.1f} KM'.format(rndval))


def main():
    global root
    root = Tk()
    root.title("MapMyRun TCX file Lap Splitter")

    # Create frames for the filename widgets and lap resolution widgets
    frameFile = ttk.Frame(root)
    frameLapRes = ttk.Frame(root)
    frameProgressBar = ttk.Frame(root)
    frameFile.pack()
    frameLapRes.pack()
    frameProgressBar.pack(expand=True, fill='x')

    global entry
    entry = ttk.Entry(frameFile, width=30, state='readonly')
    entry.grid(row=0, column=1, padx=(0, 10), pady=10)

    button = ttk.Button(frameFile, text="Select File...")
    button.grid(row=0, column=2, padx=(0, 10))

    ttk.Label(frameFile, text="TCX file: ").grid(row=0, column=0, padx=(10, 0))

    logo = PhotoImage(file='tcx_icon.gif')
    small_icon = logo.subsample(12, 12)
    button.config(image=small_icon, compound=LEFT, command=SelectFile)

    # Use spinbox for selecting the lap resolution
    # global lap_res
    # lap_res = StringVar(value='1.0')
    # ttk.Label(frameLapRes, text="Split every: ").grid(row=1, column=1, pady=(
    #     5, 10), sticky='e')
    # spinbox_km = Spinbox(frameLapRes, from_=0.1, to=5.0, increment=0.1,
    #                      format='%.1f', textvariable=lap_res, width=4,
    #                      state='readonly')
    # spinbox_km.grid(row=1, column=2, pady=(5, 10), sticky='w')

    ###############################################
    # Use scale widget to select lap resolution
    ###############################################
    ttk.Label(frameLapRes, text='Split every: ', justify=LEFT).pack(
        side=LEFT, pady=(0, 5))

    global lap_res
    lap_res = DoubleVar(value=1.0)

    global scale
    scale = ttk.Scale(frameLapRes, orient=HORIZONTAL, length=250,
                      variable=lap_res, from_=0.1, to=5.0,
                      command=UpdateLapRes)
    scale.pack(side=LEFT, anchor=CENTER, fill='x', pady=(0, 5))

    global kmLabel
    kmLabel = ttk.Label(frameLapRes, text='{} KM'.format(lap_res.get()))
    kmLabel.pack(side=LEFT, padx=5, pady=(0, 5))

    global progressbar
    progressbar = ttk.Progressbar(frameProgressBar, orient=HORIZONTAL,
                                  mode='determinate', maximum=100, length=320)
#    progressbar.pack(side=LEFT, padx=10, pady=(0, 10), expand=True, fill='x')
    progressbar.grid(column=0, row=0, sticky='w', padx=(10, 5), pady=(0, 10))

    global pbar_label
    pbar_label = ttk.Label(frameProgressBar, text="0%")
    pbar_label.grid(column=1, row=0, padx=(0, 5), pady=(0, 10), sticky='e')

    global que
    que = queue.Queue()
#   print("created queue... queue={}".format(que))
    root.mainloop()

#    f = open('lines.txt')
#    for line in f:
#        print(line, end = '')


if __name__ == "__main__":
    main()
