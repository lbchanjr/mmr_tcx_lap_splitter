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

    def getlinecount(self):
        _f = open(self._filename, 'rb')
        _fgen = self._make_gen(_f.raw.read)
        count = sum(_buf.count(b'\n') for _buf in _fgen)
        _f.close()
        return count

    def parseline(self):
        if self._progress is None:
            _f = open(self._filename)
            ParseLineInFile(_f, self._splitresKM)
            _f.close()
        else:
            self.maxval = float(self.getlinecount())
            self.linecnt = DoubleVar()
            self.linecnt.set(0)
            self._progress.config(maximum=self.maxval, variable=self.linecnt)

            self.secondary_thread = threading.Thread(
                target=self._callparseline)
            self.secondary_thread.start()
            # check the Queue in 50ms
            global root
            root.after(1, self._check_que)

    def _check_que(self):
        while True:
            global que
            try:
                x = que.get_nowait()
            except queue.Empty:
                global root
                root.after(1, self._check_que)
                break
            else:  # continue from the try suite
#                    self.label['text'] = '{}/4'.format(x)
                self.linecnt.set(x)
                # if x == 4:
                #     self.b_start['state'] = 'normal'
                #     break

    def _make_gen(self, reader):
        _b = reader(1024 * 1024)
        while _b:
            yield _b
            _b = reader(1024 * 1024)

    def _callparseline(self):
        _f = open(self._filename)
        ParseLineInFile(_f, self._splitresKM, self.linecnt, self.maxval)
        # ParseLineInFile(_f, self._splitresKM)
        _f.close()


def ParseLineInFile(file, splitresKM, *args):
    foundDistance = False
    track = False
    lapcount = 1
    linetracker = 0.0

    print('Lap {} -->'.format(lapcount), end=" ")
    for line in file:
        if len(args):
            linetracker += 1
            percent = (linetracker / args[1]) * 100
            args[0].set(linetracker)
            # global progressbar
            # progressbar.update_idletasks()

        if(foundDistance):
            line = line.strip()

            if(float(line) >= float(lapcount) * (splitresKM * 1000)):
                lapcount += 1
                print('Lap {} -->'.format(lapcount), end=" ")

            if len(args):
                print(line.strip(), end=" {} {:.1f}%\n".format(
                    args[0].get(), percent))

                global que
                que.put(linetracker)
            else:
                print(line.strip())
            foundDistance = False

        if(line.find('<Track>') >= 0):
            track = True

        if(line.find('<DistanceMeters>') >= 0 and track):
            foundDistance = True

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

            # mmrSplit = TcxSplitSingleLap(file=filename,
            #                              split_res_KM=lap_res.get(),
            #                              progbar=progressbar)
            mmrSplit = TcxSplitSingleLap(file=filename,
                                         split_res_KM=lap_res.get())

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
                                  mode='determinate')
    #progressbar = ttk.Progressbar(mode='indeterminate')
    progressbar.pack(padx=10, pady=(0, 10), expand=True, fill='x')

    global que
    que = queue.Queue()

    root.mainloop()

#    f = open('lines.txt')
#    for line in f:
#        print(line, end = '')


if __name__ == "__main__":
    main()
