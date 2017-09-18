import os
import re
import subprocess
import numpy

datafile_re = re.compile('\.dat', re.IGNORECASE)

lights_include_opt = "-il/app/lights.pov"

radius = -50
lats = [-70,-50,-30,30,50,70]
#lats = numpy.arange(-70, 70, 20)
lons = numpy.arange(0, 350, 20)

# debug stuff
#lats = [45]
#lons = [90]


# 0-15, 32-47, 256-511
colors = numpy.append(numpy.arange(0,16,1),numpy.arange(32,48,1))
colors = numpy.append(colors,numpy.arange(256,512,1))

os.chdir('/data')
subprocess.call(['rm', '-rf', '/data/*'])
subprocess.call(['mkdir', 'img'])
os.chdir('/data/img')

for fname in os.listdir('/opt/ldraw/parts'):
    f_base, ext = os.path.splitext(fname)
    if datafile_re.search(ext):
        # this is a data file
        os.chdir('/data/img')
        subprocess.call(['mkdir', f_base])
        for color in colors:
            os.chdir("/data/img/{}".format(f_base))
            subprocess.call(['mkdir', "{}".format(color)])
            os.chdir("/data/img/{}/{}".format(f_base, color))
            for lat in lats:
                for lon in lons:
                    if lon == 180:
                        lon = 181 # silly bug?
                    pov_fname = "{}_{}_{}.pov".format(f_base, lat, lon)
                    out_fname = "{}_{}_{}.png".format(f_base, lat, lon)
                    out_fname_opt = "+O{}".format(out_fname)
                    color_opt = "-c{}".format(color)
                    cg_opt = "-cg{},{},{}".format(lat, lon, radius)
                    subprocess.call(['l3p', '-bWhite', '-q4', color_opt, lights_include_opt, cg_opt, '-o', fname, pov_fname])
                    subprocess.call(['povray', '+H480', '+W640', '+A', '+Q9', pov_fname, out_fname_opt])
                    subprocess.call(['rm', pov_fname])
            








# l3p -bWhite -q4 -c4 -cg10,45,-50 -o 27c.dat pov/ && cd pov && povray +H480 +W640 +A +Q9 *.pov

        # l3p -bWhite -q4 -c4 -cg50,45,-50 -o 3755.dat && povray +H480 +W640 +A +Q9 3755.pov