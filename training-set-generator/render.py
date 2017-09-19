import os
import sys
import re
import subprocess
import numpy
import sqlite3
from pathlib import Path
import shutil


conn = sqlite3.connect('/app/inventory.db')
c = conn.cursor()

background_opt = "-b.9,.9,.9" # white background
lights_include_opt = "-il/app/lights.pov"
height_opt = '+H480'
width_opt = '+W640'


datafile_re = re.compile('\.dat', re.IGNORECASE)



radius = -50
lats = [-70,-50,-30,30,50,70]
#lats = numpy.arange(-70, 70, 20)
lons = numpy.arange(-180, 170, 45)

# debug stuff
#lats = [45]
#lons = [90]


# get color lookups - we will use the hex values allowed by l3p
color_lookup = {} # key: integer, value: hex color
for row in c.execute("select id, name, rgb, is_trans from colors"):
    prefix = "0x02"
    is_trans = False
    if row[3] == 't':
        # transparent
        prefix = "0x03"
        is_trans = True
    hex_color = row[2]
    color_id = row[0]
    color_lookup[color_id] = {'hex': "{}{}".format(prefix, hex_color), 'name': row[1], 'transparent': is_trans}


os.chdir('/data')
if Path('img').exists():
    shutil.rmtree('/data/img')
os.mkdir('img')
os.chdir('/data/img')

# go through inventory and only generate images that are valid part/color combinations
c.execute("select part_num from parts")
part_rows = c.fetchall()
for part_row in part_rows:
    os.chdir('/data/img')
    part = part_row[0]
    # check if the part is in the ldraw library
    part_file = Path("/opt/ldraw/parts", part).with_suffix('.dat')
    if not part_file.is_file():
        #something is wrong. resolve re-named parts somehow?
        print("OOPS - part {} could not be found!".format(part))
        continue
    
    os.mkdir(part)
    for color_row in c.execute("select distinct(color_id) from inventory_parts where part_num=:part", {"part": part}):
        color = color_row[0]
        # get hex value of color:
        color_hex = color_lookup[color]['hex']
        color_name = color_lookup[color]['name']
        trans = color_lookup[color]['transparent']
        color_name.replace(" ", "_")
        os.chdir("/data/img/{}".format(part))
        os.mkdir(color_name)
        os.chdir("/data/img/{}/{}".format(part, color_name))
        print("rendering -- part: {} -> color: {} ({})".format(part, color_name, "Transparent" if trans else "Opaque"))
        sys.stdout.flush()
        fname = "{}.dat".format(part)
        for lat in lats:
            for lon in lons:
                if lon == -180:
                    lon = -179  # silly bug? sometimes camera is not pointed at part
                pov_fname = "{}_{}_{}.pov".format(part, lat, lon)
                out_fname = "{}_{}_{}.png".format(part, lat, lon)
                out_fname_opt = "+O{}".format(out_fname)
                color_opt = "-c{}".format(color_hex)
                cg_opt = "-cg{},{},{}".format(lat, lon, radius)
                subprocess.call(
                    ['l3p', background_opt, '-q4', color_opt, lights_include_opt, cg_opt, '-bu', '-o', fname, pov_fname], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.call(['povray', height_opt, width_opt, '+A', '+Q9', '-GA', pov_fname, out_fname_opt], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                try:
                    os.remove(pov_fname)
                except:
                    print("couldn't remove {}".format(pov_fname))


            








# l3p -bWhite -q4 -c4 -cg10,45,-50 -o 27c.dat pov/ && cd pov && povray +H480 +W640 +A +Q9 *.pov

        # l3p -bWhite -q4 -c4 -cg50,45,-50 -o 11598.dat && povray +H480 +W640 +A +Q9 -GA 11598.pov